# Quick code to scrape through log file for usernames, UID and IP# for importing into spreadsheet

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
    
