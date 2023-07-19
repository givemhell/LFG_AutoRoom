import json
from typing import Union
from discord.ext import commands
from discord import Guild, Intents, Member, Role
from discord import PermissionOverwrite
import discord
import os

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

@bot.event
async def on_voice_state_update(member: Member, before, after):
    if before and before.channel:
        if len(before.channel.members) == 0 and bot.user not in before.channel.members and '🛸'  != before.channel.name:

            everyone_role = discord.utils.get(member.guild.roles, name='@everyone')
            overwrites = {
                everyone_role: discord.PermissionOverwrite(
                    create_instant_invite=False, 
                    kick_members=False, 
                    ban_members=False, 
                    administrator=False, 
                    manage_channels=False, 
                    manage_guild=False, 
                    add_reactions=False, 
                    view_audit_log=False, 
                    priority_speaker=False, 
                    stream=False, 
                    read_messages=False, 
                    view_channel=False, 
                    send_messages=False, 
                    send_tts_messages=False, 
                    manage_messages=False, 
                    embed_links=False, 
                    attach_files=False, 
                    read_message_history=False, 
                    mention_everyone=False, 
                    external_emojis=False, 
                    use_external_emojis=False, 
                    view_guild_insights=False, 
                    connect=False, 
                    speak=False, 
                    mute_members=False, 
                    deafen_members=False, 
                    move_members=False, 
                    use_voice_activation=False, 
                    change_nickname=False, 
                    manage_nicknames=False, 
                    manage_roles=False, 
                    manage_permissions=False, 
                    manage_webhooks=False, 
                    manage_emojis=False, 
                    manage_emojis_and_stickers=False, 
                    use_slash_commands=False, 
                    request_to_speak=False, 
                    manage_events=False, 
                    manage_threads=False, 
                    create_public_threads=False, 
                    create_private_threads=False, 
                    send_messages_in_threads=False, 
                    external_stickers=False, 
                    use_external_stickers=False, 
                    start_embedded_activities=False, 
                    moderate_members=False, 
                    send_voice_messages=False
                )
            }
            general_access_role_id = 1130510708942061598  # General Access
            general_access_role = discord.utils.get(member.guild.roles, id=general_access_role_id)
            overwrites[general_access_role] = discord.PermissionOverwrite(
                create_instant_invite=True, 
                add_reactions=True, 
                read_messages=True, 
                view_channel=True, 
                send_messages=True, 
                embed_links=True, 
                attach_files=True, 
                read_message_history=True, 
                connect=True, 
                speak=True,
                use_voice_activation=True, 
                use_slash_commands=True, 
                start_embedded_activities=True,
                external_stickers=True, 
                use_external_stickers=True, 
                external_emojis=True, 
                use_external_emojis=True,
            )
            discord_mod_role_id = 1129832625348038787  # Discord Mod
            discord_mod_role = discord.utils.get(member.guild.roles, id=discord_mod_role_id)
            overwrites[discord_mod_role] = discord.PermissionOverwrite(
                manage_messages=True, 
                mute_members=True, 
                deafen_members=True, 
                move_members=True
            )

            new_channel = await after.channel.category.create_voice_channel(
                name=f'{member.nick if member.nick else member.name}\'s room',
                user_limit=after.channel.user_limit,
                overwrites=overwrites
            )

            await member.move_to(new_channel)

            rooms[new_channel.id] = member.id

            with open('rooms.json', 'w') as file:
                json.dump(rooms, file)

            # Send the welcome embed message to the new channel
            embed_one = discord.Embed(
                title='Welcome to your custom room!',
                description='You can customize your room by clicking emojis:'
            )
            message = await new_channel.send(embed=embed_one)

            # Send the description embed message to the new channel
            embed_two = discord.Embed(
                title='Description control panel',
                description='set icons for your room\n you can only choose 2'
            )
            embed_two.add_field(name='Options', value='🌴 - Chill-out rooms None of the following\nReligion, Politics, Social Justice, Controversial Figures, Sexual Topics, Sensitive Current Events, Cultural Appropriation, Ethical Dilemmas, Conspiracy Theories, Unpopular Opinions\n\n🔞 - 18+ NSFW rooms\n(NO RULES)\n\n⏱ - Mythic+ rooms\nSet a limit on 5 users\n\n🎉 - Celebratory rooms\nfor celebrations or events\n\n🎙️ - Broadcasting rooms\nfor live streaming or broadcasting', inline=True) 
            message = await new_channel.send(embed=embed_two)
            emojis = ['🌴', '🔞', '⏱', '🎉', '🎙️']
            for emoji in emojis:
                await message.add_reaction(emoji)

            # Send the lock embed message to the new channel
            embed_three = discord.Embed(
                title='Lock control panel',
                description='set locks for your room'
            )
            embed_three.add_field(name='Options', value='🎮 - Lock by Game\n🔒 - Private rooms', inline=True)
            message = await new_channel.send(embed=embed_three)
            emojis = ['🎮', '🔒']
            for emoji in emojis:
                await message.add_reaction(emoji)

            # Send the feature embed message to the new channel
            embed_four = discord.Embed(
                title='Feature control panel',
                description='set features for your room'
            )
            embed_four.add_field(name='Options', value='💻 - Screen sharing & Camera\n🔈 - 128 kbps audio quality\n🔉 - 256 kbps audio quality\n🔊 - 386 kbps audio quality', inline=False)
            message = await new_channel.send(embed=embed_four)
            emojis = ['💻', '🔈', '🔉', '🔊']
            for emoji in emojis:
                await message.add_reaction(emoji)

#--------------------------------------#
#           On Reaction Add            #
#--------------------------------------#
@bot.event
async def on_reaction_add(reaction, user):
    # Ignore reactions made by the bot
    if user == bot.user:
        return

    print(reaction.emoji)
    channel = reaction.message.channel
    if not isinstance(channel, discord.VoiceChannel):
        return

    if reaction.emoji == '🌴':
        # Check if the user is the owner of the room
        if rooms.get(channel.id) != user.id:
            print("User is not the owner of the room")
            await channel.send(f'{user.mention} you are not the owner of the room')
            for react in reaction.message.reactions:
                if react.emoji == '🌴':  # Replace with your specific emoji
                    await react.remove(user)  # Remove the reaction of the user 'user'
            return
        # Add functionality for '🌴' reaction here
        await channel.edit(name=f'🌴' + channel.name)

    if reaction.emoji == '🔞':
        # Check if the user is the owner of the room
        if rooms.get(channel.id) != user.id:
            print("User is not the owner of the room")
            await channel.send(f'{user.mention} you are not the owner of the room')
            for react in reaction.message.reactions:
                if react.emoji == '🔞':  # Replace with your specific emoji
                    await react.remove(user)  # Remove the reaction of the user 'user'
            return
        # Add functionality for '🔞' reaction here
        await channel.edit(name=f'🔞' + channel.name)

    if reaction.emoji == '⏱':
        # Check if the user is the owner of the room
        if rooms.get(channel.id) != user.id:
            print("User is not the owner of the room")
            await channel.send(f'{user.mention} you are not the owner of the room')
            for react in reaction.message.reactions:
                if react.emoji == '⏱':
                    await react.remove(user)
            return
        # Add functionality for '⏱' reaction here
        await channel.edit(name=f'⏱' + channel.name)
        # set a max limit of 5 users in the room
        await channel.edit(user_limit=5)

    if reaction.emoji == '🎉':
        # Check if the user is the owner of the room
        if rooms.get(channel.id) != user.id:
            print("User is not the owner of the room")
            await channel.send(f'{user.mention} you are not the owner of the room')
            for react in reaction.message.reactions:
                if react.emoji == '🎉':  # Replace with your specific emoji
                    await react.remove(user)  # Remove the reaction of the user 'user'
            return
        # Add functionality for '🎉' reaction here
        await channel.edit(name=f'🎉' + channel.name)

    if reaction.emoji == '🎙️':
        # Check if the user is the owner of the room
        if rooms.get(channel.id) != user.id:
            print("User is not the owner of the room")
            await channel.send(f'{user.mention} you are not the owner of the room')
            for react in reaction.message.reactions:
                if react.emoji == '🎙️':  # Replace with your specific emoji
                    await react.remove(user)  # Remove the reaction of the user 'user'
            return
        # Add functionality for '🎙️' reaction here
        await channel.edit(name=f'🎙️' + channel.name)

    if reaction.emoji == '🎮':
        # Check if the user is the owner of the room
        if rooms.get(channel.id) != user.id:
            print("User is not the owner of the room")
            await channel.send(f'{user.mention} you are not the owner of the room')
            for react in reaction.message.reactions:
                if react.emoji == '🎮':  # Replace with your specific emoji
                    await react.remove(user)  # Remove the reaction of the user 'user'
            return
        # Add functionality for '🎮' reaction here
        creator = channel.guild.get_member(channel.guild.owner_id)
        if creator is not None and creator.activities:
            await channel.edit(name=f'🎮' + channel.name)
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
        else:
                print('else')
                for react in reaction.message.reactions:
                    if react.emoji == '🎮':  # Replace with your specific emoji
                        await react.remove(user)  # Remove the reaction of the user 'user'
                        await channel.send(f'{user.mention} you are not playing a game')
                        break

    if reaction.emoji == '🔒':
        if rooms.get(channel.id) != user.id:
            print("User is not the owner of the room")
            await channel.send(f'{user.mention} you are not the owner of the room')
            for react in reaction.message.reactions:
                if react.emoji == '🔒':  
                    await react.remove(user)  
            return
    
        await channel.edit(name=f'🔒 {channel.name}')
        
        everyone_role = discord.utils.get(channel.guild.roles, name='@everyone')
        general_access_role_id = 1130510708942061598  
        general_access_role = discord.utils.get(channel.guild.roles, id=general_access_role_id)
        discord_mod_role_id = 1129832625348038787  
        discord_mod_role = discord.utils.get(channel.guild.roles, id=discord_mod_role_id)
    
        # Get the current permissions of the roles in the channel
        everyone_permissions = channel.overwrites_for(everyone_role)
        general_access_permissions = channel.overwrites_for(general_access_role)
        discord_mod_permissions = channel.overwrites_for(discord_mod_role)
    
        # Modify the specific permissions
        everyone_permissions.update(read_messages=False, view_channel=False, connect=False)
        general_access_permissions.update(read_messages=False, connect=False)
        discord_mod_permissions.update(manage_messages=False, mute_members=False, deafen_members=False, move_members=False)
    
        # Set the permissions back
        await channel.set_permissions(everyone_role, overwrite=everyone_permissions)
        await channel.set_permissions(general_access_role, overwrite=general_access_permissions)
        await channel.set_permissions(discord_mod_role, overwrite=discord_mod_permissions)
    
        await channel.send(f'{user.mention} you have locked the room')


    if reaction.emoji == '💻':
        if rooms.get(channel.id) != user.id:
            print("User is not the owner of the room")
            await channel.send(f'{user.mention} you are not the owner of the room')
            for react in reaction.message.reactions:
                if react.emoji == '💻':  
                    await react.remove(user)  
            return
        # Add functionality for '💻' reaction here
        await channel.edit(name=f'💻 {channel.name}')
        general_access_role_id = 1130510708942061598  
        general_access_role = discord.utils.get(channel.guild.roles, id=general_access_role_id)
        # Get the current permissions of the role in the channel
        permissions = channel.overwrites_for(general_access_role)
        # Modify the specific permission
        permissions.update(stream=True)
        # Set the permissions back
        await channel.set_permissions(general_access_role, overwrite=permissions)
        await channel.send(f'{user.mention} you have updated the room permissions')

    if reaction.emoji == '🔈':
        # Check if the user is the owner of the room
        if discord.utils.get(user.roles, id=1129504850028269578) is not None:
            print("User is missing the supporter role")
            await channel.send(f'{user.mention} you are missing the supporter role')
            for react in reaction.message.reactions:
                if react.emoji == '🔈':  # Replace with your specific emoji
                    await react.remove(user)  # Remove the reaction of the user 'user'
            return
        # Add functionality for '🔈' reaction here
        await channel.edit(bitrate=128000)
        await channel.send(f'{user.mention} you have changed the audio quality to 128 kbps')
    if reaction.emoji == '🔉':
        # Check if the user is the owner of the room
        if discord.utils.get(user.roles, id=1077208333024497674) is not None:
            print("User is missing the supporter+ role")
            await channel.send(f'{user.mention} you are missing the supporter+ role')
            for react in reaction.message.reactions:
                if react.emoji == '🔉':
                    await react.remove(user)
            return
        # Add functionality for '🔉' reaction here
        await channel.edit(bitrate=256000)
        await channel.send(f'{user.mention} you have changed the audio quality to 256 kbps')
    if reaction.emoji == '🔊':
        # Check if the user is the owner of the room
        if discord.utils.get(user.roles, id=1129505458147831808) is not None:
            print("User is missing the super supporter role")
            await channel.send(f'{user.mention} you are missing the super supporter role')
            for react in reaction.message.reactions:
                if react.emoji == '🔊':
                    await react.remove(user)
            return
        # Add functionality for '🔊' reaction here
        await channel.edit(bitrate=384000)
        await channel.send(f'{user.mention} you have changed the audio quality to 384 kbps')


#--------------------------------------#
#           On Reaction Remove         #
#--------------------------------------#
@bot.event
async def on_reaction_remove(reaction, user):
    channel = reaction.message.channel
    if not isinstance(channel, discord.VoiceChannel):
        return

    if reaction.emoji == '🎮':
        await channel.edit(name=channel.name.replace(' 🎮', ''))
        # Add functionality for '🎮' reaction here
    if reaction.emoji == '🔒':
        await channel.edit(name=channel.name.replace(' 🔒', ''))
        # Add functionality for '🔒' reaction here
    if reaction.emoji == '🌴':
        await channel.edit(name=channel.name.replace(' 🌴', ''))
        # Add functionality for '🌴' reaction here
    if reaction.emoji == '🔞':
        await channel.edit(name=channel.name.replace(' 🔞', ''))
        # Add functionality for '🔞' reaction here
    if reaction.emoji == '⏱':
        await channel.edit(name=channel.name.replace(' ⏱', ''))
        # Add functionality for '⏱' reaction here
    if reaction.emoji == '🎉':
        await channel.edit(name=channel.name.replace(' 🎉', ''))
        # Add functionality for '🎉' reaction here
    if reaction.emoji == '🎙️':
        await channel.edit(name=channel.name.replace(' 🎙️', ''))
        # Add functionality for '🎙️' reaction here

# video settings
    if reaction.emoji == '💻':
        await channel.edit(name=f'{channel.name} 💻')
        # Add additional functionality for '💻' reaction here

# sound settings
    if reaction.emoji == '🔈':
        if discord.utils.get(user.roles, id=1129504850028269578) is not None:
            await channel.edit(bitrate=64000)
            # Add additional functionality for '🔈' reaction here
    if reaction.emoji == '🔉':
        if discord.utils.get(user.roles, id=1077208333024497674) is not None:
            await channel.edit(bitrate=64000)
            # Add additional functionality for '🔉' reaction here
    if reaction.emoji == '🔊':
        if discord.utils.get(user.roles, id=1129505458147831808) is not None:
            await channel.edit(bitrate=64000)
            # Add additional functionality for '🔊' reaction here

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

bot.run(TOKEN)
