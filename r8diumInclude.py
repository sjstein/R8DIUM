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
import configparser

SOFTWARE_VERSION = 'Gravitated'

CONFIG_FILE = 'r8dium.cfg'
STAT_URL = 'https://www.b2fengineering.com/r8dium/check-in'

config = configparser.ConfigParser()
if len(config.read(CONFIG_FILE)) == 0:
    print(f'Error in loading configuration file "{CONFIG_FILE}" - does it exist? Is it empty?')
    exit(-1)

try:
    # Local configuration options
    USER_DB = config['local']['db_name']
    LOG_FILE = config['local']['log_file']
    if config['local']['send_stats'] == 'True':
        SEND_STATS = True
    else:
        SEND_STATS = False
    STAT_TOKEN = config['local']['stat_token']

    if not SEND_STATS and (STAT_TOKEN != '' or STAT_TOKEN != '[insert STAT token]'):
        print('**WARNING**\nIt appears that you have entered a stat_token, but not opted in to statistics sharing!\n'
              'Please check your configuration file for errors. See the file STATS-OPT-IN for details.')
    if SEND_STATS and (STAT_TOKEN == '' or STAT_TOKEN == '[insert STAT token]'):
        print('**WARNING**\nYou have opted in to share statistics with the developers - thanks!\n'
              'However it appears you have yet to '
              'obtain and/or enter your secure token in the configuration file.\n'
              'Please see STATS-OPT-IN.md for details on how to proceed.')
        exit(-1)

    DB_FILENAME = USER_DB + '.csv'
    LOG_FILENAME = LOG_FILE + '.log'

    # Discord bot unique token
    TOKEN = config['discord']['bot_token']

    # Discord channels
    CH_ADMIN = config['discord']['ch_admin']
    CH_LOG = config['discord']['ch_log']

    BAN_SCAN_TIME = config['discord']['ban_scan_time']
    LOG_SCAN_TIME = config['discord']['log_scan_time']
    EXP_SCAN_TIME = config['discord']['expire_scan_time']
    INACT_DAYS = config['discord']['inactive_days_threshold']
    UID_PURGE_TIME = config['discord']['UID_purge_timer']

    R8SERVER_NAME = list()
    R8SERVER_PATH = list()
    SECURITY_FILE = list()
    R8SERVER_ADDR = list()
    R8SERVER_PORT = list()
    R8SERVER_LOG = list()
    for key, sub_dict in config.items():
        if key.startswith('server'):
            SECURITY_FILE.append(sub_dict['security_file'])
            R8SERVER_PATH.append(sub_dict['launch_path'])
            R8SERVER_ADDR.append(sub_dict['r8server_addr'])
            R8SERVER_PORT.append(sub_dict['r8server_port'])
            R8SERVER_NAME.append(sub_dict['name'])
            R8SERVER_LOG.append(sub_dict['log_file'])




except KeyError as e:
    print(f'\nr8dium ({__name__}.py): FATAL exception, unable to find [{e}] in configuration file')
    exit(-1)

except Exception as e:
    print(f'\nr8dium ({__name__}.py): FATAL exception type unknown - contact devs')
    exit(-1)
