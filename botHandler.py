#########################
# R8DIUM : Run8 Database for Integrated User Management
#
# Copyright (C) 2023, S. Joshua Stein, <s.joshua.stein@gmail.com>
#
# This file is part of the R8DIUM software tool suite.
#
# R8DIUM is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# R8DIUM is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with R8DIUM.
# If not, see <https://www.gnu.org/licenses/>.
##########################
import discord
from discord.ext import commands, tasks   # noqa
import asyncio    # noqa
import dbAccess
import msgHandler
from r8diumInclude import TOKEN, BAN_SCAN_TIME, SOFTWARE_VERSION, CH_ADMIN, CH_LOG, R8SERVER_ADDR, R8SERVER_PORT


def log_message(interaction) -> str:
    log_msg = f'**{interaction.user.name} ({interaction.user.display_name})** executed: `{interaction.command.name} '
    if 'options' in interaction.data:
        for parm in interaction.data['options']:
            log_msg += f'{parm["value"]} '
        log_msg = log_msg[:-1]
    log_msg += f'` in channel: *{interaction.channel}*'
    msgHandler.write_log_file(log_msg)  # Write the same message to our local log file
    return log_msg


def run_discord_bot(ldb):
    from discord import app_commands
    from discord.ext import commands

    client = commands.Bot(command_prefix="!", intents=discord.Intents.all())

    @client.event
    async def on_ready():
        print(f'Discord bot [{client.user}] is now running')
        msgHandler.write_log_file(f'------------------')
        msgHandler.write_log_file(f'R8DIUM [{SOFTWARE_VERSION}] starting')
        msgHandler.write_log_file(f'Discord bot [{client.user}] is now running')
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
    async def scan_banned_users(local_db):
        if type(local_db) != list:   # local_db must be empty - showing as NoneType
            return
        channel_id = discord.utils.get(client.get_all_channels(), name=CH_LOG).id
        channel = client.get_channel(channel_id)
        for record in local_db:
            if record[dbAccess.banned] == 'True':
                if not msgHandler.check_ban_status(record[dbAccess.sid], local_db):
                    msgHandler.unban_user(record[dbAccess.sid], 'Automated check', local_db)
                    print(f'scan_ban just unbanned: {record[dbAccess.sid]}')
                    await channel.send(f'**Automated scan** unbanned: [{record[dbAccess.sid]}] '
                                       f'{record[dbAccess.discord_name]}')

    @client.tree.command(name='bot_commands', description=f'Show all commands available')
    async def bot_commands(interaction: discord.Interaction):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        response = ''
        command_list = await client.tree.fetch_commands()
        for command in command_list:
            response += f'**{command.name}** : *{command.description}*\n'
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='list_users', description=f'List all users in database')
    async def list_users(interaction: discord.Interaction):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        response = msgHandler.list_users(ldb)
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='read_notes',
                         description=f'Display all notes for user <sid>')
    @app_commands.describe(discord_id='@id')
    async def read_notes(interaction: discord.Interaction, discord_id: str):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        response = '* ' + msgHandler.show_notes(discord_id[2:-1], ldb).replace('|', '\n* ')
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='write_note',
                         description=f'write note about <sid>')
    @app_commands.describe(discord_id='@id',
                           note='Note to add to user data')
    async def write_note(interaction: discord.Interaction, discord_id: str, note: str):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        response = msgHandler.add_note(discord_id[2:-1], note, ldb)
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='show_user',
                         description=f'Display all fields for user <sid>')
    @app_commands.describe(discord_id='@id')
    async def show_user(interaction: discord.Interaction, discord_id: str):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        response = msgHandler.show_user(discord_id[2:-1], ldb)
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='add_user',
                         description=f'Add a new user <discord_id>')
    @app_commands.describe(discord_id='@id')
    async def add_user(interaction: discord.Interaction, discord_id: str):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        discord_name = await client.fetch_user(int(discord_id[2:-1]))
        response = msgHandler.add_user(discord_id, discord_name, ldb)
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='change_roll',
                         description=f'Set role <role_str> to user <sid>')
    @app_commands.describe(discord_id='@id', role='role name')
    async def change_roll(interaction: discord.Interaction, discord_id: str, role: str):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        response = msgHandler.add_role(discord_id[2:-1], role, ldb)
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='del_user',
                         description=f'Delete user <sid>')
    @app_commands.describe(discord_id='@id')
    async def del_user(interaction: discord.Interaction, discord_id: str):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        response = msgHandler.delete_user(discord_id[2:-1], ldb)
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='ban_user',
                         description=f'ban user @id <duration(days)> <reason(string)>')
    @app_commands.describe(discord_id='@id',
                           duration='Length of ban in days',
                           reason='Reason for ban (short description)')
    async def ban_user(interaction: discord.Interaction, discord_id: str, duration: int, reason: str):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        response = msgHandler.ban_user(discord_id[2:-1], duration, reason, ldb)
        # Write a message on the admin channel letting other admins know a user has been banned
        admin_channel = discord.utils.get(interaction.guild.channels, name=CH_ADMIN)
        await admin_channel.send(response)
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='unban_user',
                         description=f'unban user <sid>')
    @app_commands.describe(discord_id='@id')
    async def unban_user(interaction: discord.Interaction, discord_id: str):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        response = msgHandler.unban_user(discord_id[2:-1], interaction.user.name, ldb)
        # Write a user to the admin channel letting other admins know a user has been un-banned
        admin_channel = discord.utils.get(interaction.guild.channels, name=CH_ADMIN)
        await admin_channel.send(response)
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='generate_pass',
                         description=f'Generate a new password for user <sid>')
    @app_commands.describe(sid='The SID of the user')
    async def generate_pass(interaction: discord.Interaction, sid: int):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        user_id = dbAccess.get_element(sid, dbAccess.sid, dbAccess.discord_id, ldb)
        response = msgHandler.new_pass(user_id, ldb)
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='arb_read',
                         description=f'read value of field <field> of user <sid>')
    @app_commands.describe(sid='The SID of the user',
                           field='Field name to show')
    async def arb_read(interaction: discord.Interaction, sid: int, field: str):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        response = f'{field} : {msgHandler.read_field(sid, field, ldb)}'
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='arb_write',
                         description=f'write value <val> to field <field> of user <sid>')
    @app_commands.describe(sid='The SID of the user',
                           field='Field name to write to',
                           val='Value to write')
    async def arb_write(interaction: discord.Interaction, sid: int, field: str, val: str = ''):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        response = msgHandler.write_field(sid, field, val, ldb)
        await interaction.response.send_message(response, ephemeral=True)  # noqa

# The following commands are to be opened up to all Discord users who have access to your server
    @client.tree.command(name='show_password',
                         description=f'Display your Run8 server password in a message only you can see')
    async def show_password(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        discord_name = await client.fetch_user(int(user_id))
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        response = msgHandler.show_pass(user_id, discord_name, ldb)
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='refresh_pass',
                         description=f'Refresh your Run8 server password and display in a message only you can see')
    async def refresh_pass(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        response = msgHandler.new_pass(user_id, ldb)
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='server_info',
                         description=f'Show the Run 8 server address and port')
    async def server_info(interaction: discord.Interaction):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        response = f'Run 8 server address: *{R8SERVER_ADDR}*\nRun 8 server port: *{R8SERVER_PORT}*'
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    client.run(TOKEN)
