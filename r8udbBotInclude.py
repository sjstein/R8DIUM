import configparser

CONFIG_FILE = 'r8udbBot.cfg'

config = configparser.ConfigParser()
config.read(CONFIG_FILE)

# Discord bot unique token
TOKEN = config['discord']['bot_token']

# Discord bot command designators
BOT_CMD = config['discord']['bot_cmd']
DM_CMD = config['discord']['bot_dm']

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
SPREADSHEET_ID = config['google']['sheet_id']
