import datetime
import random
import string
import sheetHandler
import time

from googleapiclient.errors import HttpError
from r8diumInclude import USR_LVL0, USR_LVL1, USR_LVL2, CH_USER, CH_ADMIN


def generate_password(length=20,
                      lowercase=True,
                      uppercase=True,
                      numbers=True,
                      special=True):
    chars = []
    if lowercase:
        chars += string.ascii_lowercase
    if uppercase:
        chars += string.ascii_uppercase
    if numbers:
        chars += string.digits
    if special:
        chars += string.punctuation
    pw = random.choices(chars, k=length)
    return ''.join(pw)


def add_user(name: str, sheet):
    if '<@' in name:
        return add_user_by_id_(name, sheet)
    # First, check to see if user exists - if so exit
    if sheetHandler.get_index(name, 'Discord Name', sheet) != -1:
        return f'[r8udbBot: NAME ERROR] Discord name "{name}" already exists'
    nextrow = sheetHandler.get_last_row(sheet) + 1
    nextsid = sheetHandler.get_highest_val('SID', sheet) + 1
    newpass = generate_password(random.randint(15, 25))
    joindate = datetime.date.today().strftime('%#m/%#d/%y')
    sheetHandler.set_element(nextrow, 'SID', str(nextsid), sheet)
    sheetHandler.set_element(nextrow, 'Discord Name', name, sheet)
    sheetHandler.set_element(nextrow, 'Password', newpass, sheet)
    sheetHandler.set_element(nextrow, 'Join', joindate, sheet)
    sheetHandler.set_element(nextrow, 'Ban', 'N', sheet)
    return f'{name} (SID: {nextsid}) added on {joindate}, pass: {newpass}'


def add_user_by_id_(name: str, sheet):
    # Strip off <@ > decorators from id
    name = name[2:]
    name = name[:-1]
    # Check to see if user exists - if so exit
    if sheetHandler.get_index(name, 'Discord ID', sheet) != -1:
        return f'[r8udbBot: ID ERROR] Discord ID {name} already exists'
    nextrow = sheetHandler.get_last_row(sheet) + 1
    nextsid = sheetHandler.get_highest_val('SID', sheet) + 1
    newpass = generate_password(random.randint(15, 25))
    joindate = datetime.date.today().strftime('%#m/%#d/%y')
    sheetHandler.set_element(nextrow, 'SID', str(nextsid), sheet)
    sheetHandler.set_element(nextrow, 'Discord ID', name, sheet)
    sheetHandler.set_element(nextrow, 'Password', newpass, sheet)
    sheetHandler.set_element(nextrow, 'Join', joindate, sheet)
    sheetHandler.set_element(nextrow, 'Ban', 'N', sheet)
    return f'{name} (SID: {nextsid}) added on {joindate}, pass: {newpass}'


def add_note(sid, note, sheet):
    index = sheetHandler.get_index(sid, 'SID', sheet)
    if index < 0:
        return f'[r8udbBot: INDEX ERROR] SID "{sid}" not found'
    value = sheetHandler.get_element(index, 'Notes', sheet)
    if value == -1:
        value = ''
    if value:
        update = value + '| ' + str(note)
        sheetHandler.set_element(index, "Notes", update, sheet)
    else:
        sheetHandler.set_element(index, "Notes", str(note), sheet)


def ban_user(sid, duration: int, reason: str, sheet):
    try:
        bandate = datetime.date.today().strftime('%#m/%#d/%y')
        index = sheetHandler.get_index(sid, 'SID', sheet)
        if index < 0:
            return f'[r8udbBot: INDEX ERROR] SID "{sid}" not found'
        sheetHandler.set_element(index, 'Ban', 'Y', sheet)
        sheetHandler.set_element(index, 'Ban Date', bandate, sheet)
        sheetHandler.set_element(index, 'Ban Duration', str(duration), sheet)
        uname = sheetHandler.get_element(index, 'Discord Name', sheet)
        newpw = generate_password(random.randint(15, 25))
        sheetHandler.set_element(index, "Password", newpw, sheet)
        add_note(sid, f'Banned ({bandate}) for {duration} days - {reason}', sheet)
        return f'User "{uname}" [SID: {sid}]) **Banned** and password changed'

    except HttpError as err:
        return f'[r8udbBot: HTTP ERROR] {err}'


def dump_dnames(sheet):
    retstr = 'Discord name list:\n'
    try:
        sid_col = sheetHandler.get_col('SID', sheet)
        name_col = sheetHandler.get_col('Discord Name', sheet)
        for i in range(1, len(sid_col)):
            retstr += f'SID [{sid_col[i][0]}]: {name_col[i][0]}\n'
        return retstr

    except HttpError as err:
        return f'[r8udbBot: HTTP ERROR] {err}'


def dump_rnames(sheet):
    retstr = 'Run8 name list:\n'
    try:
        sid_col = sheetHandler.get_col('SID', sheet)
        name_col = sheetHandler.get_col('Run8 Name', sheet)
        for i in range(1, len(sid_col)):
            retstr += f'SID [{sid_col[i][0]}]: {name_col[i][0]}\n'
        return retstr

    except HttpError as err:
        return f'[r8udbBot: HTTP ERROR] {err}'

def show_notes(sid, sheet):
    index = sheetHandler.get_index(sid, 'SID', sheet)
    if index < 0:
        return f'[r8udbBot: INDEX ERROR] SID "{sid}" not found'
    return sheetHandler.get_element(index, 'Notes', sheet)


def show_pass(discord_id, sheet):
    try:
        index = sheetHandler.get_index(discord_id, "Discord ID", sheet)
        if index < 0:
            return f'[r8udbBot: INDEX ERROR] ID "{discord_id}" not found'
        if sheetHandler.get_element(index, "Ban", sheet) != 'N':
            return f'You are currently banned'  # Don't let banned users see their password
        result = sheetHandler.get_element(index, "Password", sheet)
        return result

    except HttpError as err:
        return f'[r8udbBot: HTTP ERROR] {err}'


def show_user(sid, sheet):
    index = sheetHandler.get_index(sid, 'SID', sheet)
    if index < 0:
        return f'[r8udbBot: INDEX ERROR] SID "{sid}" not found'
    retStr = ''
    for item in sheetHandler.COLUMNS:
        retStr += f'**{item}**: {sheetHandler.get_element(index, item, sheet)}\n'
    return retStr


def unban_user(sid, sheet):
    try:
        currdate = datetime.date.today().strftime('%#m/%#d/%y')
        index = sheetHandler.get_index(sid, 'SID', sheet)
        if index < 0:
            return f'[r8udbBot: INDEX ERROR] SID "{sid}" not found'
        sheetHandler.set_element(index, 'Ban', 'N', sheet)
        sheetHandler.set_element(index, 'Ban Date', '', sheet)
        sheetHandler.set_element(index, 'Ban Duration', '', sheet)
        add_note(sid, f'Ubanned ({currdate}) by admin override', sheet)
        uname = sheetHandler.get_element(index, 'Discord Name', sheet)
        return f'User "{uname}" [SID: {sid}] **Unbanned**'

    except HttpError as err:
        return f'[r8udbBot: HTTP ERROR] {err}'


def new_pass(discord_id, sheet):
    try:
        index = sheetHandler.get_index(discord_id, "Discord ID", sheet)
        if index < 0:
            return f'[r8udbBot: INDEX ERROR] ID "{discord_id}" not found'
        if sheetHandler.get_element(index, "Ban", sheet) != 'N':
            return f'You are currently banned'
        newpw = generate_password(random.randint(15, 25))
        sheetHandler.set_element(index, "Password", newpw, sheet)
        return f'new password = {newpw}'

    except HttpError as err:
        return f'[r8udbBot: HTTP ERROR] {err}'


def get_response(message: str, uname: str, discord_id: int, roles: list, channel: str, sheet) -> str:
    ###
    # Main function to handle bot commands
    ###
    p_message = message.lower()
    rolelist = [role.name for role in roles]
    rolelist.remove('@everyone')

    if p_message.split()[0] == 'add':
        if channel != CH_ADMIN:
            return ''
        if USR_LVL1 in rolelist:
            return add_user(str(p_message.split()[1]), sheet)
        else:
            return '[r8udbBot: Permissions error] Invalid user role for command'

    if p_message.split()[0] == 'addnote':
        if channel != CH_ADMIN:
            return ''
        if USR_LVL1 in rolelist:
            return add_note(int(p_message.split()[1]), ' '.join(p_message.split()[2:]), sheet)
        else:
            return '[r8udbBot: Permissions error] Invalid user role for command'

    if p_message.split()[0] == 'ban':
        if channel != CH_ADMIN:
            return ''
        if USR_LVL1 in rolelist:
            sid = int(p_message.split()[1])
            duration = int(p_message.split()[2])
            reason = ' '.join(p_message.split()[3:])
            return ban_user(sid, duration, reason, sheet)
        else:
            return '[r8udbBot: Permissions error] Invalid user role for command'

    if p_message == 'showdnames':
        if channel != CH_ADMIN:
            return ''
        if USR_LVL1 in rolelist:
            return dump_dnames(sheet)
        else:
            return '[r8udbBot: Permissions error] Invalid user role for command'

    if p_message == 'showrnames':
        if channel != CH_ADMIN:
            return ''
        if USR_LVL1 in rolelist:
            return dump_rnames(sheet)
        else:
            return '[r8udbBot: Permissions error] Invalid user role for command'

    if p_message.split()[0] == 'readnote':
        if channel != CH_ADMIN:
            return ''
        if USR_LVL1 in rolelist:
            return show_notes(int(p_message.split()[1]), sheet)
        else:
            return '[r8udbBot: Permissions error] Invalid user role for command'

    if p_message.split()[0] == 'show':
        if channel != CH_ADMIN:
            return ''
        if USR_LVL1 in rolelist:
            return show_user(int(p_message.split()[1]), sheet)
        else:
            return '[r8udbBot: Permissions error] Invalid user role for command'

    if p_message.split()[0] == 'unban':
        if channel != CH_ADMIN:
            return ''
        if USR_LVL1 in rolelist:
            return unban_user(int(p_message.split()[1]), sheet)
        else:
            return '[r8udbBot: Permissions error] Invalid user role for command'

    #
    # User commands
    #
    if p_message == 'newpass':
        if channel != CH_USER:
            return ''
        if USR_LVL2 in rolelist:
            return new_pass(discord_id, sheet)
        else:
            return 'Invalid user role for command'

    if p_message == 'showpass':
        if channel != CH_USER:
            return ''
        if USR_LVL2 in rolelist:
            return show_pass(discord_id, sheet)
        else:
            return '[r8udbBot: Permissions error] Invalid user role for command'

    if p_message == 'write':
        if channel != CH_ADMIN:
            return ''
        if USR_LVL0 in rolelist:
            return sheetHandler.write_security_file(sheet)
        else:
            return '[r8udbBot: Permissions error] Invalid user role for command'

    if p_message == 'merge':
        if channel != CH_ADMIN:
            return ''
        if USR_LVL0 in rolelist:
            return sheetHandler.merge_xml(sheet)
        else:
            return '[r8udbBot: Permissions error] Invalid user role for command'

    if p_message == 'help':
        if channel == CH_USER:
            return '## r8udbBot User Commands:\n' \
                   '**showpass** (show current password)\n' \
                   '**newpass** (generate new password)\n'
        if channel == CH_ADMIN:
            cmd_list = '## r8udbBot Admin Commands:\n' \
                       '**add** *<discord_name>* (add a new user)\n' \
                       '**addnote** *<sid> <note_text>* (append a note to a user)\n' \
                       '**ban** *<sid> <duration> <reason_text>* (ban use for *n* days with explanation)\n' \
                       '**help** (show this help)\n' \
                       '**readnote** *<sid>* (display notes for a user)\n' \
                       '**show** *<sid>* (display stats for user)\n' \
                       '**showdnames** (show Discord names of all users)\n'\
                       '**showrnames** (show Run8 names of all users)\n' \
                       '**unban** *<sid>* (remove ban from user)\n' \
                       '\n## r8udbBot Server commands:\n' \
                       '**write** (write new *HostSecurity.xml* file)\n' \
                       '**merge** (merge UID updates from Run8 server into database)\n'
            return cmd_list

    return ''
