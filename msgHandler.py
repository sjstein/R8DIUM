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
import datetime
import random
import string
import dbAccess
from r8diumInclude import DB_FILENAME, LOG_FILENAME


def generate_password(length=20,
                      lowercase=True,
                      uppercase=True,
                      numbers=True,
                      special=False):
    chars = []
    invalid_chars = ['<', '>', '&', '"', "'", "l", "O"]

    if lowercase:
        chars += string.ascii_lowercase
    if uppercase:
        chars += string.ascii_uppercase
    if numbers:
        chars += string.digits
    if special:
        chars += string.punctuation
    # Strip out invalid characters
    for c in invalid_chars:
        try:
            chars.remove(c)
        except ValueError:
            continue
    pw = random.choices(chars, k=length)
    return ''.join(pw)


def write_log_file(msg):
    try:
        fp = open(LOG_FILENAME, mode='a', encoding='utf-16')  # Using utf-16 because discord does
        datestr = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        fp.write(f'[{datestr}] {msg}\n')

    except Exception as e:
        print(f'Exception in write_log_file : {e}')
        return

    fp.close()
    return


def check_ban_status(sid, ldb):
    ban_date = dbAccess.get_element(sid, dbAccess.sid, dbAccess.ban_date, ldb)
    ban_duration = dbAccess.get_element(sid, dbAccess.sid, dbAccess.ban_duration, ldb)
    try:
        bdate = datetime.datetime.strptime(ban_date, '%m/%d/%y')
    except ValueError:
        # Somehow the ban_date field is malformed - just return a banned status
        return True

    if (datetime.datetime.today() - bdate).days < int(ban_duration):
        return True
    else:
        return False


def read_field(discord_id, field_name, ldb):
    if field_name not in dbAccess.db_field_list:
        return f'[R8DIUM: FIELD ERROR] field: "{field_name}" unknown'
    if int(dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.discord_id, ldb)) < 0:
        return f'[R8DIUM: INDEX ERROR] discord id {discord_id} not found'
    return dbAccess.get_element(discord_id, dbAccess.discord_id, field_name, ldb)


def write_field(discord_id, field_name, write_val, ldb):
    if field_name not in dbAccess.db_field_list:
        return f'[R8DIUM: FIELD ERROR] field: "{field_name}" unknown'
    if int(dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.discord_id, ldb)) < 0:
        return f'[R8DIUM: INDEX ERROR] discord id {discord_id} not found'
    if int(dbAccess.set_element(discord_id, dbAccess.discord_id, field_name, write_val, ldb)) > 0:
        dbAccess.save_db(DB_FILENAME, ldb)
        dbAccess.write_security_file(ldb)
        if write_val == '':
            return '<null>'
        return write_val
    else:
        return f'[R8DIUM: WRITE ERROR] unknown failure to write to field: {field_name}'


def write_field_by_sid(sid, field_name, write_val, ldb):
    if field_name not in dbAccess.db_field_list:
        return f'[R8DIUM: FIELD ERROR] field: "{field_name}" unknown'
    if int(dbAccess.get_element(sid, dbAccess.sid, dbAccess.discord_id, ldb)) < 0:
        return f'[R8DIUM: INDEX ERROR] server id {sid} not found'
    if int(dbAccess.set_element(sid, dbAccess.sid, field_name, write_val, ldb)) > 0:
        dbAccess.save_db(DB_FILENAME, ldb)
        dbAccess.write_security_file(ldb)
        if write_val == '':
            return '<null>'
        return write_val
    else:
        return f'[R8DIUM: WRITE ERROR] unknown failure to write to field: {field_name}'


def add_user(discord_id, discord_name, ldb):
    if dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.sid, ldb) != -1:
        return f'[R8DIUM: ID ERROR] Discord id {discord_id} already exists'
    new_sid = dbAccess.add_new_user(discord_id, discord_name, ldb)
    password = generate_password(random.randint(15, 25))
    join_date = datetime.date.today().strftime('%#m/%#d/%y')
    dbAccess.set_element(new_sid, dbAccess.sid, dbAccess.password, password, ldb)
    dbAccess.set_element(new_sid, dbAccess.sid, dbAccess.join_date, join_date, ldb)
    dbAccess.set_element(new_sid, dbAccess.sid, dbAccess.last_login, join_date, ldb)  # populate last_login
    dbAccess.set_element(new_sid, dbAccess.sid, dbAccess.active, True, ldb)
    dbAccess.set_element(new_sid, dbAccess.sid, dbAccess.banned, False, ldb)
    dbAccess.save_db(DB_FILENAME, ldb)
    dbAccess.write_security_file(ldb)
    dbAccess.send_statistics(ldb)
    return f'{discord_name} (SID: {new_sid}) added on {join_date}, pass: {password}'


def delete_user(discord_id, ldb):
    sid = int(dbAccess.get_element(str(discord_id), dbAccess.discord_id, dbAccess.sid, ldb))
    if sid < 0:
        return f'[R8DIUM: INDEX ERROR] discord user id {discord_id} not found'
    user_name = dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.discord_name, ldb)
    if dbAccess.del_user(sid, ldb) < 0:
        return f'[R8DIUM: UNK ERROR] in delete user routine'
    dbAccess.save_db(DB_FILENAME, ldb)
    dbAccess.write_security_file(ldb)
    dbAccess.send_statistics(ldb)
    return f'User: {user_name} ({discord_id}) deleted'


def add_note(discord_id, note, ldb):
    if int(dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.discord_id, ldb)) < 0:
        return f'[R8DIUM: INDEX ERROR] discord id {discord_id} not found'
    curr_note = dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.notes, ldb)
    if curr_note:
        update = curr_note + '|' + str(note)
        dbAccess.set_element(discord_id, dbAccess.discord_id, dbAccess.notes, update, ldb)
    else:
        dbAccess.set_element(discord_id, dbAccess.discord_id, dbAccess.notes, str(note), ldb)
    dbAccess.save_db(DB_FILENAME, ldb)
    return (f'Note: "{note}" added to user: '
            f'{dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.discord_name, ldb)}')


def add_role(discord_id, role, ldb):
    if int(dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.discord_id, ldb)) < 0:
        return f'[R8DIUM: INDEX ERROR] discord id {discord_id} not found'
    dbAccess.set_element(discord_id, dbAccess.discord_id, dbAccess.role, str(role), ldb)
    dbAccess.save_db(DB_FILENAME, ldb)
    return (f'Role: "{role}" given to user: '
            f'{dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.discord_name, ldb)}')


def suspend_user(discord_id, date, reason, ldb):
    if int(dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.discord_id, ldb)) < 0:
        return -1
    dbAccess.set_element(discord_id, dbAccess.discord_id, dbAccess.active, False, ldb)
    dbAccess.set_element(discord_id, dbAccess.discord_id, dbAccess.password,
                         generate_password(random.randint(15, 25)), ldb)
    add_note(discord_id, f'User suspended on {date} : {reason}', ldb)
    dbAccess.save_db(DB_FILENAME, ldb)
    dbAccess.write_security_file(ldb)
    return


def expire_user(discord_id, exp_date, ldb):
    if int(dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.discord_id, ldb)) < 0:
        return f'[R8DIUM: INDEX ERROR] discord id {discord_id} not found'
    dbAccess.set_element(discord_id, dbAccess.discord_id, dbAccess.active, False, ldb)
    dbAccess.set_element(discord_id, dbAccess.discord_id, dbAccess.password,
                         generate_password(random.randint(15, 25)), ldb)
    add_note(discord_id, f'Expired due to inactivity on {exp_date}', ldb)
    dbAccess.save_db(DB_FILENAME, ldb)
    dbAccess.write_security_file(ldb)
    return


def activate_user(discord_id, admin_name, ldb):
    if int(dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.discord_id, ldb)) < 0:
        return f'[R8DIUM: INDEX ERROR] discord id {discord_id} not found'
    act_date = datetime.date.today().strftime('%#m/%#d/%y')
    dbAccess.set_element(discord_id, dbAccess.discord_id, dbAccess.active, True, ldb)
    dbAccess.set_element(discord_id, dbAccess.discord_id, dbAccess.last_login, act_date, ldb)
    add_note(discord_id, f'Set back to active status by {admin_name} on {act_date}', ldb)
    dbAccess.save_db(DB_FILENAME, ldb)
    dbAccess.write_security_file(ldb)
    return (f'{dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.discord_name, ldb)} '
            f'reactivated on {act_date} by {admin_name}')


def ban_user(discord_id, admin_name, duration, reason, ldb):
    if int(dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.discord_id, ldb)) < 0:
        return f'[R8DIUM: INDEX ERROR] discord id {discord_id} not found'
    ban_date = datetime.date.today().strftime('%#m/%#d/%y')
    # ban_date = datetime.date.today()
    dbAccess.set_element(discord_id, dbAccess.discord_id, dbAccess.banned, True, ldb)
    dbAccess.set_element(discord_id, dbAccess.discord_id, dbAccess.ban_date, ban_date, ldb)
    dbAccess.set_element(discord_id, dbAccess.discord_id, dbAccess.ban_duration, duration, ldb)
    dbAccess.set_element(discord_id, dbAccess.discord_id, dbAccess.password,
                         generate_password(random.randint(15, 25)), ldb)
    add_note(discord_id, f'Banned ({ban_date}) for {duration} days - {reason}', ldb)
    dbAccess.save_db(DB_FILENAME, ldb)
    dbAccess.write_security_file(ldb)
    # [staff member] banned [user] for [duration] days with reason: [reason]
    return (f'{admin_name} **banned** '
            f'{dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.discord_name, ldb)} for {duration} days. '
            f'*Reason*: {reason}')


def unban_user(discord_id, admin_name, ldb):
    if int(dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.discord_id, ldb)) < 0:
        return f'[R8DIUM: INDEX ERROR] discord id {discord_id} not found'
    current_date = datetime.date.today().strftime('%#m/%#d/%y')
    dbAccess.set_element(discord_id, dbAccess.discord_id, dbAccess.banned, False, ldb)
    dbAccess.set_element(discord_id, dbAccess.discord_id, dbAccess.ban_date, '', ldb)
    dbAccess.set_element(discord_id, dbAccess.discord_id, dbAccess.ban_duration, '', ldb)
    add_note(discord_id, f'Unbanned ({current_date}) by {admin_name}', ldb)
    dbAccess.save_db(DB_FILENAME, ldb)
    dbAccess.write_security_file(ldb)
    return (f'{admin_name} **unbanned** '
            f'{dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.discord_name, ldb)}')


def list_users(ldb):
    return_str = f'## User list (total: {len(ldb)})\ndiscord_name / discord_id : join date\n\n'
    for record in ldb:
        return_str += (f'[{record[dbAccess.sid]}] {record[dbAccess.discord_name]} / '
                       f'{record[dbAccess.discord_id]} : {record[dbAccess.join_date]}')
        if record[dbAccess.banned] == 'True':
            return_str += f' **--> BANNED on {record[dbAccess.ban_date]} for {record[dbAccess.ban_duration]} days <--**'
        if record[dbAccess.active] == 'False':
            return_str += f' **--> Currently marked as INACTIVE <--**'
        return_str += '\n'
    return return_str


def show_notes(discord_id, ldb):
    if int(dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.discord_id, ldb)) < 0:
        return f'[R8DIUM: INDEX ERROR] discord id {discord_id} not found'
    return_string = dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.notes, ldb)
    if return_string == '':
        return_string = '<none>'
    return return_string


def show_pass(discord_id, discord_name, ldb):
    if int(dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.sid, ldb)) < 0:
        add_user(discord_id, discord_name, ldb)  # give the md tags back to the UID
        return show_pass(discord_id, discord_name, ldb)
    if dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.banned, ldb) == 'True':
        return f'You are currently banned'  # Don't let banned users see their password
    if dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.active, ldb) == 'False':
        return f'Your account has been suspended due to inactivity - please contact a staff member to renew'
    result = dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.password, ldb)
    return result


def show_user(discord_id, ldb):
    if int(dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.discord_id, ldb)) < 0:
        return f'[R8DIUM: INDEX ERROR] discord id {discord_id} not found'
    result = ''
    for field_name in dbAccess.db_field_list:
        result += f'{field_name}: {dbAccess.get_element(discord_id, dbAccess.discord_id, field_name, ldb)}\n'
    return result


def show_user_by_id(sid, ldb):
    if int(dbAccess.get_element(sid, dbAccess.sid, dbAccess.discord_id, ldb)) < 0:
        return f'[R8DIUM: INDEX ERROR] server id {sid} not found'
    result = ''
    for field_name in dbAccess.db_field_list:
        result += f'{field_name}: {dbAccess.get_element(sid, dbAccess.sid, field_name, ldb)}\n'
    return result


def new_pass(discord_id, ldb):
    if int(dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.sid, ldb)) < 0:
        return f'[R8DIUM: INDEX ERROR] discord id {discord_id} not found'
    if dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.banned, ldb) == 'True':
        return f'You are currently banned'  # Don't let banned users see their password
    if dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.active, ldb) == 'False':
        return f'Your account has been suspended due to inactivity - please contact a staff member to renew'
    new_pw = generate_password(random.randint(15, 25))
    dbAccess.set_element(discord_id, dbAccess.discord_id, dbAccess.password, new_pw, ldb)
    dbAccess.set_element(discord_id, dbAccess.discord_id, dbAccess.uid, None, ldb)
    dbAccess.save_db(DB_FILENAME, ldb)
    dbAccess.write_security_file(ldb)
    # Writing to log file here in order to back-track any nefarious password sharing
    # NOTE: Definitely not very secure storing the password in cleartext, but welcome to the jungle
    write_log_file(f'PASSWORD (RE)SET REQUEST: discord_id [{discord_id}], discord_name ['
                   f'{dbAccess.get_element(discord_id, dbAccess.discord_id, dbAccess.discord_name, ldb)}] '
                   f'{new_pw}')
    return new_pw


if __name__ == '__main__':
    pass
