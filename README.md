# R8DIUM

## Killerp51's R8DIUM Fork
This fork is based off of the R8DIUM-Gravitated release. All credit goes to sjstein and Garrisonsan for the release. I have made a few fixes and added some features. sjtein/Garrisonsan, if you see this, feel free to incorporate these changes into your work

* Fixed - audioop file missing
* Added - Discord bot activity status (incorporated into config.cfg)
* Added - Discord role assignment upon member joining server (optional)

## The Run8 Database for Integrated User Management

**R8DIUM is a Discord "bot" which enables user management for a Run8 server**. It allows admin/yardmasters the ability to
add and remove users as well as ban and unban them. Furthermore, R8DIUM allows the users themselves to view their
current password, and request a new one be generated.

R8DIUM keeps a local database of user records for its own use, and updates the Run8 HostSecurity.xml to reflect changes
to the Run8 server.

### BLUF:

* R8DIUM was designed to make the job of _Run8 server_ USER administration easier by automating certain server 
maintenance tasks.
* Since R8DIUM is designed to run on the same machine or network which the _Run8 server_ is hosted on, all data is stored 
locally - **no data is exported off the host machine**.
* R8DIUM utilizes individual passwords for all _Run8 server_ members. 
* Utilizing **Discord server** roles, the _Run8 server_ owner can delegate certain personnel the ability to add, remove,
ban and unban users by using R8DIUM commands. 
* R8DIUM handles tracking of _Run8 server_ USER passwords and their active/banned status. 
* R8DIUM will automatically unban users after a specified duration has elapsed. 
* R8DIUM synchronizes its own user data with the _Run8 server_ security file - no need for manual edits.
* R8DIUM allows storing and reading of notes for each user it tracks.
* R*DIUM has limited commands to interact with users - allowing them to view their password, request a new password, 
and view _Run8 server_ info (address and port).
* All R*DIUM responses are sent back to the requester as private text - no one else will see them.
* R*DIUM has the ability to log all commands it receives - to a file and/or a specific Discord channel.


---------------

## R8DIUM is a Discord bot that runs on your local machine


Unlike the typical Discord bot which is installed via a bot invite, R8DIUM requires the Run8 server admin to run the bot
from their own machine. This keeps the user information local to that filesystem - avoiding hosting sensitive
information on a third party machine.

Of course, the downside to that is the Run8 server administrator will have to go through the process on the
Discord developer portal to register the bot and give it the proper server permissions to function properly.

The process of registering on the Discover developer portal and "programming" their own bot is beyond the scope of this
document. There are a lot of guides and youTube videos available which describe the process. That being said, there are
a couple of things to make note:

1. Once your bot is registered, you will have access to its unique Token. This value will be put in the R8DIUM configuration
file (discussed later).

2. When setting up your bot authorizations, make sure that the following are toggled **on**:
   * PRESENCE INTENT
   * SERVER MEMBERS INTENT
   * MESSAGE CONTENT INTENT

----------------

## Installing / running using a virtual environment (highly recommended):

### To install:
From the R8DIUM installation directory:
* Set up a new virtual environment per your local installation / OS within the directory you installed the R8DIUM software
* Activate your new environment
* update pip : `python -m pip install --upgrade pip`
* install packages : `pip install -r requirements.txt`

### To run:
From the R8DIUM installation directory:
* Activate virtual environment
* type: `python r8dium.py`
------------
## Installing / running without using a virtual environment (not recommended):

From the R8DIUM installation directory:
* update pip : `python -m pip install --upgrade pip`
* install packages : `pip install -r requirements.txt`

### To run:
From the R8DIUM installation directory:
* type: `python r8dium.py`
------------
### For further info on server/bot configuration and usage, see [Getting_Started.md](Getting_Started.md)

---------

### Project files:

* r8dium.py : Entry point
* r8diumInclude.py : Helper routines / constants
* botHandler.py : Define bot commands and interactions
* msgHandler.py : Middleman between bot, database, and (local) file system
* dbAccess.py   : Database support
* r8dium_example.cfg : Sample configuration file
~~* r8diumDb-blank.csv : Blank database schema~~


### Auxillary files:

* logScraper.py  : simple hack to scrape through run8 logs looking for user data


### Deprecated files:

* archived/msgHandlerGoogle.py  : message handler for working with google sheets
* archived/sheetHandler.py  : database support when using google sheet as database



