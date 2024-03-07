# R8DIUM Changelog

### 7-Mar-2024 [Gravitated]
### This update introduces the ability to kill / restart Run8 server instances ###

**Version Update** : "Gravitated"

**NOTE 1**: This update requires the addition of a new python library ("psutil") as reflected in the 
file **requirements.txt** : 

**NOTE 2**: This update requires modification of your bot configuration file. Check  **r8dium_example.cfg** for details.
In short, a new field has been added to each [server] block to point to the run8 executable location.

**NOTE 3**: This update requires adding a batch file in the same directory as your Run8 executable(s) - see below for
more details.

#### Two new bot commands have been added: ####

**/kill_server** _opt_:[server_name]

**/restart_server** _opt_:[server_name]

To faciliate dealing with the server instances, the server admin will have to utilize the -ServerConfigFile switch 
of Run8, as well as a ServerConfig.xml file. See the documentation that comes with Run8 - specifically:
* "Auto Server Startup.pdf"
* "ServerOnlyMode.pdf"

Along with modifying the ServerConfig.xml file to tailor for your needs, you will also need to install a batch file in
the Run8 executable directory. An example batch file is included with this distribution. See:

**startServer_example.bat**

For those admins who are only dealing with one server per bot, the [server_name] parameter for the new commands can be 
ignored. For those admins who manage more than one server instance from a single bot, the server_name specifies which 
server instance the command will affect. If left blank, the first server in your server list will be assumed.

### 06-Mar-2024 [flagellated]

** Version Update** : "flagellated"

This update fixes a vulnerability wherein a user could leave the discord server, still have access to the Run8 server,
and the discord admins would not have the ability to manipulate the user data database as it reports an "invalid 
discord id".

Two changes were implemented to handle this issue:

1 - When a user leaves the discord server, their password will be changed, and their (run8) account suspended. The only 
way to reactivate is to contact an admin.

2 - a new command "/show_user_by_sid" was added to allow viewing of users who have left the discord server. To find a
user's id (sid), you will have to list all users and find the corresponding id#.


### 20-Nov-2023 [Excommunicated]

**Version Update** : "Excommunicated"

This update brings in the ability to track user login dates and set their status to "Inactive" after a user-defined
timeout. As a side-effect, this change also adds the feature of populating the user database with login IP numbers. 
These functions require scraping through the Run8 log file(s).

**NOTE 1** : The underlying user database schema changes with this update - adding two new columns to the user record:
*last_login* (datestr) and *active* (True/False). A utility has been created to convert your existing user database to
the new schema; run the python script named "updateDb.py". After the utility is run - **you will need to manually copy
over the new database to the original filename** - a backup of your original database is automatically created named
"r8diumDb.BAK"

**NOTE 2** : Because it is so important - restating the need to update your user database by running `updateDb.py` 
**and copying the updated database (`r8diumDb-update.csv`) over your existing `r8diumDb.csv` file.**

**NOTE 3** : The configuration file has changed to add in new parameters / options
1. Under the [server1], [server2], etc. categories :
   - log_file [location and name of server Run8.log file]
2. Under the [discord] category
   - inactive_days_threshold [Number of days between logins required to elapse for a user to be considered inactive]
   - expire_scan_time [Number of **minutes** between each check for expired users]
   - UID_purge_timer [Time in seconds to regularly check and purge UIDs from HostSecurity file]

**Also addressed** :
1. Added a new bot function `/reactivate_user <username>` to allow staff members the ability to reinstate an expired user
2. Cleaned up the `/ban_user` and `/unban_user` functions to disallow banning or unbanning users already in those states
3. Added option to routinely remove UID entries from HostSecurity file(s) as a stop-gap way of eliminating the need
for users who have changing UIDs from having to frequently run `/refresh_pass`
------------------------------
### 11-Nov-2023 [Discombobulated]

**Version Update** : "Discombobulated"

This update brings the ability to track more than one Run8 server running on the host machine.

**NOTE 1** : The configuration file format has changed to accommodate multiple server instances. See the file
`r8dium_example.cfg` for details. In summary, there are now categories for each server with specific parameters for
each as follows:

[server1] (create a new category for each server - server1, server2, etc.)
- name [Human readable name of this particular server - eg "BNSF SoCal"]
- r8server_addr [host name / IP for use in /server_info command]
- r8server_port [host port for use in /server_info command]
- security_file [location and name of server HostSecurity.xml file]
----------------
### 10-Nov-2023 [Chelated]
- Changed `/ban_user` and `/unban_user` commands to report status changes in admin logs as well as note who initiated the change
- Added same reporting to automated unban scan function
----------------
### 08-Nov-2023 [Chelated]
- Added scope so bot had access to user IDs outside of current channel 
- Fixed `/list_users` command to handle messages which exceeded discord character limit by converting those messages to a file upload
----------------
### 1-Nov-2023 [Chelated]
**Version Update** : "Chelated"
Beginning of the Changelog
