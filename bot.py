import json
from typing import Union
from discord.ext import commands
from discord import Guild, Intents, Member, Role
from discord import PermissionOverwrite
import discord
import os
import asyncio

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

# Load bot token
with open('bot_token.txt', 'r') as file:
    TOKEN = file.read().strip()

# Load rooms
if os.path.exists('rooms.json'):
    with open('rooms.json', 'r') as file:
        rooms = json.load(file)
else:
    rooms = {}

# Load blacklist_data
if os.path.exists('blacklist_data.json'):
    with open('blacklist_data.json', 'r') as file:
        blacklist_data = json.load(file)
else:
    blacklist_data = {}


@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user:  # Ignore bot's own voice state updates
        return

    # When a user leaves a channel
    if before.channel is not None and after.channel is None:
        if before.channel.id in rooms and rooms[before.channel.id] == member.id:
            await asyncio.sleep(30)  # Wait for 30sec
            if before.channel.members == []:
                await before.channel.delete()
                del rooms[before.channel.id]

    # Do something when a user joins a '🛸' channel
    elif after.channel and '🛸' in after.channel.name:
        # Get the permission overwrites from the 🛸 channel
        overwrites = after.channel.overwrites
        # Get the blacklisted users
        blacklist = blacklist_data.get(member.id, set())
        for blacklisted_user_id in blacklist:
            blacklisted_member = discord.utils.get(member.guild.members, id=blacklisted_user_id)
            if blacklisted_member:  # Ensure the member was found
                overwrites[blacklisted_member] = discord.PermissionOverwrite(connect=False)

        new_channel = await after.channel.category.create_voice_channel(
            name=f'👽┃{member.nick if member.nick else member.name}\'s room',
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
                              '📋 - Enable whitelist\n\n', inline=False)

        embed.add_field(name='Audio Quality',
                        value='set the audio quality\n'
                              '🔈 - 128 kbps audio quality\n'
                              '🔉 - 256 kbps audio quality\n'
                              '🔊 - 386 kbps audio quality\n\n', inline=False)

        embed.add_field(name='Feature Control Panel',
                        value='set features for your room\n'
                              '💻 - Screen sharing & Camera\n'
                              '💾 - Update room name (will take some time)\n\n', inline=False)

        message = await new_channel.send(embed=embed)
        emojis = ['🌴', '🔞', '⏱', '🎉', '🎙️', '🃏', '📺', '🔒', '🎮', '📋', '🔈', '🔉', '🔊', '💻', '💾']
        for emoji in emojis:
            await message.add_reaction(emoji)

    with open('rooms.json', 'w') as file:
        json.dump(rooms, file)

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
# 🌴 Add Reaction Function
async def handle_palm_tree(reaction, user):
    channel = reaction.message.channel
    # Add function to 🌴 reaction

# 🔞 Add Reaction Function
async def handle_adult_content(reaction, user):
    channel = reaction.message.channel
    # Add function to 🔞 reaction

# ⏱ Add Reaction Function
async def handle_timer(reaction, user):
    channel = reaction.message.channel
    # Add function to ⏱ reaction
    await channel.edit(user_limit=5)

# 🎉 Add Reaction Function
async def handle_party(reaction, user):
    channel = reaction.message.channel
    # Add function to 🎉 reaction

# 🎙️ Add Reaction Function
async def handle_microphone(reaction, user):
    channel = reaction.message.channel
    # Add function to 🎙️ reaction

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
    await channel.send(embed=embed)
    pass

# 📺 Add Reaction Function
async def handle_tv(reaction, user):
    channel = reaction.message.channel
    # Add function to 📺 reaction
    # Get the role
    general_access_role_id = 1070344422799200306
    general_access_role = discord.utils.get(channel.guild.roles, id=general_access_role_id)
    # Get the current permissions of the role in the channel
    permissions = channel.overwrites_for(general_access_role)
    # Modify the 'speak' permission
    permissions.update(speak=False)
    # Apply the modified permissions
    await channel.set_permissions(general_access_role, overwrite=permissions)

# 🎮 Add Reaction Function
async def handle_video_game(reaction, user):
    channel = reaction.message.channel
    # Add function to 🎮 reaction
    creator = channel.guild.get_member(channel.guild.owner_id)
    if creator is not None and creator.activities:
        # await channel.edit(name=f'🎮' + channel.name)
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
            await channel.edit(overwrites=overwrites)
            pass

# 🔒 Add Reaction Function
async def handle_lock(reaction, user):
    channel = reaction.message.channel
    # Add function to 🔒 reaction
    everyone_role = discord.utils.get(channel.guild.roles, name='@everyone')
    general_access_role_id = 1070344422799200306
    general_access_role = discord.utils.get(channel.guild.roles, id=general_access_role_id)
    discord_mod_role_id = 578664579584753685
    discord_mod_role = discord.utils.get(channel.guild.roles, id=discord_mod_role_id)
    # Get the current permissions of the roles in the channel
    everyone_permissions = channel.overwrites_for(everyone_role)
    general_access_permissions = channel.overwrites_for(general_access_role)
    discord_mod_permissions = channel.overwrites_for(discord_mod_role)
    # Modify the specific permissions
    everyone_permissions.update(read_messages=False, view_channel=False, connect=False)
    general_access_permissions.update(read_messages=False, view_channel=True, connect=False)
    discord_mod_permissions.update(manage_messages=False, mute_members=False, deafen_members=False, move_members=False)
    # Set the permissions back
    await channel.set_permissions(everyone_role, overwrite=everyone_permissions)
    await channel.set_permissions(general_access_role, overwrite=general_access_permissions)
    await channel.set_permissions(discord_mod_role, overwrite=discord_mod_permissions)
    await channel.send(f'{user.mention} you have locked the room')
    pass
 
# 💾 Add Reaction Function
async def handle_save(reaction, user):
    channel = reaction.message.channel
    # Add function to 💾 reaction
    owner = user
    message = reaction.message
    reactions = message.reactions
    emoji_order = ['🔒', '🎮', '📋', '🌴', '🔞', '⏱', '🎉', '🎙️', '🃏', '📺', '💻', '🔊', '🔉', '🔈']
    emoji_priority = {emoji: i for i, emoji in enumerate(emoji_order)}
    emoji_name_list = sorted([(react.emoji, emoji_priority.get(react.emoji, float('inf'))) for react in reactions if owner in await react.users().flatten() and react.emoji != '💾'], key=lambda x: x[1])
    # Only add '👽' if no other emojis were used
    if emoji_name_list:
        channel_name = channel.name.replace('👽', '').strip()
    else:
        channel_name = channel.name
    new_channel_name = ''.join(emoji for emoji, _ in emoji_name_list) + '' + channel_name
    await channel.edit(name=new_channel_name)
    await channel.send(f'{user.mention} you have updated the room name')

# 💻 Add Reaction Function
async def handle_computer(reaction, user):
    channel = reaction.message.channel
    # Add function to 💻 reaction
    general_access_role_id = 1070344422799200306  
    general_access_role = discord.utils.get(channel.guild.roles, id=general_access_role_id)
    # Get the current permissions of the role in the channel
    permissions = channel.overwrites_for(general_access_role)
    # Modify the specific permission
    permissions.update(stream=True)
    # Set the permissions back
    await channel.set_permissions(general_access_role, overwrite=permissions)
    await channel.send(f'{user.mention} you have updated the room permissions')
    pass

# 🔈 Add Reaction Function
async def handle_volume_down(reaction, user):
    channel = reaction.message.channel
    # Add function to 🔈 reaction
    await channel.edit(bitrate=128000)
    await channel.send(f'{user.mention} you have changed the audio quality to 128 kbps')

# 🔉 Add Reaction Function
async def handle_volume_medium(reaction, user):
    channel = reaction.message.channel
    # Add function to 🔉 reaction
    await channel.edit(bitrate=256000)
    await channel.send(f'{user.mention} you have changed the audio quality to 256 kbps')

# 🔊 Add Reaction Function
async def handle_volume_up(reaction, user):
    channel = reaction.message.channel
    # Add function to 🔊 reaction
    await channel.edit(bitrate=384000)
    await channel.send(f'{user.mention} you have changed the audio quality to 384 kbps')

# 📋 Add Reaction Function
async def handle_clipboard(reaction, user):
    channel = reaction.message.channel
    # Add function to 📋 reaction

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
#             On Message               #
#--------------------------------------#

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

bot.run(TOKEN)