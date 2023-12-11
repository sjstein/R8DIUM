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
import datetime
import discord
from discord.ext import commands, tasks  # noqa
import asyncio  # noqa
import dbAccess
import msgHandler
import pathlib
import r8diumInclude
from r8diumInclude import (TOKEN, BAN_SCAN_TIME, SOFTWARE_VERSION, CH_ADMIN, CH_LOG, R8SERVER_ADDR, R8SERVER_PORT,
                           R8SERVER_NAME, R8SERVER_LOG, DB_FILENAME, LOG_SCAN_TIME, INACT_DAYS, EXP_SCAN_TIME,
                           UID_PURGE_TIME)

discord_char_limit = 1900
hsf_mtime = {}
tmp_filename = 'user_list.txt'  # File to hold long user list for sending to Discord (avoiding character limit)


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
        print(f'Discord bot [{client.user}] is starting')
        # Populate the dict with current host file modification timestamps
        for filename in r8diumInclude.SECURITY_FILE:
            hsf_mtime[filename] = pathlib.Path(filename).stat().st_mtime

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
        print(f'Starting log-in periodic checks')
        msgHandler.write_log_file(f'Starting log-in periodic checks')
        scan_logins.start(ldb)
        if int(INACT_DAYS) > 0:  # Not all server admins want to auto-expire users
            print(f'Starting expired user checks')
            msgHandler.write_log_file(f'Starting expired user checks')
            expire_users.start(ldb)
        if int(UID_PURGE_TIME) > 0:  # Not all server admins want to purge UIDs from HostSecurity file
            print(f'Starting UID purge daemon')
            msgHandler.write_log_file(f'Starting UID purge daemon')
            clean_uids.start(ldb)
        dbAccess.send_statistics(ldb)

    @tasks.loop(seconds=int(LOG_SCAN_TIME))
    async def scan_logins(ldb):
        for log_file in R8SERVER_LOG:
            write_db = False
            fp = open(log_file, 'r')
            for line in fp.readlines():
                if 'Name' in line and 'PW:' in line:  # This is a log in status message
                    lft_line = line.split(',')[0]  # Chunk up the line into useful parts
                    rt_line = line.split(',', 1)[1]  # Very fragile due to the dependency on the log file format
                    print(f'Left : {lft_line}')
                    print(f'Right: {rt_line}')
                    raw_date = lft_line.split(' ')[
                        0]  # This date shows up as YYYY-MM-DD which is different than how we store
                    date = datetime.datetime.strptime(raw_date, '%Y-%m-%d').strftime('%#m/%#d/%y')
                    time = lft_line.split(' ')[1]
                    name = rt_line.split('Name:')[1].split('  PW:')[0]
                    print(f'{name}')
                    pw = rt_line.split('PW:')[1].split('  UID:')[0]
                    print(f'{pw}')
                    uid = rt_line.split('UID:')[1].split('  IP:')[0]
                    print(f'{uid}')
                    ip = rt_line.split('::ffff:')[1].split(']:')[0]
                    print(f'{ip}')
                    #          print(f'{date} : {time} : {name} : {pw} : {uid} : {ip}')
                    last_login = dbAccess.get_element(pw, dbAccess.password, dbAccess.last_login, ldb)
                    if last_login == '':
                        last_login = '1/1/00'
                    # What to do if the password isn't found? Possible if the user changed pass in-between scans
                    # For now, just ignoring. Should eventually sync up
                    if last_login != -1:
                        log_date = datetime.datetime.strptime(date, '%m/%d/%y')
                        last_date = datetime.datetime.strptime(last_login, '%m/%d/%y')
                        if (log_date - last_date).days > 0:
                            dbAccess.set_element(pw, dbAccess.password, dbAccess.last_login, date, ldb)
                            dbAccess.set_element(pw, dbAccess.password, dbAccess.ip, ip, ldb)
                            dbAccess.set_element(pw, dbAccess.password, dbAccess.run8_name, name, ldb)
                            msg = f'Updating login info for ' \
                                  f'{dbAccess.get_element(pw, dbAccess.password, dbAccess.discord_name, ldb)} from ' \
                                  f'file {log_file}'
                            msgHandler.write_log_file(msg)
                            write_db = True
            if write_db:
                dbAccess.save_db(DB_FILENAME, ldb)
            fp.close()
        return

    @tasks.loop(minutes=int(EXP_SCAN_TIME))
    async def expire_users(ldb):
        today = datetime.datetime.today()
        today_str = datetime.datetime.strftime(today, '%m/%d/%y')
        for line in ldb:
            discord_id = line['discord_id']
            last_active = dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.last_login, ldb)
            if last_active == '':   # Handling a blank last_active by comparing to today's date
                last_active = today_str
            diff = (today - datetime.datetime.strptime(last_active, '%m/%d/%y')).days
            if diff > int(INACT_DAYS) and \
                    dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.active, ldb) != 'False':
                channel_id = discord.utils.get(client.get_all_channels(), name=CH_LOG).id
                channel = client.get_channel(channel_id)
                channel_id = discord.utils.get(client.get_all_channels(), name=CH_ADMIN).id
                admin_channel = client.get_channel(channel_id)
                discord_name = dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.discord_name, ldb)
                msg = f'Automated scan set user {discord_name} to INACTIVE; last login : {last_active}'
                msgHandler.write_log_file(msg)
                await channel.send(msg)
                await admin_channel.send(msg)
                msgHandler.expire_user(discord_id, today_str, ldb)
        return

    @tasks.loop(seconds=int(UID_PURGE_TIME))
    async def clean_uids(local_db):
        for filename in r8diumInclude.SECURITY_FILE:
            current_mtime = pathlib.Path.stat(filename).st_mtime
            if current_mtime != hsf_mtime[filename]:
                print(f'clean_uid daemon: purging HostSecurity file(s) of UIDs')
                msgHandler.write_log_file(f'clean_uid daemon: purging HostSecurity file(s) of UIDs')
                dbAccess.write_security_file(local_db, purge_uids=True)
                for key in hsf_mtime:
                    hsf_mtime[key] = pathlib.Path.stat(filename).st_mtime
                break

    @tasks.loop(seconds=int(BAN_SCAN_TIME))
    async def scan_banned_users(local_db):
        if type(local_db) is not list:  # local_db must be empty - showing as NoneType
            return
        for record in local_db:
            if record[dbAccess.banned] == 'True':
                if not msgHandler.check_ban_status(record[dbAccess.sid], local_db):
                    channel_id = discord.utils.get(client.get_all_channels(), name=CH_LOG).id
                    channel = client.get_channel(channel_id)
                    channel_id = discord.utils.get(client.get_all_channels(), name=CH_ADMIN).id
                    admin_channel = client.get_channel(channel_id)
                    msg = f'Automated scan **unbanned** {record[dbAccess.discord_name]} due to ' \
                          f'time served ({record[dbAccess.ban_duration]} days)'
                    msgHandler.write_log_file(msg)
                    msgHandler.unban_user(record[dbAccess.discord_id], 'Automated check', local_db)
                    await channel.send(msg)
                    await admin_channel.send(msg)

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
        if len(response) > discord_char_limit:
            tf = open(tmp_filename, 'w')
            tf.write(response)
            tf.close()
            await interaction.response.send_message(file=discord.File(tmp_filename), ephemeral=True)  # noqa
        else:
            await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='read_notes',
                         description=f'Display all notes for user @id')
    @app_commands.describe(member='@id')
    async def read_notes(interaction: discord.Interaction, member: discord.Member):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        response = '* ' + msgHandler.show_notes(str(member.id), ldb).replace('|', '\n* ')
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='write_note',
                         description=f'write note about @id')
    @app_commands.describe(member='@id',
                           note='Note to add to user data')
    async def write_note(interaction: discord.Interaction, member: discord.Member, note: str):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        response = msgHandler.add_note(str(member.id), note, ldb)
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='show_user',
                         description=f'Display all fields for user @id')
    @app_commands.describe(member='@id')
    async def show_user(interaction: discord.Interaction, member: discord.Member):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        response = msgHandler.show_user(str(member.id), ldb)
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='add_user',
                         description=f'Add a new user <discord_id>')
    @app_commands.describe(member='@id')
    async def add_user(interaction: discord.Interaction, member: discord.Member):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        discord_name = await client.fetch_user(member.id)
        response = msgHandler.add_user(str(member.id), discord_name, ldb)
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='change_role',
                         description=f'Set role <role_str> to user @id')
    @app_commands.describe(member='@id', role='role name')
    async def change_role(interaction: discord.Interaction, member: discord.Member, role: str):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        response = msgHandler.add_role(str(member.id), role, ldb)
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='del_user',
                         description=f'Delete user @id')
    @app_commands.describe(member='@id')
    async def del_user(interaction: discord.Interaction, member: discord.Member):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        response = msgHandler.delete_user(str(member.id), ldb)
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='ban_user',
                         description=f'ban user @id <duration(days)> <reason(string)>')
    @app_commands.describe(member='@id',
                           duration='Length of ban in days',
                           reason='Reason for ban (short description)')
    async def ban_user(interaction: discord.Interaction, member: discord.Member, duration: int, reason: str):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        if dbAccess.get_element(str(member.id), dbAccess.discord_id, dbAccess.banned, ldb) != 'True':
            response = msgHandler.ban_user(str(member.id), interaction.user.name, duration, reason, ldb)
            # Write a message on the admin channel letting other admins know a user has been banned
            admin_channel = discord.utils.get(interaction.guild.channels, name=CH_ADMIN)
            await admin_channel.send(response)
        else:
            response = f'*{member.name}* **is already banned** - ignoring request'
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='unban_user',
                         description=f'unban user @id')
    @app_commands.describe(member='@id')
    async def unban_user(interaction: discord.Interaction, member: discord.Member):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        if dbAccess.get_element(str(member.id), dbAccess.discord_id, dbAccess.banned, ldb) != 'False':
            response = msgHandler.unban_user(str(member.id), interaction.user.name, ldb)
            # Write a message to the admin channel letting other admins know a user has been un-banned
            admin_channel = discord.utils.get(interaction.guild.channels, name=CH_ADMIN)
            await admin_channel.send(response)
        else:
            response = f'*{member.name}* is **not currently banned** - ignoring request'
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='reactivate_user',
                         description=f'reactivate user @id')
    @app_commands.describe(member='@id')
    async def reactivate_user(interaction: discord.Interaction, member: discord.Member):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        if dbAccess.get_element(str(member.id), dbAccess.discord_id, dbAccess.active, ldb) != 'True':
            response = msgHandler.activate_user(str(member.id), interaction.user.name, ldb)
            # Write a message to the admin channel letting other admins know a user has been un-banned
            admin_channel = discord.utils.get(interaction.guild.channels, name=CH_ADMIN)
            await admin_channel.send(response)
        else:
            response = f'*{member.name}* is **already active** - ignoring request'
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='generate_pass',
                         description=f'Generate a new password for user @id')
    @app_commands.describe(member='@id')
    async def generate_pass(interaction: discord.Interaction, member: discord.Member):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        response = msgHandler.new_pass(str(member.id), ldb)
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='arb_read',
                         description=f'read value of field <field> of user @id')
    @app_commands.describe(member='@id',
                           field='Field name to show')
    async def arb_read(interaction: discord.Interaction, member: discord.Member, field: str):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        response = f'{field} : {msgHandler.read_field(str(member.id), field, ldb)}'
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    @client.tree.command(name='arb_write',
                         description=f'write value <val> to field <field> of user @id')
    @app_commands.describe(member='@id',
                           field='Field name to write to',
                           val='Value to write')
    async def arb_write(interaction: discord.Interaction, member: discord.Member, field: str, val: str = ''):
        if CH_LOG != 'none':
            log_channel = discord.utils.get(interaction.guild.channels, name=CH_LOG)  # return channel id from name
            await log_channel.send(log_message(interaction))
        response = msgHandler.write_field(str(member.id), field, val, ldb)
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
        i = 0
        response = ''
        for server in R8SERVER_NAME:
            if i > 0:
                response += '----------------\n'
            response += (f'Server info for : **{server}** \n'
                         f'* address: **{R8SERVER_ADDR[i]}**\n'
                         f'* port:    **{R8SERVER_PORT[i]}**\n')
            i += 1
        await interaction.response.send_message(response, ephemeral=True)  # noqa

    client.run(TOKEN)
