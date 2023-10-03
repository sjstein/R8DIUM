import botHandler
import dbAccess
import msgHandler
import threading
import time
from r8udbBotInclude import DB_FILENAME


def scan_ban(ldb):
    while True:
        time.sleep(60*10)   # Once every ten minutes
        for record in ldb:
            if record[dbAccess.banned] == 'True':
                if not msgHandler.check_ban_status(record[dbAccess.sid], ldb):
                    msgHandler.unban_user(record[dbAccess.sid], 'Automated check', ldb)
                    print(f'scan_ban just unbanned: {record[dbAccess.sid]}')


if __name__ == '__main__':
    userDb = dbAccess.load_db(DB_FILENAME)
    tid = threading.Thread(target=scan_ban, args=(userDb,))
    print(f'Firing off scan_ban; thread id {tid}')
    tid.start()
    botHandler.run_new_discord_bot(userDb)
