'''
This utility will update the current r8dium database (in csv) to the most recent schema
- Currently this involves adding a new field (column) to store the last login date of each user
'''


import shutil

input_name = 'r8diumDb'
output_name = input_name + '-update'

ifp = open(input_name + '.csv', 'r')
ofp = open(output_name + '.csv', 'w')

shutil.copy(input_name + '.csv', input_name + '.BAK')   # create a backup of the original db

for line in ifp.readlines():
    if line.find('discord_name,discord_id') > 0:
        if line.find(',last_login') < 0:     # Header hasn't been modified
            ins_pt = line.find(',ip')
            new_header = line[:ins_pt] + ',last_login,active' + line[ins_pt:]
            ofp.write(new_header)
        else:
            print('found first line has already been updated')
            ofp.write(line)
    else:
        if line.count(',') == 12:
            # This is an old format, so update by adding two new fields (last_login, active?)
            cpos = 0
            cfnd = 0
            for char in line:
                if char == ',':
                    cfnd += 1
                cpos += 1
                if cfnd == 8:
                    cloc = cpos
            # insert two new fields - blank for last_login, and True for active
            new_line = line[:cloc] + ',True,' + line[cloc:]
            ofp.write(new_line)

ofp.close()
ifp.close()

print(f'Database updated and stored as {output_name}.csv')
print(f'It is suggested to compare the existing database to the newly created one before copying over.')
print(f'A backup of the original database has been saved as {input_name}.BAK')
