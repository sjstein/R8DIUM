# R8DIUM

## The Run8 Database for Integrated User Management

## Installing / running using a virtual environment (highly recommended):
------------
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
### For further info on bot installation and usage, see [Getting_Started.md](Getting_Started.md)

---------

### Project files:

* r8dium.py : Entry point
* r8diumInclude.py : Helper routines / constants
* botHandler.py : Define bot commands and interactions
* msgHandler.py : Middleman between bot, database, and (local) file system
* dbAccess.py   : Database support
* r8dium_example.cfg : Sample configuration file
* r8diumDb-blank.csv : Blank database schema


### Auxillary files:

* logScraper.py  : simple hack to scrape through run8 logs looking for user data


### Deprecated files:

* archived/msgHandlerGoogle.py  : message handler for working with google sheets
* archived/sheetHandler.py  : database support when using google sheet as database



