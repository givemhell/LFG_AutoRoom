import hashlib
import json
from typing import Union
from discord.ext import commands
from discord import Guild, Intents, Member, Role, Option
from discord import PermissionOverwrite
import discord
import os
import asyncio
import bcrypt
import logging



intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s', 
                    filename='bot.log', 
                    filemode='a')

ALLOWED_ROLE_IDS = {578664576674168834, 578664579584753685}
MOVE_DELAY = 0.5  # Time in seconds

# Load bot token
with open('bot_token.txt', 'r') as file:
    TOKEN = file.read().strip()

try:
    with open('rooms.json', 'r') as file:
        rooms = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    rooms = {}
logging.info(f"Loaded rooms: {rooms}")


# Load blacklist_data
if os.path.exists('blacklist_data.json'):
    with open('blacklist_data.json', 'r') as file:
        blacklist_data = json.load(file)
else:
    blacklist_data = {}

def get_display_name(member):
    return member.nick if member.nick else member.name

def load_data():
    global room_settings
    if os.path.exists('room_settings.json'):
        with open('room_settings.json', 'r') as f:
            # Convert lists back to sets after loading
            loaded_room_settings = json.load(f)
            room_settings = {int(user_id): {key: set(value) if isinstance(value, list) else value for key, value in settings.items()} for user_id, settings in loaded_room_settings.items()}

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:  # Ignore all bots  # Ignore bot's own voice state updates
        return

    # When a user leaves a channel
    if before.channel is not None and after.channel is None:
        if before.channel.id in rooms and rooms[before.channel.id] == member.id:  # If the user leaving is the owner
            remaining_members = before.channel.members
            if remaining_members:  # If there are still members in the room
                # Sort the members by top role's position (which is a measure of rank)
                remaining_members.sort(key=lambda m: m.top_role.position, reverse=True)
                new_owner = remaining_members[0]  # The highest ranked member is the new owner
                rooms[before.channel.id] = new_owner.id  # Update the owner in the rooms dictionary
                # Update the channel name here with the new owner's name
                await before.channel.edit(name=f'👽┃{new_owner.nick if new_owner.nick else new_owner.name}\'s room')
                # send a message to the voice chat the new owner
                await before.channel.send(f'{new_owner.mention} you are now the owner of this room')
            else:  # If no members left in the room
                try:
                    await before.channel.delete()
                except Exception as e:
                    logging.error(f"Error deleting channel {before.channel.id}: {e}")

    # Do something when a user joins a '🛸' channel
    elif after.channel and '🛸' in after.channel.name:
        # print the name of the user who joined the channel
        print(f'{member.name} is creating a room')
        overwrites = {**after.channel.overwrites}  # Copy the permission overwrites from the 🛸 channel
        if member.id in room_settings:
            settings = room_settings[member.id]
            # Apply the whitelist
            if settings["whitelist_enabled"]:
                for user_id in settings["whitelist"]:
                    user = member.guild.get_member(user_id)
                    if user:
                        overwrites[user] = discord.PermissionOverwrite(connect=True)
            # Apply the blacklist
            if settings["blacklist_enabled"]:
                for user_id in settings["blacklist"]:
                    user = member.guild.get_member(user_id)
                    if user:
                        overwrites[user] = discord.PermissionOverwrite(connect=False)

        base_name = f'👽┃{get_display_name(member)}\'s room'
        channel_name = base_name
        counter = 1

        # Check if a channel with the desired name exists
        while any(channel.name == channel_name for channel in after.channel.category.channels):
            channel_name = f"{base_name} ({counter})"
            counter += 1

        new_channel = await after.channel.category.create_voice_channel(
            name=channel_name,
            user_limit=after.channel.user_limit,
            overwrites=overwrites
        )

        await member.move_to(new_channel)
        rooms[new_channel.id] = member.id


        # Create the main embed message
        embed = discord.Embed(
            title='Welcome to your custom room!',
            description='You can customize your room by clicking emojis:'
        )

        # Add Description Control Panel field
        embed.add_field(name='Givemhells LFG Tool',
                        value='Choose One of two\n'
                              '🌴 - Chill-out rooms (NO Religion or Politics)\n'
                              '🔞 - 18+ NSFW rooms (NO RULES)\n\n', inline=False)

        embed.add_field(name='Special Room Presets',
                        value='you can skip these if not apply\n'
                              '⏱ - Mythic+ rooms (Set 5 user limit)\n'
                              '🎉 - Celebratory rooms (for celebrations)\n'
                              '🎙️ - Broadcasting rooms (for twitch broadcasting)\n'
                              '🃏 - Card Room (for card/board games)\n'
                              '📺 - Movie/Show Room (all members muted)\n\n', inline=False)

        embed.add_field(name='Lock Room Presets',
                        value='you can skip these if none apply\n'
                              '🔒 - Lock Everyone Out\n'
                              '🎮 - Lock Room By Game\n'
                              '📋 - Enable/Disable whitelist\n\n', inline=False)

        embed.add_field(name='Audio Quality',
                        value='set the audio quality\n'
                              '🔈 - 128 kbps audio quality\n'
                              '🔉 - 256 kbps audio quality\n'
                              '🔊 - 386 kbps audio quality\n\n', inline=False)

        embed.add_field(name='Feature Control Panel',
                        value='set features for your room\n'
                              '💻 - Enable Screen sharing & Camera\n'
                              '💾 - Save & Apply Room Settings\n\n', inline=False)

        message = await new_channel.send(embed=embed)
        emojis = ['🌴', '🔞', '⏱', '🎉', '🎙️', '🃏', '📺', '🔒', '🎮', '📋', '🔈', '🔉', '🔊', '💻', '💾']

        async def add_single_reaction(message, emoji):
            try:
                await message.add_reaction(emoji)
            except discord.errors.NotFound:
                logging.warning(f"Channel {message.channel.id} not found when trying to add reaction {emoji}.")

        await asyncio.gather(*(add_single_reaction(message, emoji) for emoji in emojis))



    try:
        with open('rooms.json', 'w') as file:
            json.dump(rooms, file)
    except Exception as e:
        logging.error(f"Error writing to rooms.json: {e}")


#--------------------------------------#
#           On Reaction Add            #
#--------------------------------------#
@bot.event
async def on_reaction_add(reaction, user):
    # Ignore reactions made by the bot
    if user == bot.user:
        return

    channel = reaction.message.channel
    if not isinstance(channel, discord.VoiceChannel):
        return

    if rooms.get(channel.id) != user.id:
        print('User is not the owner of the room')
        await channel.send(f'{user.mention} you are not the owner of the room')
        for react in reaction.message.reactions:
            if react.emoji == reaction.emoji:
                await react.remove(user)
        return

    print(reaction.emoji)

    reaction_handlers = {
        '🌴': handle_palm_tree,
        '🔞': handle_adult_content,
        '⏱': handle_timer,
        '🎉': handle_party,
        '🎙️': handle_microphone,
        '🃏': handle_card_game,
        '📺': handle_tv,
        '🎮': handle_video_game,
        '🔒': handle_lock,
        '💾': handle_save,
        '💻': handle_computer,
        '🔈': handle_volume_down,
        '🔉': handle_volume_medium,
        '🔊': handle_volume_up,
    }

    if reaction.emoji in reaction_handlers:
        await reaction_handlers[reaction.emoji](reaction, user)

#--------------------------------------#
#           On reaction remove         #
#--------------------------------------#
async def on_reaction_remove(reaction, user):
    channel = reaction.message.channel
    if not isinstance(channel, discord.VoiceChannel):
        return

    reaction_handlers = {
        '🔒': remove_handle_lock,
        '🌴': remove_handle_palm_tree,
        '🔞': remove_handle_adult_content,
        '⏱': remove_handle_timer,
        '🎉': remove_handle_party,
        '🎙️': remove_handle_microphone,
        '🃏': remove_handle_card_game,
        '📺': remove_handle_tv,
        '🔈': remove_handle_volume_down,
        '🔉': remove_handle_volume_medium,
        '🔊': remove_handle_volume_up,
        '💻': remove_handle_computer,
        '💾': remove_handle_save,
        '📋': remove_handle_clipboard,
        '🎮': remove_handle_video_game,
    }

    if reaction.emoji in reaction_handlers:
        await reaction_handlers[reaction.emoji](reaction, user)

#--------------------------------------#
#         reaction add functions       #
#--------------------------------------#
# A dictionary to store the pending changes for each channel


pending_changes = {}

async def handle_palm_tree(reaction, user):
    channel = reaction.message.channel
    # Add function to 🌴 reaction

    # Check if the 🔞 reaction is already present
    for react in reaction.message.reactions:
        if react.emoji == '🔞' and user in await react.users().flatten():
            # Remove the 🔞 reaction
            await reaction.message.remove_reaction('🔞', user)

async def handle_adult_content(reaction, user):
    channel = reaction.message.channel
    # Add function to 🔞 reaction

    # Check if the 🌴 reaction is already present
    for react in reaction.message.reactions:
        if react.emoji == '🌴' and user in await react.users().flatten():
            # Remove the 🌴 reaction
            await reaction.message.remove_reaction('🌴', user)

# ⏱ Add Reaction Function
async def handle_timer(reaction, user):
    channel = reaction.message.channel
    # Add function to ⏱ reaction
    if channel.id not in pending_changes:
        pending_changes[channel.id] = {}
    pending_changes[channel.id]['user_limit'] = 5

# 🎉 Add Reaction Function
async def handle_party(reaction, user):
    channel = reaction.message.channel
    # Add function to 🎉 reaction
    pass

# 🎙️ Add Reaction Function
async def handle_microphone(reaction, user):
    channel = reaction.message.channel
    # Add function to 🎙️ reaction
    pass

# 🃏 Add Reaction Function
async def handle_card_game(reaction, user):
    channel = reaction.message.channel
    # Add function to 🃏 reaction
    embed = discord.Embed(
        title="Game Resources",
        description="Here are some links to online games you can play:",
        color=discord.Color.blue()
    )
    embed.add_field(name="Cards Against Humanity", value="https://picturecards.online/static/index.html\nor use /cah packs then /cah create\n", inline=False)
    embed.add_field(name="Random Common Card & Board Games", value="https://playingcards.io/games/\n", inline=False)
    embed.add_field(name="Random Multiplayer Games", value="https://boardgamearena.com/lobby\n", inline=False)
    embed.add_field(name="Games available:", value="Uno (called solo)\nYahtzee\nand much more", inline=False)
    if channel.id not in pending_changes:
        pending_changes[channel.id] = {}
    pending_changes[channel.id]['embed'] = embed

# 📺 Add Reaction Function
async def handle_tv(reaction, user):
    channel = reaction.message.channel
    # Add function to 📺 reaction
    general_access_role = discord.utils.get(channel.guild.roles, id=1070344422799200306)
    # Get the current permissions of the role in the channel
    permissions = channel.overwrites_for(general_access_role)
    # Modify the 'speak' permission
    permissions.update(speak=False)
    # Apply the modified permissions
    if channel.id not in pending_changes:
        pending_changes[channel.id] = {}
    pending_changes[channel.id]['permissions'] = permissions
    pending_changes[channel.id]['general_access_role'] = general_access_role

# 🎮 Add Reaction Function
async def handle_video_game(reaction, user):
    channel = reaction.message.channel
    # Add function to 🎮 reaction
    creator = channel.guild.get_member(channel.guild.owner_id)
    if creator is not None and creator.activities:
        creator_game = None
        for activity in creator.activities:
            if isinstance(activity, discord.Game):
                creator_game = activity.name
                break
        if creator_game is not None:
            overwrites = channel.overwrites
            for member in channel.guild.members:
                member_game = None
                for activity in member.activities:
                    if isinstance(activity, discord.Game):
                        member_game = activity.name
                        break
                if member_game == creator_game:
                    overwrites[member] = discord.PermissionOverwrite(connect=True)
                else:
                    overwrites[member] = discord.PermissionOverwrite(connect=False)
            if channel.id not in pending_changes:
                pending_changes[channel.id] = {}
            pending_changes[channel.id]['overwrites'] = overwrites
            pass

# 🔒 Add Reaction Function
async def handle_lock(reaction, user):
    channel = reaction.message.channel
    # Add function to 🔒 reaction
    everyone_role = discord.utils.get(channel.guild.roles, name='@everyone')
    general_access_role = discord.utils.get(channel.guild.roles, id=1070344422799200306)
    discord_mod_role = discord.utils.get(channel.guild.roles, id=578664579584753685)
    # Get the current permissions of the roles in the channel
    everyone_permissions = channel.overwrites_for(everyone_role)
    general_access_permissions = channel.overwrites_for(general_access_role)
    discord_mod_permissions = channel.overwrites_for(discord_mod_role)
    # Modify the specific permissions
    everyone_permissions.update(read_messages=False, view_channel=False, connect=False)
    general_access_permissions.update(read_messages=False, view_channel=True, connect=False)
    discord_mod_permissions.update(manage_messages=False, mute_members=False, deafen_members=False, move_members=False)
    # Set the permissions back
    if channel.id not in pending_changes:
        pending_changes[channel.id] = {}
    pending_changes[channel.id]['everyone_permissions'] = everyone_permissions
    pending_changes[channel.id]['general_access_permissions'] = general_access_permissions
    pending_changes[channel.id]['discord_mod_permissions'] = discord_mod_permissions
    pending_changes[channel.id]['everyone_role'] = everyone_role
    pending_changes[channel.id]['general_access_role'] = general_access_role
    pending_changes[channel.id]['discord_mod_role'] = discord_mod_role
    pending_changes[channel.id]['lock_message'] = f'{user.mention} you have locked the room'
    pass

# 💻 Add Reaction Function
async def handle_computer(reaction, user):
    channel = reaction.message.channel
    # Add function to 💻 reaction
    general_access_role = discord.utils.get(channel.guild.roles, id=1070344422799200306)
    # Get the current permissions of the role in the channel
    permissions = channel.overwrites_for(general_access_role)
    # Modify the specific permission
    permissions.update(stream=True)
    # Set the permissions back
    if channel.id not in pending_changes:
        pending_changes[channel.id] = {}
    pending_changes[channel.id]['permissions'] = permissions
    pending_changes[channel.id]['general_access_role'] = general_access_role
    pending_changes[channel.id]['computer_message'] = f'{user.mention} you have updated the room permissions'
    pass

# 📋 Add Reaction Function
async def handle_clipboard(reaction, user):
    channel = reaction.message.channel
    # Add function to 📋 reaction
    if user.id not in room_settings:
        room_settings[user.id] = {"whitelist": set(), "blacklist": set(), "whitelist_enabled": False, "blacklist_enabled": False}
    room_settings[user.id]["whitelist_enabled"] = not room_settings[user.id]["whitelist_enabled"]  # Toggle the whitelist status
    if channel.id not in pending_changes:
        pending_changes[channel.id] = {}
    pending_changes[channel.id]['whitelist_enabled'] = room_settings[user.id]["whitelist_enabled"]
    if room_settings[user.id]["whitelist_enabled"]:
        await channel.send(f'{user.mention} your whitelist will be enabled when you save.')
    else:
        await channel.send(f'{user.mention} your whitelist will be disabled when you save.')


# 🔊 Add Reaction Function
async def handle_volume_up(reaction, user):
    channel = reaction.message.channel
    # Add function to 🔊 reaction
    if discord.utils.get(user.roles, id=1129504850028269578) is None:  # check if the user does not have the role
        print("User is missing the supporter role")
        await channel.send(f'{user.mention} you are missing the supporter role')
        for react in reaction.message.reactions:
            if react.emoji == '🔊':  # Replace with your specific emoji
                await react.remove(user)  # Remove the reaction of the user 'user'
        return  # make sure to return after this point if the user does not have the role
    # Prepare functionality for '🔊' reaction
    bitrate = 384000
    if channel.id not in pending_changes:
        pending_changes[channel.id] = {}
    pending_changes[channel.id]['bitrate'] = bitrate
    pending_changes[channel.id]['bitrate_message'] = f'{user.mention} you have changed the audio quality to {bitrate/1000} kbps'


# 🔉 Add Reaction Function
async def handle_volume_medium(reaction, user):
    channel = reaction.message.channel
    # Add function to 🔉 reaction
    if discord.utils.get(user.roles, id=1077208333024497674) is None:  # check if the user does not have the role
        print("User is missing the supporter+ role")
        await channel.send(f'{user.mention} you are missing the supporter+ role')
        for react in reaction.message.reactions:
            if react.emoji == '🔉':
                await react.remove(user)
        return  # make sure to return after this point if the user does not have the role
    # Prepare functionality for '🔉' reaction
    bitrate = 256000
    if channel.id not in pending_changes:
        pending_changes[channel.id] = {}
    pending_changes[channel.id]['bitrate'] = bitrate
    pending_changes[channel.id]['bitrate_message'] = f'{user.mention} you have changed the audio quality to {bitrate/1000} kbps'

# 🔈 Add Reaction Function
async def handle_volume_down(reaction, user):
    channel = reaction.message.channel
    # Add function to 🔈 reaction
    if discord.utils.get(user.roles, id=1129504850028269578) is None:  # check if the user does not have the role
        print("User is missing the supporter role")
        await channel.send(f'{user.mention} you are missing the supporter role')
        for react in reaction.message.reactions:
            if react.emoji == '🔈':  # Replace with your specific emoji
                await react.remove(user)  # Remove the reaction of the user 'user'
        return  # make sure to return after this point if the user does not have the role
    # Prepare functionality for '🔈' reaction
    bitrate = 128000
    if channel.id not in pending_changes:
        pending_changes[channel.id] = {}
    pending_changes[channel.id]['bitrate'] = bitrate
    pending_changes[channel.id]['bitrate_message'] = f'{user.mention} you have changed the audio quality to {bitrate/1000} kbps'

# 💾 Add Reaction Function
async def handle_save(reaction, user):
    channel = reaction.message.channel
    # Add function to 💾 reaction
    owner = user
    message = reaction.message
    reactions = message.reactions
    emoji_order = ['🔒', '🎮', '📋', '🌴', '🔞', '⏱', '🎉', '🎙️', '🃏', '📺', '💻', '🔊', '🔉', '🔈']
    emoji_priority = {emoji: i for i, emoji in enumerate(emoji_order)}
    emoji_name_list = sorted([(react.emoji, emoji_priority.get(react.emoji, float('inf'))) for react in reactions if owner in await react.users().flatten() and react.emoji not in ['💾', '📋']], key=lambda x: x[1])
    # Only add '👽' if no other emojis were used
    if emoji_name_list:
        channel_name = channel.name.replace('👽', '').strip()
    else:
        channel_name = channel.name
    new_channel_name = ''.join(emoji for emoji, _ in emoji_name_list) + '' + channel_name


    # Set default user limit to 0 if not in changes
    if channel.id not in pending_changes or 'user_limit' not in pending_changes[channel.id]:
        await channel.edit(user_limit=0)

    # Apply the pending changes (if any)
    if channel.id in pending_changes:
        changes = pending_changes[channel.id]
        if 'user_limit' in changes:
            await channel.edit(user_limit=changes['user_limit'])
        if 'embed' in changes:
            await channel.send(embed=changes['embed'])
        if 'permissions' in changes and 'general_access_role' in changes:
            await channel.set_permissions(changes['general_access_role'], overwrite=changes['permissions'])
        if 'overwrites' in changes:
            await channel.edit(overwrites=changes['overwrites'])
        if 'everyone_permissions' in changes and 'everyone_role' in changes:
            await channel.set_permissions(changes['everyone_role'], overwrite=changes['everyone_permissions'])
        if 'general_access_permissions' in changes and 'general_access_role' in changes:
            await channel.set_permissions(changes['general_access_role'], overwrite=changes['general_access_permissions'])
        if 'discord_mod_permissions' in changes and 'discord_mod_role' in changes:
            await channel.set_permissions(changes['discord_mod_role'], overwrite=changes['discord_mod_permissions'])
        if 'computer_message' in changes:
            await channel.send(changes['computer_message'])
        if 'lock_message' in changes:
            await channel.send(changes['lock_message'])
        if 'general_access_role' in changes and 'permissions' in changes:
            await channel.set_permissions(changes['general_access_role'], overwrite=changes['permissions'])
        if 'bitrate' in changes:
            await channel.edit(bitrate=changes['bitrate'])
        if 'bitrate_message' in changes:
            await channel.send(changes['bitrate_message'])
        if 'whitelist_enabled' in changes:
            room_settings[channel.id]["whitelist_enabled"] = changes['whitelist_enabled']
            if room_settings[channel.id]["whitelist_enabled"]:
                # If whitelist is enabled, grant 'connect' permission to everyone on the whitelist
                overwrites = {user.guild.get_member(user_id): discord.PermissionOverwrite(connect=True) for user_id in room_settings[channel.id]["whitelist"]}
                await channel.edit(overwrites=overwrites)
                await channel.send(f'{user.mention} your whitelist is now enabled.')
            else:
                # If whitelist is disabled, reset 'connect' permission
                overwrites = {user.guild.get_member(user_id): discord.PermissionOverwrite(connect=None) for user_id in room_settings[channel.id]["whitelist"]}
                await channel.edit(overwrites=overwrites)
                await channel.send(f'{user.mention} your whitelist is now disabled.')
                
        # Clear the pending changes for this channel
        del pending_changes[channel.id]
        
    # Continue with the rest of the function
    await channel.edit(name=new_channel_name)
    await channel.send(f'{user.mention} you have updated the room with changes')
    # Clear the pending changes for this channel
    if channel.id in pending_changes:
        del pending_changes[channel.id]



#--------------------------------------#
#     Reaction Remove functions        #
#--------------------------------------#

# 🌴 Remove
async def remove_handle_palm_tree(reaction, user):
    channel = reaction.message.channel
    # Add function to 🌴 remove reaction

# 🔞 Remove
async def remove_handle_adult_content(reaction, user):
    channel = reaction.message.channel
    # Add function to 🔞 remove reaction

# ⏱ Remove
async def remove_handle_timer(reaction, user):
    channel = reaction.message.channel
    # Add function to ⏱ remove reaction

# 🎉 Remove
async def remove_handle_party(reaction, user):
    channel = reaction.message.channel
    # Add function to 🎉 remove reaction

# 🎙️ Remove
async def remove_handle_microphone(reaction, user):
    channel = reaction.message.channel
    # Add function to 🎙️ remove reaction

# 🃏 Remove
async def remove_handle_card_game(reaction, user):
    channel = reaction.message.channel
    # Add function to 🃏 remove reaction

# 📺 Remove
async def remove_handle_tv(reaction, user):
    channel = reaction.message.channel
    # Add function to 📺 remove reaction

# 🎮 Remove
async def remove_handle_video_game(reaction, user):
    channel = reaction.message.channel
    # Add function to 🎮 remove reaction

# 🔒 Remove
async def remove_handle_lock(reaction, user):
    channel = reaction.message.channel
    # Add function to 🔒 remove reaction

# 💾 Remove
async def remove_handle_save(reaction, user):
    channel = reaction.message.channel
    # Add function to 💾 remove reaction

# 💻 Remove
async def remove_handle_computer(reaction, user):
    channel = reaction.message.channel
    # Add function to 💻 remove reaction

# 🔈 Remove
async def remove_handle_volume_down(reaction, user):
    channel = reaction.message.channel
    # Add function to 🔈 remove reaction

# 🔉 Remove
async def remove_handle_volume_medium(reaction, user):
    channel = reaction.message.channel
    # Add function to 🔉 remove reaction

# 🔊 Remove
async def remove_handle_volume_up(reaction, user):
    channel = reaction.message.channel
    # Add function to 🔊 remove reaction

# 📋 Remove
async def remove_handle_clipboard(reaction, user):
    channel = reaction.message.channel
    # Add function to 📋 remove reaction

#--------------------------------------#
#            Slash Commands            #
#--------------------------------------#
room_settings = {}

def save_data():
    with open('room_settings.json', 'w') as f:
        # Convert sets to lists before saving
        save_room_settings = {user_id: {key: list(value) if isinstance(value, set) else value for key, value in settings.items()} for user_id, settings in room_settings.items()}
        json.dump(save_room_settings, f)

#--------------------------------------#
#           Whitelist Commands         #
#--------------------------------------#

@bot.slash_command(name="whitelist_add", description="Add a user or role to your whitelist")
async def whitelist_add(ctx, user: discord.Member):
    if ctx.author.id not in room_settings:
        room_settings[ctx.author.id] = {"whitelist": set(), "blacklist": set(), "whitelist_enabled": False, "blacklist_enabled": False}
    room_settings[ctx.author.id]["whitelist"].add(user.id)
    await ctx.send(f"{user.mention} has been added to your whitelist.")
    save_data()

@bot.slash_command(name="whitelist_remove", description="Remove a user or role from your whitelist")
async def whitelist_remove(ctx, user: discord.Member):
    if ctx.author.id in room_settings and user.id in room_settings[ctx.author.id]["whitelist"]:
        room_settings[ctx.author.id]["whitelist"].remove(user.id)
        await ctx.send(f"{user.mention} has been removed from your whitelist.")
    save_data()

@bot.slash_command(name="whitelist_enable", description="Enable your whitelist for your room")
async def whitelist_enable(ctx):
    if ctx.author.id not in room_settings:
        room_settings[ctx.author.id] = {"whitelist": set(), "blacklist": set(), "whitelist_enabled": False, "blacklist_enabled": False}
    room_settings[ctx.author.id]["whitelist_enabled"] = True
    await ctx.send("Your whitelist has been enabled.")
    save_data()

@bot.slash_command(name="whitelist_disable", description="Disable your whitelist for your room")
async def whitelist_disable(ctx):
    if ctx.author.id in room_settings:
        room_settings[ctx.author.id]["whitelist_enabled"] = False
        await ctx.send("Your whitelist has been disabled.")
    save_data()

@bot.slash_command(name="whitelist_clear", description="Clear your whitelist of all users and roles")
async def whitelist_clear(ctx):
    if ctx.author.id in room_settings:
        room_settings[ctx.author.id]["whitelist"] = set()
        await ctx.send("Your whitelist has been cleared.")
    save_data()

#--------------------------------------#
#           Blacklist Commands         #
#--------------------------------------#
@bot.slash_command(name="blacklist_add", description="Add a user or role to your blacklist")
async def blacklist_add(ctx, user: discord.Member):
    if ctx.author.id not in room_settings:
        room_settings[ctx.author.id] = {"whitelist": set(), "blacklist": set(), "whitelist_enabled": False, "blacklist_enabled": False}
    room_settings[ctx.author.id]["blacklist"].add(user.id)
    await ctx.send(f"{user.mention} has been added to your blacklist.")
    save_data()

@bot.slash_command(name="blacklist_remove", description="Remove a user or role from your blacklist")
async def blacklist_remove(ctx, user: discord.Member):
    if ctx.author.id in room_settings and user.id in room_settings[ctx.author.id]["blacklist"]:
        room_settings[ctx.author.id]["blacklist"].remove(user.id)
        await ctx.send(f"{user.mention} has been removed from your blacklist.")
    save_data()

@bot.slash_command(name="blacklist_enable", description="Enable your blacklist for your room")
async def blacklist_enable(ctx):
    if ctx.author.id not in room_settings:
        room_settings[ctx.author.id] = {"whitelist": set(), "blacklist": set(), "whitelist_enabled": False, "blacklist_enabled": False}
    room_settings[ctx.author.id]["blacklist_enabled"] = True
    await ctx.send("Your blacklist has been enabled.")
    save_data()

@bot.slash_command(name="blacklist_disable", description="Disable your blacklist for your room")
async def blacklist_disable(ctx):
    if ctx.author.id in room_settings:
        room_settings[ctx.author.id]["blacklist_enabled"] = False
        await ctx.send("Your blacklist has been disabled.")
    save_data()

@bot.slash_command(name="blacklist_clear", description="Clear your blacklist of all users and roles")
async def blacklist_clear(ctx):
    if ctx.author.id in room_settings:
        room_settings[ctx.author.id]["blacklist"] = set()
        await ctx.send("Your blacklist has been cleared.")
    save_data()

#--------------------------------------#
#           Allow/Deny Commands        #
#--------------------------------------#

@bot.slash_command(name="allow", description="Allow a user or role to join your room")
async def allow(ctx, user: discord.Member):
    if ctx.author.id not in room_settings:
        room_settings[ctx.author.id] = {"whitelist": set(), "blacklist": set(), "allow": set(), "deny": set(), "whitelist_enabled": False, "blacklist_enabled": False}
    room_settings[ctx.author.id]["allow"].add(user.id)
    await ctx.send(f"{user.mention} has been allowed to join your room.")
    save_data()

@bot.slash_command(name="deny", description="Deny a user or role from joining your room")
async def deny(ctx, user: discord.Member):
    if ctx.author.id not in room_settings:
        room_settings[ctx.author.id] = {"whitelist": set(), "blacklist": set(), "allow": set(), "deny": set(), "whitelist_enabled": False, "blacklist_enabled": False}
    room_settings[ctx.author.id]["deny"].add(user.id)
    await ctx.send(f"{user.mention} has been denied from joining your room.")
    save_data()

#--------------------------------------#
#           Password Commands          #
#--------------------------------------#
@bot.slash_command(name="set_room_password", description="Set a password for your room")
async def set_room_password(ctx, password: str):
    if ctx.author.id not in room_settings:
        room_settings[ctx.author.id] = {"whitelist": set(), "blacklist": set(), "allow": set(), "deny": set(), "whitelist_enabled": False, "blacklist_enabled": False}
    import bcrypt
    room_settings[ctx.author.id]['password'] = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    await ctx.send("Password has been set for your room.")
    save_data()


@bot.slash_command(name="join", description="Join a locked room with a password")
async def join(ctx, user: discord.Member, password: str):
    if user.id in room_settings and "password" in room_settings[user.id]:
        hashed_password = room_settings[user.id]["password"].encode()
        if bcrypt.checkpw(password.encode(), hashed_password):  # Verify the password using bcrypt
            # Find the voice channel that the target user is in
            voice_channel = user.voice.channel if user.voice else None
            if voice_channel:
                # Move the author to the voice channel
                await ctx.author.move_to(voice_channel)
                await ctx.send(f"{ctx.author.mention} has joined the room.")
            else:
                await ctx.send("The user is not in a voice channel.")
        else:
            await ctx.send("Unable to join the room. Incorrect password.")
    else:
        await ctx.send("The user has not set a password for the room.")


@bot.slash_command(name="move_all", description="Move all users with a specific role from all voice channels to a specified channel")
async def move_all(ctx, role: discord.Role, target_channel: discord.VoiceChannel):
    if target_channel is None:
        await ctx.respond("Please specify a valid target channel.")
        return

    if any(role.id for role in ctx.author.roles if role.id in ALLOWED_ROLE_IDS):
        await ctx.respond(f"Starting to move all members with the {role.name} role to {target_channel.name}...")
        
        members_with_role = [member for member in ctx.guild.members if role in member.roles]
        for member in members_with_role:
            if member.voice and member.voice.channel:
                try:
                    await member.move_to(target_channel)
                    await asyncio.sleep(MOVE_DELAY)
                except discord.HTTPException:
                    continue
        
        await ctx.send(f"Moved all members with the {role.name} role to {target_channel.name}")
    else:
        await ctx.respond("You do not have the required role to use this command!")

@bot.slash_command(name="move_us", description="Move all users with a specific role from the user's voice channel to a specified channel")
async def move_us(ctx, role: discord.Role, target_channel: discord.VoiceChannel):
    if target_channel is None:
        await ctx.respond("Please specify a valid target channel.")
        return

    if any(role.id for role in ctx.author.roles if role.id in ALLOWED_ROLE_IDS):
        if ctx.author.voice and ctx.author.voice.channel:
            source_channel = ctx.author.voice.channel
            
            await ctx.respond(f"Starting to move members with the {role.name} role from {source_channel.name} to {target_channel.name}...")
            
            members_with_role_in_source = [member for member in source_channel.members if role in member.roles]
            for member in members_with_role_in_source:
                try:
                    await member.move_to(target_channel)
                    await asyncio.sleep(MOVE_DELAY)
                except discord.HTTPException:
                    continue
            
            await ctx.send(f"Moved members with the {role.name} role from {source_channel.name} to {target_channel.name}")
        else:
            await ctx.respond("You are not in a voice channel!")
    else:
        await ctx.respond("You do not have the required role to use this command!")


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    global rooms
    to_remove = []

    for channel_id, owner_id in rooms.items():
        channel = bot.get_channel(channel_id)
        
        # If the channel doesn't exist or is empty, mark it for removal
        if channel is None or not channel.members:
            to_remove.append(channel_id)

    # Remove marked channels from the rooms dictionary
    for channel_id in to_remove:
        del rooms[channel_id]

    # Optionally, save the updated rooms data to rooms.json
    with open('rooms.json', 'w') as file:
        json.dump(rooms, file)

    print(f'{bot.user.name} has finished checking rooms!')


bot.run(TOKEN)