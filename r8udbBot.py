import botHandler
import sheetHandler

if __name__ == '__main__':
    sheet_credential, user_sheet = sheetHandler.auth_sheet()
    botHandler.run_discord_bot(user_sheet)
