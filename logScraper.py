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

# Quick code to scrape through log file for usernames, UID and IP# for importing into database
infile = 'run8.log'
outfile = 'userlist.csv'
line_list = []
user_dict = dict()

# Read log file and create list of lines of interest
fp = open(infile)
while True:
    line = fp.readline()
    if 'Name:' and 'PW:' in line:
        line_list.append(line)
    if line == '':
        break
fp.close()

# Parse line for name, uid, and IP#
for member in line_list:
    name = member.split('Name:')[1].split(' PW:')[0][:-1]
    uid = member.split('UID:')[1].split(' IP:')[0][:-1]
    ip = member.split('IP:[NetConnection to [::ffff:')[1].split(']:')[0]
    user_dict[name] = [uid, ip]

# Write csv file
wp = open('userlist.csv', 'w')
wp.write('Name, UID, IP\n')
for name in user_dict:
    print(f'Name: {name} | UID: {user_dict[name][0]} | IP: {user_dict[name][1]}')
    wp.write(f'{name},{user_dict[name][0]},{user_dict[name][1]}\n')

wp.close()
    
