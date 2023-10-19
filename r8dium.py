#########################
# R8DIUM : Run8 Database for Integrated User Management
#
# Copyright (C) 2023, S. Joshua Stein, <s.joshua.stein@gmail.com>
#
# This file is part of the R8DIUM software tool suite.
#
# R8DIUM is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# R8DIUM is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with R8DIUM.
# If not, see <https://www.gnu.org/licenses/>.
##########################
import botHandler
import dbAccess
import time
from r8diumInclude import DB_FILENAME, SEND_STATS, SOFTWARE_VERSION

if __name__ == '__main__':
    userDb = dbAccess.load_db(DB_FILENAME)
    if not SEND_STATS:
        print("\nIt appears R8DIUM is running without reporting anonymous statistics.")
        print("Please consider enabling this feature as it will help improve this software.")
        print("See STATS-OPT-IN.md for details on how to opt-in for this.")
        print("Thanks in advance!\n\n")
        time.sleep(1)
    print(f'R8DIUM [{SOFTWARE_VERSION}] is starting.')
    botHandler.run_discord_bot(userDb)
