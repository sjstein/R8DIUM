import configparser

CONFIG_FILE = 'r8udbBot.cfg'

config = configparser.ConfigParser()
config.read(CONFIG_FILE)

# Local configuration options
USER_DB = config['local']['db_name']
DB_FILENAME = USER_DB + '.csv'

# Discord bot unique token
TOKEN = config['discord']['bot_token']

# Discord user levels (roles)
USR_LVL0 = config['discord']['usr_lvl0']
USR_LVL1 = config['discord']['usr_lvl1']
USR_LVL2 = config['discord']['usr_lvl2']
USR_LVL3 = config['discord']['usr_lvl3']

# Discord channels
CH_ADMIN = config['discord']['ch_0']
CH_USER = config['discord']['ch_1']

# Run 8 security configuration xml filename
SECURITY_FILE = config['run8']['security_file']

# Google sheet unique ID
# SPREADSHEET_ID = config['google']['sheet_id']
