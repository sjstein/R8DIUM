import configparser

SOFTWARE_VERSION = 'Articulated'
CONFIG_FILE = 'r8dium.cfg'

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

    DB_FILENAME = USER_DB + '.csv'
    LOG_FILENAME = LOG_FILE + '.log'

    # Discord bot unique token
    TOKEN = config['discord']['bot_token']

    # Discord user levels (roles)
    USR_LVL0 = config['discord']['usr_lvl0']
    USR_LVL1 = config['discord']['usr_lvl1']
    USR_LVL2 = config['discord']['usr_lvl2']
    USR_LVL3 = config['discord']['usr_lvl3']

    BOT_ROLES = [USR_LVL0, USR_LVL1, USR_LVL2, USR_LVL3]

    # Discord channels
    CH_ADMIN = config['discord']['ch_0']
    CH_USER = config['discord']['ch_1']
    CH_LOG = config['discord']['ch_log']
    # Restrict interaction based on channels?
    if config['discord']['ch_permissions'] == 'False':
        CH_RQD = False
    else:
        CH_RQD = True

    BAN_SCAN_TIME = config['discord']['ban_scan_time']

    # Run 8 security configuration xml filename
    SECURITY_FILE = config['run8']['security_file']

except KeyError as e:
    print(f'\nr8dium ({__name__}.py): FATAL exception, unable to find [{e}] in configuration file')
    exit(-1)

except Exception as e:
    print(f'\nr8dium ({__name__}.py: FATAL exception type unknown - contact devs')
    exit(-1)

