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
import csv
import hashlib
import requests
import uuid

import xmltodict
from r8diumInclude import SECURITY_FILE, DB_FILENAME, SEND_STATS, SOFTWARE_VERSION

STAT_URL = ''
# Don't bother trying to send stats until we get a decent endpoint
if STAT_URL == '':
    SEND_STATS = False

# Below define the tags which Run8 uses inside the security XML
XML_ROOT_NAME = 'HostSecurityData'
XML_BANNED_CATEGORY_NAME = 'Banned_Users'
XML_BANNED_NAME = 'BannedUser'
XML_UNIQUE_CATEGORY_NAME = 'Unique_Logins'
XML_UNIQUE_NAME = 'UniqueLogin'
XML_NAME = 'Name'
XML_UID = 'UID'
XML_IP = 'IP'
XML_PASSWORD = 'Password'

# Field names
sid = 'sid'  # int (unique)
discord_name = 'discord_name'  # str
discord_id = 'discord_id'  # int
run8_name = 'run8_name'  # str
uid = 'uid'  # str
role = 'role'  # str
password = 'password'  # str
join_date = 'join_date'  # str
ip = 'ip'  # str
banned = 'banned'  # bool
ban_date = 'ban_date'  # str
ban_duration = 'ban_duration'  # str
notes = 'notes'  # str[]

db_field_list = [sid,
                 discord_name,
                 discord_id,
                 run8_name,
                 uid,
                 role,
                 password,
                 join_date,
                 ip,
                 banned,
                 ban_date,
                 ban_duration,
                 notes]


def load_db(filename: str) -> list:
    ldb = list()
    try:
        with open(filename, newline='') as csvfile:
            input_file = csv.DictReader(csvfile)
            for row in input_file:
                ldb.append(row)
        return ldb

    except FileNotFoundError as e:
        print(f'\nr8dium: Databse file {filename} not found, creating a new one')
        with open(filename, 'w', newline='') as csvfile:
            csvwriter = csv.DictWriter(csvfile, fieldnames=db_field_list)
            csvwriter.writeheader()
        return load_db(filename)

    except Exception as e:
        print(f'\nr8dium ({__name__}.py: FATAL exception in load_db, type unknown - contact devs')
        exit(-1)


def save_db(filename: str, ldb: list) -> int:
    try:
        with open(filename, 'w', newline='') as csvfile:
            csvwriter = csv.DictWriter(csvfile, fieldnames=db_field_list)
            csvwriter.writeheader()
            for row in ldb:
                csvwriter.writerow(row)
        return len(ldb)

    except Exception as e:
        print(f'\nr8dium ({__name__}.py: FATAL exception in save_db, type unknown - contact devs')
        exit(-1)


def send_statistics(ldb: list):
    if SEND_STATS:
        server_mac_addr = ''.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(5, -1, -1)])
        server_id = hashlib.md5((server_mac_addr + SECURITY_FILE).encode()).hexdigest()
        put_dict = {'server_id': server_id, 'bot_version': SOFTWARE_VERSION, 'number_of_users': len(ldb)-1}
        return_val = requests.post(STAT_URL, put_dict)
        return return_val
    return


def write_security_file(ldb: list):
    # First we merge in the Run8 XML security file to capture any changes before overwriting
    merge_security_file(ldb)

    xml_dict = \
        {XML_ROOT_NAME: {XML_BANNED_CATEGORY_NAME: {XML_BANNED_NAME: []},
                         XML_UNIQUE_CATEGORY_NAME: {XML_UNIQUE_NAME: []}}}
    ban_list = xml_dict[XML_ROOT_NAME][XML_BANNED_CATEGORY_NAME][XML_BANNED_NAME]
    usr_list = xml_dict[XML_ROOT_NAME][XML_UNIQUE_CATEGORY_NAME][XML_UNIQUE_NAME]
    for record in ldb:
        if record[banned] == 'True':
            ban_list.append({XML_NAME: record[run8_name],
                             XML_UID: record[uid],
                             XML_IP: record[ip]})
        elif record[banned] == 'False' and record[password] != '':  # Don't save users without pw
            usr_list.append({XML_NAME: record[run8_name],
                             XML_UID: record[uid],
                             XML_PASSWORD: record[password]})
    xml_out = xmltodict.unparse(xml_dict, pretty=True)

    try:
        wp = open(SECURITY_FILE, 'w')
        wp.write(xml_out)
        wp.close()
        return 'file written'

    except Exception as e:
        print(f'\nr8dium ({__name__}.py: FATAL exception in write_security_file, type unknown - contact devs')
        exit(-1)


def merge_security_file(ldb: list):
    try:
        # Read current HostSecurity file and update UID fields based on password (gross)
        fp = open(SECURITY_FILE, 'r')
        xml_in = xmltodict.parse(fp.read(), process_namespaces=True)
        fp.close()

    except FileNotFoundError as e:
        print(f'\nr8dium ({__name__}.py): FATAL exception -> {e}')
        exit(-1)

    except Exception as e:
        print(f'\nr8dium ({__name__}.py: FATAL exception in merge_security_file, type unknown - contact devs')
        exit(-1)

    update_flag = False
    retstr = '`Merge results:\n-------------\n'

    if type(xml_in[XML_ROOT_NAME]) is not dict:
        # No entries in XML, just return
        return f'File merge error : No category names found'

    if type(xml_in[XML_ROOT_NAME][XML_UNIQUE_CATEGORY_NAME]) is not dict:
        # No user entries in XML, just return
        return f'File merge error : No names found'

    if type(xml_in[XML_ROOT_NAME][XML_UNIQUE_CATEGORY_NAME][XML_UNIQUE_NAME]) is dict:
        # Edge case to take of a single entry for XML-UNIQUE_NAME, just return and allow complete rewrite
        return f'File merge error : only one {XML_UNIQUE_NAME} entry found'

    for record in range(0, len(xml_in[XML_ROOT_NAME][XML_UNIQUE_CATEGORY_NAME][XML_UNIQUE_NAME])):
        retstr += f'{record : 03d}: '
        new_sid = get_element(xml_in[XML_ROOT_NAME][XML_UNIQUE_CATEGORY_NAME][XML_UNIQUE_NAME][record][XML_PASSWORD],
                              password, sid, ldb)
        if new_sid != -1:  # Found xml password in database
            current_uid = get_element(new_sid, sid, uid, ldb)
            # When run8 devs finally decide to capture the name, uncomment below
            # new_r8name = ''
            new_uid = ''
            if current_uid == '' or current_uid.lower() == 'none':  # No UID in database, so populate with XML version
                try:
                    new_uid = xml_in[XML_ROOT_NAME][XML_UNIQUE_CATEGORY_NAME][XML_UNIQUE_NAME][record][XML_UID]
                    # When run8 devs finally decide to capture the name, uncomment below
                    # new_r8name = xml_in[XML_ROOT_NAME][XML_UNIQUE_CATEGORY_NAME][XML_UNIQUE_NAME][record][XML_NAME]
                    update_flag = True
                    # When run8 devs finally decide to capture the name, uncomment below and remove following line
                    # retstr += f'added UID[{new_uid}] and R8_name [{new_r8name}] ' \
                    #           f'to SID[{new_sid}]  ({get_element(new_sid, sid, discord_name, ldb)})\n'
                    retstr += f'added UID[{new_uid}] ' \
                              f'to SID[{new_sid}]  ({get_element(new_sid, sid, discord_name, ldb)})\n'

                except KeyError:
                    retstr += f'Found password but no UID (in XML) for ' \
                              f'SID[{new_sid}]\n'
            else:   # UID found in XML
                try:
                    new_uid = xml_in[XML_ROOT_NAME][XML_UNIQUE_CATEGORY_NAME][XML_UNIQUE_NAME][record][XML_UID]
                    # When run8 devs finally decide to capture the name, uncomment below
                    # new_r8name = xml_in[XML_ROOT_NAME][XML_UNIQUE_CATEGORY_NAME][XML_UNIQUE_NAME][record][XML_NAME]
                    if new_uid != current_uid:
                        # db and xml do not match, what to do? Just notify user for now
                        # Maybe we should start keeping a list of these UIDs? (ala Notes)
                        retstr += f'Existing UID mismatch for SID[{new_sid}]:\n'
                        retstr += f' database file UID: {current_uid}\n'
                        retstr += f' host_security UID: {new_uid}\n'
                        retstr += (f'Database file NOT updated for this record\n'
                                   f'-----------------------------------------')
                    else:
                        retstr += f'Existing UID valid for SID[{new_sid}]\n'
                except KeyError:
                    retstr += f'Found password but no UID (in XML) for SID {new_sid}'
            if update_flag:
                # When run8 devs finally decide to capture the name, uncomment below
                # set_element(new_sid, sid, run8_name, new_r8name, ldb)  # Updating this for no real reason atm
                set_element(new_sid, sid, uid, new_uid, ldb)
                save_db(DB_FILENAME, ldb)
        else:
            retstr += f'Password '
            retstr += f'[{xml_in[XML_ROOT_NAME][XML_UNIQUE_CATEGORY_NAME][XML_UNIQUE_NAME][record][XML_PASSWORD]}]'
            retstr += ' not found\n'
    return retstr


def get_index(key, search_col: str, ldb: list):
    """
    Return index of record keyed off of <search_string> contained in column <search_col>
    returns (-1) if string not found or invalid column name is specified.
    NOTE: Will return first instance if there are duplicates
    """
    index = 0
    try:
        for line in ldb:
            if line[str(search_col)] == str(key):
                return index
            index += 1
        return -1

    except Exception as e:
        print(f'{get_element.__name__} : {e.__class__.__name__} ({e})')
        return -1


def get_element(key, search_col: str, return_col: str, ldb: list):
    """
    Return value in return_col column keyed off of <search_string> contained in column <search_col>
    returns (-1) if string not found or invalid column name is specified.
    NOTE: Will return first instance if there are duplicates
    """
    try:
        for line in ldb:
            if line[str(search_col)] == str(key):
                return line[str(return_col)]
        return -1

    except Exception as e:
        print(f'{get_element.__name__} : {e.__class__.__name__} ({e})')
        return -1


def set_element(key, search_col: str, set_col: str, set_val, ldb: list):
    """
    Set the value <set_val> to column <set_col> of the row found with <search_col> == <key>
    returns sid of record which has been modified
    returns (-1) if no record found
    NOTE: Will hit on first match if multiples exist
    """
    if set_val is None:
        set_val = ''
    try:
        for line in ldb:
            if line[str(search_col)] == str(key):
                line[str(set_col)] = str(set_val)
                return line[sid]
        return -1

    except Exception as e:
        print(f'{set_element.__name__} : {e.__class__.__name__} ({e})')
        return -1


def add_new_user(name: str, user_name, ldb: list):
    new_sid = next_avail_sid(ldb)
    record = {}
    for field in db_field_list:
        record[field] = ''
    record[sid] = str(new_sid)
    record[discord_id] = name[2:-1]  # Strip off Discord md codes
    if record[discord_name] == '':
        record[discord_name] = user_name
    if new_sid <= len(ldb):
        ldb.insert(new_sid - 1, record)
    else:
        ldb.append(record)
    return new_sid


def del_user(search_sid, ldb: list):
    # Find index in ldb corresponding to sid and remove
    index = get_index(str(search_sid), sid, ldb)
    if index < 0:
        return -1
    del ldb[index]
    return index


def next_avail_sid(ldb: list):
    index = 0
    for row in ldb:
        if int(row[sid]) - index > 1:
            # Found empty row
            return index + 1
        else:
            if int(row[sid]) > index:
                index = int(row[sid])
    return index + 1


if __name__ == '__main__':
    test = [1, 2, 3]
    send_statistics(test)
    pass
