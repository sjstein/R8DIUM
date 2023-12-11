# R8DIUM Changelog

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