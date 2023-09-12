import os
import xmltodict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from r8udbBotInclude import SPREADSHEET_ID, SECURITY_FILE

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
COLUMNS = ['SID', 'Discord Name', 'Discord ID', 'Run8 Name', 'UID', 'Role', 'Password',
           'Join', 'IP', 'Ban', 'Ban Date', 'Ban Duration', 'Notes']
COL_NAMES = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
FULL_SHEET_RANGE = 'A:' + COL_NAMES[len(COLUMNS) - 1]

XML_ROOT_NAME = 'HostSecurityData'
XML_BANNED_CATEGORY_NAME = 'Banned_Users'
XML_BANNED_NAME = 'BannedUser'
XML_UNIQUE_CATEGORY_NAME = 'Unique_Logins'
XML_UNIQUE_NAME = 'UniqueLogin'
XML_NAME = 'Name'
XML_UID = 'UID'
XML_IP = 'IP'
XML_PASSWORD = 'Password'
XML_DICT = \
    {XML_ROOT_NAME: {XML_BANNED_CATEGORY_NAME: {XML_BANNED_NAME: []}, XML_UNIQUE_CATEGORY_NAME: {XML_UNIQUE_NAME: []}}}
BAN_DICT = XML_DICT[XML_ROOT_NAME][XML_BANNED_CATEGORY_NAME][XML_BANNED_NAME]
USR_DICT = XML_DICT[XML_ROOT_NAME][XML_UNIQUE_CATEGORY_NAME][XML_UNIQUE_NAME]


def auth_sheet():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Now open the sheet
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    return creds, sheet


def get_index(search_string: str, search_col: str, this_sheet) -> int:
    """
    Return row number keyed off of <search_string> contained in column <search_col>
    returns (-1) if string not found or invalid column name is specified.
    NOTE: Will return first instance if there are duplicates
    """
    try:
        if search_col not in COLUMNS:
            return -1  # Invalid search column specified
        search_range = (f'{COL_NAMES[COLUMNS.index(search_col)]}:'
                        f'{COL_NAMES[COLUMNS.index(search_col)]}')
        res = this_sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                      range=search_range).execute()
        val = res.get('values', [])
        flat_values = [num for sublist in val for num in sublist]

        if str(search_string) not in flat_values:
            return -1
        else:
            return flat_values.index(str(search_string)) + 1

    except HttpError as err:
        print(err)


def get_last_row(this_sheet) -> int:
    res = this_sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                  range='A:A').execute()
    val = res.get('values', [])
    return len(val)


def get_highest_val(search_col, this_sheet) -> int:
    t = 0
    search_range = (f'{COL_NAMES[COLUMNS.index(search_col)]}:'
                    f'{COL_NAMES[COLUMNS.index(search_col)]}')
    res = this_sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=search_range).execute()
    val = res.get('values', [])
    try:
        for row in val[1:]:
            if int(row[0]) > t:
                t = int(row[0])

    except Exception as e:
        print(f'Failed with error {e}')
    return t


def get_element(index: int, search_col: str, this_sheet):
    """
    Return the element associated with the index and the column name
    :param index:
    :param search_col:
    :param this_sheet:
    :return:
    """
    try:
        if search_col not in COLUMNS:
            return -1  # Invalid search column specified
        search_range = (f'{COL_NAMES[COLUMNS.index(search_col)]}:'
                        f'{COL_NAMES[COLUMNS.index(search_col)]}')
        res = this_sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                      range=search_range).execute()
        val = res.get('values', [])
        return val[index - 1][0]

    except HttpError as err:
        print(err)

    except IndexError:
        return ''


def set_element(index: int, search_col: str, write_val: str, this_sheet):
    try:
        if search_col not in COLUMNS:
            return -1  # Invalid search column specified
        search_range = (f'{COL_NAMES[COLUMNS.index(search_col)]}:'
                        f'{COL_NAMES[COLUMNS.index(search_col)]}')
        cell = search_range + str(index)
        this_sheet.values().update(spreadsheetId=SPREADSHEET_ID, range=cell,
                                   valueInputOption="USER_ENTERED",
                                   body={"values": [[f"{write_val}"]]}).execute()

    except HttpError as err:
        print(err)


def write_security_file(this_sheet):
    try:
        sheetresult = this_sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                              range=FULL_SHEET_RANGE).execute()
        sheetvalues = sheetresult.get('values', [])
        if not sheetvalues:
            print('No data found.')
        else:
            print(f'Found {len(sheetvalues)} rows:')
            for sheetvalue in sheetvalues:
                if sheetvalue[COLUMNS.index('Ban')] == 'Y':
                    BAN_DICT.append({XML_NAME: sheetvalue[COLUMNS.index('Run8 Name')],
                                     XML_UID: sheetvalue[COLUMNS.index('UID')],
                                     XML_IP: sheetvalue[COLUMNS.index('IP')]})
                elif sheetvalue[COLUMNS.index('Ban')] == 'N':
                    USR_DICT.append({XML_NAME: sheetvalue[COLUMNS.index('Run8 Name')],
                                     XML_UID: sheetvalue[COLUMNS.index('UID')],
                                     XML_PASSWORD: sheetvalue[COLUMNS.index('Password')]})

    except HttpError as err:
        print(err)

    xml_out = xmltodict.unparse(XML_DICT, pretty=True)
    print(xml_out)

    wp = open(SECURITY_FILE, 'w')
    wp.write(xml_out)
    wp.close()
    return 'file written'


def merge_xml(this_sheet):
    # Read current HostSecurity file and update UID fields based on password (gross)
    fp = open(SECURITY_FILE, 'r')
    xml_in = xmltodict.parse(fp.read(), process_namespaces=True)
    fp.close()
    retstr = '`Merge results:\n-------------\n'
    for item in range(0, len(xml_in[XML_ROOT_NAME][XML_UNIQUE_CATEGORY_NAME][XML_UNIQUE_NAME])):
        retstr += f'{item : 03d}: '
        pindex = get_index(xml_in[XML_ROOT_NAME][XML_UNIQUE_CATEGORY_NAME][XML_UNIQUE_NAME][item][XML_PASSWORD],
                           'Password', this_sheet)
        if pindex != -1:  # Found xml password in sheet
            uid = get_element(pindex, 'UID', this_sheet)
            if not uid:  # No UID in sheet, so populate with XML version
                try:
                    new_id = xml_in[XML_ROOT_NAME][XML_UNIQUE_CATEGORY_NAME][XML_UNIQUE_NAME][item][XML_UID]
                    retstr += f'added UID[{new_id}]' \
                              f'to SID[{get_element(pindex, "SID", this_sheet)}]\n'
                except KeyError:
                    retstr += f'Found password but no UID (in XML) for '\
                              f'SID[{get_element(pindex, "SID", this_sheet)}]\n'
                    new_id = ''
                set_element(pindex, 'UID', new_id, this_sheet)
            else:
                try:
                    if uid != xml_in[XML_ROOT_NAME][XML_UNIQUE_CATEGORY_NAME][XML_UNIQUE_NAME][item][XML_UID]:
                        retstr += f'Existing UID mismatch for SID[{get_element(pindex, "SID", this_sheet)}]\n'
                        retstr += f'- Sheet UID: {uid}\n'
                        retstr += f'- XML   UID: '
                        retstr += f'{xml_in[XML_ROOT_NAME][XML_UNIQUE_CATEGORY_NAME][XML_UNIQUE_NAME][item][XML_UID]}\n'
                    else:
                        retstr += f'Existing UID valid for SID[{get_element(pindex, "SID", this_sheet)}]\n'
                except KeyError:
                    retstr += f'Found password but no UID (in XML) for ' \
                              f'SID[{get_element(pindex, "SID", this_sheet)}]\n'

        else:
            retstr += f'Password[{xml_in[XML_ROOT_NAME][XML_UNIQUE_CATEGORY_NAME][XML_UNIQUE_NAME][item][XML_PASSWORD]}'
            retstr += '] not found\n'

    return retstr + '`'


## Main ##
if __name__ == '__main__':
    sheet_credential, user_sheet = auth_sheet()
