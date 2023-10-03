# r8udbBot
A discord bot to manage individual run8 users

Note: Need to add python env info to make this a reasonable package. Put on the "to-do" list. 
I **believe** the only unusual library needed is 'discord.py', but it will become obvious if others are needed to be installed

Project files:
r8udbBot.py : Entry point
r8udbBotInclude.py : Helper routines / constants
botHandler.py : Define bot commands and interactions
msgHandler.py : Middleman between bot, database, and (local) file system
dbAccess.py   : Database support
r8udbBot-example.cfg : Sample configuration file

Auxillary files:
logScraper.py  : simple hack to scrape through run8 logs looking for user data

Deprecated files:
archived/msgHandlerGoogle.py  : message handler for working with google sheets
archived/sheetHandler.py  : database support when using google sheet as database

