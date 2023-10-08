import botHandler
import dbAccess
from r8udbBotInclude import DB_FILENAME


if __name__ == '__main__':
    userDb = dbAccess.load_db(DB_FILENAME)
    botHandler.run_discord_bot(userDb)
