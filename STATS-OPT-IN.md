In order to help me further improve R8DIUM, I ask that you allow your installation to send back some basic statistics.

Currently, this just consists of a unique (hashed) server ID and the number of users that your copy of R8DIUM manages.
No personal data (passwords, user IDs, etc.) are collected.

If you decide to help me further development of R8DIUM by opting-in and sharing this data, 
I will need to get you a unique token to authenticate access.
For now, I will simply issue these tokens on a case-by-case basis. 
In the future, if demand becomes high enough (a good thing!), this process will be automated. 

However, for the time being I ask that you **send an email to me** formatted as follows:

----
**Subject**: R8DIUM token request

Contents:
* name: _your name (optional)_
* server: _your server name (optional)_
* url: _your server url (optional)_
----

Send your request to: _s.joshua.stein+r8dium@gmail.com_

I will generate your token and send back to you as soon as I can. 
In the meantime, feel free to start using R8DIUM with the `send_stats` option set to **False** in the r8dium.cfg file.

Once you get the token back from me, please add it to your configuration file and also change
the `send_stats` option to **True** like this:

`send_stats = True
`

`stat_token = your_new_token_goes_here
`

Thank you so much for helping!
