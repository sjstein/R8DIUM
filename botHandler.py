import discord
from discord.ext import commands, tasks   # noqa
import asyncio    # noqa
import dbAccess
import msgHandler
from r8udbBotInclude import TOKEN, BAN_SCAN_TIME
from r8udbBotInclude import USR_LVL0, USR_LVL1, USR_LVL2, CH_ADMIN, BOT_ROLES, CH_LOG, CH_RQD


def msg_auth(interaction):
    channel = str(interaction.channel)
    role_list = [role.name for role in interaction.user.roles]
    role_list.remove('@everyone')
    return channel, role_list


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
    msgHandler.write_log_file(log_msg)  # Write the same message to our local log file
    return log_msg


def check_permissions(interaction, channel_restriction, valid_ch, valid_user):
    '''
    return 'OK' if permissions satisfied
    '''
    channel, roles = msg_auth(interaction)
    if channel_restriction:
        if user_level(roles) <= BOT_ROLES.index(valid_user):
            if channel == valid_ch:
                return 'Ok'
            else:
                return '[r8udbBot: Permissions error] Wrong channel for command'
        else:
            return 'r8udbBot: Permissions error] Invalid user role for command'
    elif user_level(roles) <= BOT_ROLES.index(valid_user):
        return 'Ok'
    else:
        return 'r8udbBot: Permissions error] Invalid user role for command'


def run_discord_bot(ldb):
    from discord import app_commands
    from discord.ext import commands

    client = commands.Bot(command_prefix="!", intents=discord.Intents.all())

    @client.event
    async def on_ready():
        print(f'{client.user} is now running')
        msgHandler.write_log_file(f'------------------')
        msgHandler.write_log_file(f'{client.user} is now running')
        try:
            command_list = await client.tree.sync()
            print(f'Registered {len(command_list)} command(s)')
            msgHandler.write_log_file(f'Registered {len(command_list)} command(s)')
        except Exception as e:
            print(e)
        print(f'Starting banned user periodic checks')
        msgHandler.write_log_file(f'Starting banned user periodic checks')
        scan_banned_users.start(ldb)

    @tasks.loop(seconds=int(BAN_SCAN_TIME))
    async def scan_banned_users(ldb):
        channel_id = discord.utils.get(client.get_all_channels(), name=CH_LOG).id
        channel = client.get_channel(channel_id)
        for record in ldb:
            if record[dbAccess.banned] == 'True':
                if not msgHandler.check_ban_status(record[dbAccess.sid], ldb):
                    msgHandler.unban_user(record[dbAccess.sid], 'Automated check', ldb)
                    print(f'scan_ban just unbanned: {record[dbAccess.sid]}')
                    await channel.send(f'**Automated scan** unbanned: [{record[dbAccess.sid]}] '
                                       f'{record[dbAccess.discord_name]}')

    @client.tree.command(name='bot_commands', description=f'Show all commands available [{USR_LVL1}]')
    async def bot_commands(interaction: discord.Interaction):
        permission = check_permissions(interaction, CH_RQD, CH_ADMIN, USR_LVL1)
        if permission == 'Ok':
            if CH_LOG != 'none':
                log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
                await log_channel.send(log_message(interaction))
            response = ''
            command_list = await client.tree.fetch_commands()
            for command in command_list:
                response += f'**{command.name}** : *{command.description}*\n'
        else:
            response = permission
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='list_users', description=f'List all users in database [{USR_LVL1}]')
    async def list_users(interaction: discord.Interaction):
        permission = check_permissions(interaction, CH_RQD, CH_ADMIN, USR_LVL1)
        if permission == 'Ok':
            if CH_LOG != 'none':
                log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
                await log_channel.send(log_message(interaction))
            response = msgHandler.list_users(ldb)
        else:
            response = permission
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='read_notes',
                         description=f'Display all notes for user <sid>[{USR_LVL1}]')
    @app_commands.describe(sid='The SID of the user')
    async def read_notes(interaction: discord.Interaction, sid: int):
        permission = check_permissions(interaction, CH_RQD, CH_ADMIN, USR_LVL1)
        if permission == 'Ok':
            if CH_LOG != 'none':
                log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
                await log_channel.send(log_message(interaction))
            response = '* ' + msgHandler.show_notes(sid, ldb).replace('|', '\n* ')
        else:
            response = permission
        if successful_cmd and CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)   # return channel id from name
            await log_channel.send(log_message(interaction))
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='write_note',
                         description=f'write note about <sid> [{USR_LVL1}]')
    @app_commands.describe(sid='The SID of the user',
                           note='Note to add to user data')
    async def write_note(interaction: discord.Interaction, sid: int, note: str):
        permission = check_permissions(interaction, CH_RQD, CH_ADMIN, USR_LVL1)
        if permission == 'Ok':
            if CH_LOG != 'none':
                log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
                await log_channel.send(log_message(interaction))
            response = msgHandler.add_note(sid, note, ldb)
        else:
            response = permission
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='show_user',
                         description=f'Display all fields for user <sid>[{USR_LVL1}]')
    @app_commands.describe(sid='The SID of the user')
    async def show_user(interaction: discord.Interaction, sid: int):
        permission = check_permissions(interaction, CH_RQD, CH_ADMIN, USR_LVL1)
        if permission == 'Ok':
            if CH_LOG != 'none':
                log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
                await log_channel.send(log_message(interaction))
            response = msgHandler.show_user(sid, ldb)
        else:
            response = permission
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='add_user',
                         description=f'Add a new user <discord_id> [{USR_LVL1}]')
    @app_commands.describe(discord_id='@id')
    async def add_user(interaction: discord.Interaction, discord_id: str):
        permission = check_permissions(interaction, CH_RQD, CH_ADMIN, USR_LVL1)
        if permission == 'Ok':
            if CH_LOG != 'none':
                log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
                await log_channel.send(log_message(interaction))
            discord_name = await client.fetch_user(int(discord_id[2:-1]))
            response = msgHandler.add_user(discord_id, discord_name, ldb)
        else:
            response = permission
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='change_roll',
                         description=f'Set role <role_str> to user <sid> [{USR_LVL1}]')
    @app_commands.describe(sid='user SID', role='role name')
    async def change_roll(interaction: discord.Interaction, sid: int, role: str):
        permission = check_permissions(interaction, CH_RQD, CH_ADMIN, USR_LVL1)
        if permission == 'Ok':
            if CH_LOG != 'none':
                log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
                await log_channel.send(log_message(interaction))
            response = msgHandler.add_role(sid, role, ldb)
        else:
            response = permission
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='del_user',
                         description=f'Delete user <sid> [{USR_LVL1}]')
    @app_commands.describe(sid='User SID')
    async def del_user(interaction: discord.Interaction, sid: str):
        permission = check_permissions(interaction, CH_RQD, CH_ADMIN, USR_LVL1)
        if permission == 'Ok':
            if CH_LOG != 'none':
                log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
                await log_channel.send(log_message(interaction))
            response = msgHandler.delete_user(sid, ldb)
        else:
            response = permission
            await log_channel.send(log_message(interaction))
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='ban_user',
                         description=f'ban user <sid> <duration(days)> <reason(string)> [{USR_LVL1}]')
    @app_commands.describe(sid='The SID of the user',
                           duration='Length of ban in days',
                           reason='Reason for ban (short description)')
    async def ban_user(interaction: discord.Interaction, sid: int, duration: int, reason: str):
        permission = check_permissions(interaction, CH_RQD, CH_ADMIN, USR_LVL1)
        if permission == 'Ok':
            if CH_LOG != 'none':
                log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
                await log_channel.send(log_message(interaction))
            response = msgHandler.ban_user(sid, duration, reason, ldb)
        else:
            response = permission
        # Write a message on the admin channel letting other admins know a user has been banned
        admin_channel = discord.utils.get(interaction.guild.channels, name=CH_ADMIN)
        await admin_channel.send(response)
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='unban_user',
                         description=f'unban user <sid> [{USR_LVL1}]')
    @app_commands.describe(sid='The SID of the user')
    async def unban_user(interaction: discord.Interaction, sid: int):
        permission = check_permissions(interaction, CH_RQD, CH_ADMIN, USR_LVL1)
        if permission == 'Ok':
            if CH_LOG != 'none':
                log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
                await log_channel.send(log_message(interaction))
            response = msgHandler.unban_user(sid, interaction.user.name, ldb)
        else:
            response = permission
        # Write a user to the admin channel letting other admins know a user has been un-banned
        admin_channel = discord.utils.get(interaction.guild.channels, name=CH_ADMIN)
        await admin_channel.send(response)
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='generate_pass',
                         description=f'Generate a new password for user <sid> [{USR_LVL1}]')
    @app_commands.describe(sid='The SID of the user')
    async def generate_pass(interaction: discord.Interaction, sid: int):
        permission = check_permissions(interaction, CH_RQD, CH_ADMIN, USR_LVL1)
        if permission == 'Ok':
            if CH_LOG != 'none':
                log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
                await log_channel.send(log_message(interaction))
            user_id = dbAccess.get_element(sid, dbAccess.sid, dbAccess.discord_id, ldb)
            response = msgHandler.new_pass(user_id, ldb)
        else:
            response = permission
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='arb_read',
                         description=f'read value of field <field> of user <sid> [{USR_LVL1}]')
    @app_commands.describe(sid='The SID of the user',
                           field='Field name to show')
    async def arb_read(interaction: discord.Interaction, sid: int, field: str):
        permission = check_permissions(interaction, CH_RQD, CH_ADMIN, USR_LVL1)
        if permission == 'Ok':
            if CH_LOG != 'none':
                log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
                await log_channel.send(log_message(interaction))
            response = f'{field} : {msgHandler.read_field(sid, field, ldb)}'
        else:
            response = permission
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='arb_write',
                         description=f'write value <val> to field <field> of user <sid> [{USR_LVL0}]')
    @app_commands.describe(sid='The SID of the user',
                           field='Field name to write to',
                           val='Value to write')
    async def arb_write(interaction: discord.Interaction, sid: int, field: str, val: str = ''):
        permission = check_permissions(interaction, CH_RQD, CH_ADMIN, USR_LVL0)
        if permission == 'Ok':
            if CH_LOG != 'none':
                log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
                await log_channel.send(log_message(interaction))
            response = msgHandler.write_field(sid, field, val, ldb)
        else:
            response = permission
        await interaction.response.send_message(response, ephemeral=True)  # noqa

# The following two commands are available to all users if they are at USR_LVL2 or better
# This allows uers who have server access to check and refresh their password from any channel
    @client.tree.command(name='show_password',
                         description=f'Display your Run8 server password in a message only you can see')
    async def show_password(interaction: discord.Interaction):
        channel, roles = msg_auth(interaction)
        user_id = str(interaction.user.id)
        if user_level(roles) <= BOT_ROLES.index(USR_LVL2):
            if CH_LOG != 'none':
                log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
                await log_channel.send(log_message(interaction))
            response = msgHandler.show_pass(user_id, ldb)
        else:
            response = 'You currently do not have access to the server, please contact an admin [err0]'
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='refresh_pass',
                         description=f'Refresh your Run8 server password and display in a message only you can see')
    async def refresh_pass(interaction: discord.Interaction):
        channel, roles = msg_auth(interaction)
        user_id = str(interaction.user.id)
        if user_level(roles) <= BOT_ROLES.index(USR_LVL2):
            if CH_LOG != 'none':
                log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
                await log_channel.send(log_message(interaction))
            response = msgHandler.new_pass(user_id, ldb)
        else:
            response = 'You currently do not have access to the server, please contact an admin [err1]'
        await interaction.response.send_message(response, ephemeral=True)  # noqa


    # The following block of code was removed after auto-updates to the HostSecurity file was added
    #  However, I left in for the possible future situation where this functionality is desired.
    #
    # @client.tree.command(name='security_write',
    #                      description=f'write the host security file [{USR_LVL0}]')
    # async def security_write(interaction: discord.Interaction):
    #     channel, roles = msg_auth(interaction)
    #     successful_cmd = False
    #     if user_level(roles) <= BOT_ROLES.index(USR_LVL0):
    #         if channel == CH_ADMIN:
    #             successful_cmd = True
    #             response = dbAccess.write_security_file(ldb)
    #         else:
    #             response = '[r8udbBot: Permissions error] Wrong channel for command'
    #     else:
    #         response = '[r8udbBot: Permissions error] Invalid user role for command'
    #     if successful_cmd and CH_LOG != 'none':
    #         log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)   # return channel id from name
    #         await log_channel.send(log_message(interaction))
    #     await interaction.response.send_message(response, ephemeral=False)
    #
    # @client.tree.command(name='security_merge',
    #                      description=f'merge security file into database [{USR_LVL0}]')
    # async def security_merge(interaction: discord.Interaction):
    #     channel, roles = msg_auth(interaction)
    #     successful_cmd = False
    #     if user_level(roles) <= BOT_ROLES.index(USR_LVL0):
    #         if channel == CH_ADMIN:
    #             successful_cmd = True
    #             response = dbAccess.merge_security_file(ldb)
    #         else:
    #             response = '[r8udbBot: Permissions error] Wrong channel for command'
    #     else:
    #         response = '[r8udbBot: Permissions error] Invalid user role for command'
    #     if successful_cmd and CH_LOG != 'none':
    #         log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)   # return channel id from name
    #         await log_channel.send(log_message(interaction))
    #     await interaction.response.send_message(response, ephemeral=False)

    client.run(TOKEN)