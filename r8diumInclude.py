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
import os
from pathlib import Path

SOFTWARE_VERSION = 'Halogenated'

CONFIG_FILE = os.environ.get('R8DIUM_CONFIG_FILE', 'r8dium.cfg')

config = configparser.ConfigParser()
if len(config.read(CONFIG_FILE)) == 0:
    print(f'Error in loading configuration file "{CONFIG_FILE}" - does it exist? Is it empty?')
    exit(-1)

try:
    # Local configuration options
    USER_DB = config['local']['db_name']
    LOG_FILE = config['local']['log_file']

    DB_FILENAME = USER_DB + '.csv'
    LOG_FILENAME = LOG_FILE + '.log'

    # Discord bot unique token
    token_file = os.environ.get('R8DIUM_BOT_TOKEN_FILE', '')
    file_token = Path(token_file).read_text(encoding='utf-8').strip() if token_file else ''
    TOKEN = os.environ.get('R8DIUM_BOT_TOKEN') or file_token or config['discord'].get('bot_token', '')
    if not TOKEN:
        raise KeyError('bot_token, R8DIUM_BOT_TOKEN, or R8DIUM_BOT_TOKEN_FILE')

    # Discord bot status
    BOT_STATUS = config['discord']['bot_status']

    # Discord channels
    CH_ADMIN = config['discord']['ch_admin']
    CH_LOG = config['discord']['ch_log']
    if CH_LOG.lower() == 'none':
        CH_LOG = 'none'

    BAN_SCAN_TIME = config['discord']['ban_scan_time']
    LOG_SCAN_TIME = config['discord']['log_scan_time']
    EXP_SCAN_TIME = config['discord']['expire_scan_time']
    INACT_DAYS = config['discord']['inactive_days_threshold']
    UID_PURGE_TIME = config['discord']['UID_purge_timer']
    RUN8_EVENT_LOG = os.environ.get('RUN8_EVENT_LOG', '')
    RUN8_EVENT_STATE_FILE = os.environ.get('RUN8_EVENT_STATE_FILE', '/state/run8-events.offset')

    R8SERVER_NAME = list()
    R8SERVER_PATH = list()
    SECURITY_FILE = list()
    R8SERVER_ADDR = list()
    R8SERVER_PORT = list()
    R8SERVER_LOG = list()
    R8SERVER_INDUSTRY_FNAME = list()
    R8SERVER_SECURITY_FNAME = list()
    R8SERVER_WORLD_FNAME = list()
    R8SERVER_TRAFFIC_FNAME = list()
    R8SERVER_HUMP_FNAME = list()
    R8SERVER_START_COMMAND = list()
    R8SERVER_STOP_COMMAND = list()
    R8SERVER_RESTART_COMMAND = list()
    for key, sub_dict in config.items():
        if key.startswith('server'):
            SECURITY_FILE.append(sub_dict['security_file'])
            R8SERVER_PATH.append(sub_dict['launch_path'])
            R8SERVER_ADDR.append(sub_dict['r8server_addr'])
            R8SERVER_PORT.append(sub_dict['r8server_port'])
            R8SERVER_NAME.append(sub_dict['name'])
            R8SERVER_LOG.append(sub_dict['log_file'])
            R8SERVER_INDUSTRY_FNAME.append(sub_dict['industry_file'])
            R8SERVER_SECURITY_FNAME.append(sub_dict['security_file'])
            R8SERVER_WORLD_FNAME.append(sub_dict['world_file'])
            R8SERVER_TRAFFIC_FNAME.append(sub_dict['traffic_file'])
            R8SERVER_HUMP_FNAME.append(sub_dict['hump_file'])
            R8SERVER_START_COMMAND.append(sub_dict.get('start_command', ''))
            R8SERVER_STOP_COMMAND.append(sub_dict.get('stop_command', ''))
            R8SERVER_RESTART_COMMAND.append(sub_dict.get('restart_command', ''))

except KeyError as e:
    print(f'\nr8dium ({__name__}.py): FATAL exception, unable to find [{e}] in configuration file')
    exit(-1)

except Exception as e:
    print(f'\nr8dium ({__name__}.py): FATAL exception type unknown - contact devs')
    exit(-1)
