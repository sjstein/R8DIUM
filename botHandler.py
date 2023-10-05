import discord

import dbAccess
import msgHandler
from r8udbBotInclude import TOKEN, DB_FILENAME
from r8udbBotInclude import USR_LVL0, USR_LVL1, USR_LVL2, CH_USER, CH_ADMIN, BOT_ROLES, CH_LOG


def msg_auth(interaction):
    channel = str(interaction.channel)
    rolelist = [role.name for role in interaction.user.roles]
    rolelist.remove('@everyone')
    return channel, rolelist


def user_level(roles):
    security_lvl = 100  # Base level - highest number
    common_roles = [i for i in roles if i in BOT_ROLES]
    if len(common_roles) > 0:
        for single_role in common_roles:
            if BOT_ROLES.index(single_role) < security_lvl:
                security_lvl = BOT_ROLES.index(single_role)
    return security_lvl


def log_message(interaction) -> str:
    log_msg = f'**{interaction.user.name} ({interaction.user.display_name})** executed: `{interaction.command.name} '
    if 'options' in interaction.data:
        for parm in interaction.data['options']:
            log_msg += f'{parm["value"]} '
        log_msg = log_msg[:-1]
    log_msg += f'` in channel: *{interaction.channel}*'
    return log_msg


def run_new_discord_bot(ldb):
    from discord import app_commands
    from discord.ext import commands

    client = commands.Bot(command_prefix="!", intents=discord.Intents.all())

    @client.event
    async def on_ready():
        print(f'{client.user} is now running')
        try:
            command_list = await client.tree.sync()
            print(f'Registered {len(command_list)} command(s)')
        except Exception as e:
            print(e)

    @client.tree.command(name='bot_commands', description=f'Show all commands available [{USR_LVL1}]')
    async def bot_commands(interaction: discord.Interaction):
        channel, roles = msg_auth(interaction)
        successful_cmd = False
        if user_level(roles) <= BOT_ROLES.index(USR_LVL1):
            if channel == CH_ADMIN:
                successful_cmd = True
                response = ''
                command_list = await client.tree.fetch_commands()
                for command in command_list:
                    response += f'**{command.name}** : *{command.description}*\n'
            else:
                response = '[r8udbBot: Permissions error] Wrong channel for command'
        else:
            response = '[r8udbBot: Permissions error] Invalid user role for command'
        if successful_cmd and CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)   # return channel id from name
            await log_channel.send(log_message(interaction))
        await interaction.response.send_message(response, ephemeral=False)

    @client.tree.command(name='list_users', description=f'List all users in db [{USR_LVL1}]')
    async def list_users(interaction: discord.Interaction):
        channel, roles = msg_auth(interaction)
        successful_cmd = False
        if user_level(roles) <= BOT_ROLES.index(USR_LVL1):
            if channel == CH_ADMIN:
                successful_cmd = True
                response = msgHandler.list_users(ldb)
            else:
                response = '[r8udbBot: Permissions error] Wrong channel for command'
        else:
            response = '[r8udbBot: Permissions error] Invalid user role for command'
        if successful_cmd and CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)   # return channel id from name
            await log_channel.send(log_message(interaction))
        await interaction.response.send_message(response, ephemeral=False)

    @client.tree.command(name='read_notes',
                         description=f'Display all notes for user [{USR_LVL1}]')
    @app_commands.describe(sid='The SID of the user')
    async def read_notes(interaction: discord.Interaction, sid: int):
        channel, roles = msg_auth(interaction)
        successful_cmd = False
        if user_level(roles) <= BOT_ROLES.index(USR_LVL1):
            if channel == CH_ADMIN:
                successful_cmd = True
                response = '* ' + msgHandler.show_notes(sid, ldb).replace('|', '\n* ')
            else:
                response = '[r8udbBot: Permissions error] Wrong channel for command'
        else:
            response = '[r8udbBot: Permissions error] Invalid user role for command'
        if successful_cmd and CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)   # return channel id from name
            await log_channel.send(log_message(interaction))
        await interaction.response.send_message(response, ephemeral=False)

    @client.tree.command(name='write_note',
                         description=f'write note about <sid> [{USR_LVL1}]')
    @app_commands.describe(sid='The SID of the user',
                           note='Note to add to user data')
    async def write_note(interaction: discord.Interaction, sid: int, note: str):
        channel, roles = msg_auth(interaction)
        successful_cmd = False
        if user_level(roles) <= BOT_ROLES.index(USR_LVL1):
            if channel == CH_ADMIN:
                successful_cmd = True
                response = msgHandler.add_note(sid, note, ldb)
            else:
                response = '[r8udbBot: Permissions error] Wrong channel for command'
        else:
            response = '[r8udbBot: Permissions error] Invalid user role for command'
        if successful_cmd and CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)   # return channel id from name
            await log_channel.send(log_message(interaction))
        await interaction.response.send_message(response, ephemeral=False)

    @client.tree.command(name='show_user',
                         description=f'Display all fields for user [{USR_LVL1}]')
    @app_commands.describe(sid='The SID of the user')
    async def show_user(interaction: discord.Interaction, sid: int):
        channel, roles = msg_auth(interaction)
        successful_cmd = False
        if user_level(roles) <= BOT_ROLES.index(USR_LVL1):
            if channel == CH_ADMIN:
                successful_cmd = True
                response = msgHandler.show_user(sid, ldb)
            else:
                response = '[r8udbBot: Permissions error] Wrong channel for command'
        else:
            response = '[r8udbBot: Permissions error] Invalid user role for command'
        if successful_cmd and CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)   # return channel id from name
            await log_channel.send(log_message(interaction))
        await interaction.response.send_message(response, ephemeral=False)

    @client.tree.command(name='add_user',
                         description=f'Add a new user <discord_id> [{USR_LVL1}]')
    @app_commands.describe(discord_id='@id')
    async def add_user(interaction: discord.Interaction, discord_id: str):
        channel, roles = msg_auth(interaction)
        successful_cmd = False
        if user_level(roles) <= BOT_ROLES.index(USR_LVL1):
            if channel == CH_ADMIN:
                successful_cmd = True
                discord_name = await client.fetch_user(int(discord_id[2:-1]))
                response = msgHandler.add_user(discord_id, discord_name, ldb)
            else:
                response = '[r8udbBot: Permissions error] Wrong channel for command'
        else:
            response = '[r8udbBot: Permissions error] Invalid user role for command'
        if successful_cmd and CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)   # return channel id from name
            await log_channel.send(log_message(interaction))
        await interaction.response.send_message(response, ephemeral=False)

    @client.tree.command(name='del_user',
                         description=f'Delete user <sid> [{USR_LVL1}]')
    @app_commands.describe(sid='User SID')
    async def del_user(interaction: discord.Interaction, sid: str):
        channel, roles = msg_auth(interaction)
        successful_cmd = False
        if user_level(roles) <= BOT_ROLES.index(USR_LVL1):
            if channel == CH_ADMIN:
                successful_cmd = True
                response = msgHandler.delete_user(sid, ldb)
            else:
                response = '[r8udbBot: Permissions error] Wrong channel for command'
        else:
            response = '[r8udbBot: Permissions error] Invalid user role for command'
        if successful_cmd and CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)   # return channel id from name
            await log_channel.send(log_message(interaction))
        await interaction.response.send_message(response, ephemeral=False)

    @client.tree.command(name='ban_user',
                         description=f'ban user <sid> <duration(days)> <reason(string)> [{USR_LVL1}]')
    @app_commands.describe(sid='The SID of the user',
                           duration='Length of ban in days',
                           reason='Reason for ban (short description)')
    async def ban_user(interaction: discord.Interaction, sid: int, duration: int, reason: str):
        channel, roles = msg_auth(interaction)
        successful_cmd = False
        if user_level(roles) <= BOT_ROLES.index(USR_LVL1):
            if channel == CH_ADMIN:
                successful_cmd = True
                response = msgHandler.ban_user(sid, duration, reason, ldb)
            else:
                response = '[r8udbBot: Permissions error] Wrong channel for command'
        else:
            response = '[r8udbBot: Permissions error] Invalid user role for command'
        if successful_cmd and CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)   # return channel id from name
            await log_channel.send(log_message(interaction))
        await interaction.response.send_message(response, ephemeral=False)

    @client.tree.command(name='unban_user',
                         description=f'unban user <sid> [{USR_LVL1}]')
    @app_commands.describe(sid='The SID of the user')
    async def unban_user(interaction: discord.Interaction, sid: int):
        channel, roles = msg_auth(interaction)
        successful_cmd = False
        if user_level(roles) <= BOT_ROLES.index(USR_LVL1):
            if channel == CH_ADMIN:
                successful_cmd = True
                response = msgHandler.unban_user(sid, interaction.user.name, ldb)
            else:
                response = '[r8udbBot: Permissions error] Wrong channel for command'
        else:
            response = '[r8udbBot: Permissions error] Invalid user role for command'
        if successful_cmd and CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)   # return channel id from name
            await log_channel.send(log_message(interaction))
        await interaction.response.send_message(response, ephemeral=False)

    @client.tree.command(name='show_password',
                         description=f'Show your password (your eyes only) [{USR_LVL2}]')
    async def show_password(interaction: discord.Interaction):
        channel, roles = msg_auth(interaction)
        successful_cmd = False
        user_id = str(interaction.user.id)
        if user_level(roles) <= BOT_ROLES.index(USR_LVL2):
            successful_cmd = True
            response = msgHandler.show_pass(user_id, ldb)
        else:
            response = '[r8udbBot: Permissions error] Invalid user role for command'
        if successful_cmd and CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)   # return channel id from name
            await log_channel.send(log_message(interaction))
        await interaction.response.send_message(response, ephemeral=True)

    @client.tree.command(name='refresh_pass',
                         description=f"Refresh user's password (your eyes only) [{USR_LVL2}]")
    async def refresh_pass(interaction: discord.Interaction):
        channel, roles = msg_auth(interaction)
        successful_cmd = False
        user_id = str(interaction.user.id)
        if user_level(roles) <= BOT_ROLES.index(USR_LVL2):
            successful_cmd = True
            response = msgHandler.new_pass(user_id, ldb)
        else:
            response = '[r8udbBot: Permissions error] Invalid user role for command'
        if successful_cmd and CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)   # return channel id from name
            await log_channel.send(log_message(interaction))
        await interaction.response.send_message(response, ephemeral=True)

    @client.tree.command(name='generate_pass',
                         description=f'Generate a new password for user <sid> [{USR_LVL1}]')
    @app_commands.describe(sid='The SID of the user')
    async def generate_pass(interaction: discord.Interaction, sid: int):
        channel, roles = msg_auth(interaction)
        successful_cmd = False
        if user_level(roles) <= BOT_ROLES.index(USR_LVL1):
            if channel == CH_ADMIN:
                successful_cmd = True
                user_id = dbAccess.get_element(sid, dbAccess.sid, dbAccess.discord_id, ldb)
                response = msgHandler.new_pass(user_id, ldb)
            else:
                response = '[r8udbBot: Permissions error] Wrong channel for command'
        else:
            response = '[r8udbBot: Permissions error] Invalid user role for command'
        if successful_cmd and CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)   # return channel id from name
            await log_channel.send(log_message(interaction))
        await interaction.response.send_message(response, ephemeral=False)

    @client.tree.command(name='arb_read',
                         description=f'read value of field <field> of user <sid> [{USR_LVL1}]')
    @app_commands.describe(sid='The SID of the user',
                           field='Field name to show')
    async def arb_read(interaction: discord.Interaction, sid: int, field: str):
        channel, roles = msg_auth(interaction)
        successful_cmd = False
        if user_level(roles) <= BOT_ROLES.index(USR_LVL1):
            if channel == CH_ADMIN:
                successful_cmd = True
                response = f'{field} : {msgHandler.read_field(sid, field, ldb)}'
            else:
                response = '[r8udbBot: Permissions error] Wrong channel for command'
        else:
            response = '[r8udbBot: Permissions error] Invalid user role for command'
        if successful_cmd and CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)   # return channel id from name
            await log_channel.send(log_message(interaction))
        await interaction.response.send_message(response, ephemeral=False)

    @client.tree.command(name='arb_write',
                         description=f'write value <val> to field <field> of user <sid> [{USR_LVL0}]')
    @app_commands.describe(sid='The SID of the user',
                           field='Field name to write to',
                           val='Value to write')
    async def arb_write(interaction: discord.Interaction, sid: int, field: str, val: str = ''):
        channel, roles = msg_auth(interaction)
        successful_cmd = False
        if user_level(roles) <= BOT_ROLES.index(USR_LVL0):
            if channel == CH_ADMIN:
                successful_cmd = True
                response = msgHandler.write_field(sid, field, val, ldb)
            else:
                response = '[r8udbBot: Permissions error] Wrong channel for command'
        else:
            response = '[r8udbBot: Permissions error] Invalid user role for command'
        if successful_cmd and CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)   # return channel id from name
            await log_channel.send(log_message(interaction))
        await interaction.response.send_message(response, ephemeral=False)

    @client.tree.command(name='security_write',
                         description=f'write the host security file [{USR_LVL0}]')
    async def security_write(interaction: discord.Interaction):
        channel, roles = msg_auth(interaction)
        successful_cmd = False
        if user_level(roles) <= BOT_ROLES.index(USR_LVL0):
            if channel == CH_ADMIN:
                successful_cmd = True
                response = dbAccess.write_security_file(ldb)
            else:
                response = '[r8udbBot: Permissions error] Wrong channel for command'
        else:
            response = '[r8udbBot: Permissions error] Invalid user role for command'
        if successful_cmd and CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)   # return channel id from name
            await log_channel.send(log_message(interaction))
        await interaction.response.send_message(response, ephemeral=False)

    @client.tree.command(name='security_merge',
                         description=f'merge security file into database [{USR_LVL0}]')
    async def security_merge(interaction: discord.Interaction):
        channel, roles = msg_auth(interaction)
        successful_cmd = False
        if user_level(roles) <= BOT_ROLES.index(USR_LVL0):
            if channel == CH_ADMIN:
                successful_cmd = True
                response = dbAccess.merge_security_file(ldb)
            else:
                response = '[r8udbBot: Permissions error] Wrong channel for command'
        else:
            response = '[r8udbBot: Permissions error] Invalid user role for command'
        if successful_cmd and CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)   # return channel id from name
            await log_channel.send(log_message(interaction))
        await interaction.response.send_message(response, ephemeral=False)

    client.run(TOKEN)