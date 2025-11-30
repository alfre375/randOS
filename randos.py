# Imports
import json
import os
if not os.path.exists('./randosUtils.py'):
    import requests
    try:
        print("The randosUtils.py file is missing, downloading randosUtils.py from GitHub...")
        response = requests.get('https://raw.githubusercontent.com/alfre375/randOS/main/randosUtils.py', stream=True)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

        with open('./randosUtils.py', 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):  # Download in chunks
                if chunk:  # Filter out keep-alive new chunks
                    file.write(chunk)
        print(f"File successfully downloaded and saved to randosUtils.py.")
    except Exception as e:
        print(f"Failed to download the file: {e}")
        raise
import uuid
import random
import hashlib
import randosUtils
import getpass
import socket
from termcolor import colored as coloured #type: ignore

versionId = 0.0
version = '0.0.0-pre-0'

# Searching for ./files and creating if necessary
if (not os.path.exists('./files')):
    os.mkdir('./files')

# Getting fileowners file and creating if necessary
if not os.path.exists('./files/filePermissions.json'):
    with open('./files/filePermissions.json', 'w') as fpfile:
        fpfile.write('{}')
        fpfile.close()
filePerms = None
with open('./files/filePermissions.json', 'r') as fpfile:
    filePerms = json.load(fpfile)
    
# Functions relating to fileperms
def updateFilePermsFile():
    global filePerms
    with open('./files/filePermissions.json', 'w') as fpfile:
        fpfile.write(json.dumps(filePerms))

def createFile(path: str, owner: str = 'root', initialText: str = '', allowReplacement: bool = False, permissions: str = 'rwx------'):
    global filePerms
    if not path:
        raise Exception('Must specify a path')
    
    exactPath = str(os.path.abspath(str(os.path.abspath('./files')) + path))
    if (os.path.exists(exactPath)) and (not allowReplacement):
        raise Exception('Allow replacement is set to False, but file already exists')
    with open(exactPath, 'w') as file:
        file.write(initialText)
        file.close()
    
    filePerms[path] = {'owner': owner, 'permissions': permissions}
    updateFilePermsFile()
    return True

# Getting user file and creating if necessary
if (not os.path.exists('./files/users.json')):
    createFile('/users.json', initialText='{}', permissions='rw-r--r--')
users = None
with open('./files/users.json', 'r') as usersfile:
    users = json.load(usersfile)

# Getting sudoers file and creating if necessary
if (not os.path.exists('./files/sudoers.json')):
    createFile('/sudoers.json', initialText='[]', permissions='rw-r--r--')
sudoers: list = []
with open('./files/sudoers.json', 'r') as sudoersfile:
    sudoers = json.load(sudoersfile)

# Checking for existing users
if (len(users) == 0):
    while True:
        print('Let\'s get you set all set up.')
        newUname: str = input('Enter a new username: ')
        if ('.' in newUname) or ('/' in newUname):
            print('The . and / characters are not allowed in the username')
            continue
        newPassword = getpass.getpass('Now, enter a new password for your user: ')
        newHomeDir = '/home/' + newUname
        newUUID = str(uuid.uuid4())
        if (not os.path.exists('./files/home')):
            os.mkdir('./files/home')
            filePerms['/home'] = {'owner': 'root', 'permissions': 'rw-r--r--'}
        if (os.path.exists('./files' + newHomeDir)):
            clearPath = input('The home directory for your user already exists. Would you like to clear it? [y/N]')
            if (clearPath.capitalize() == 'Y'):
                os.removedirs('./files' + newHomeDir)
                os.mkdir('./files' + newHomeDir)
        else:
            os.mkdir('./files' + newHomeDir)
        filePerms[newHomeDir] = {'owner': newUUID, 'permissions': 'rw-r-----'}
        newSalt = str(random.random())
        newPassword = newPassword + newSalt
        newPassword = hashlib.sha256(newPassword.encode('UTF-8')).hexdigest()
        users[newUUID] = {
            'uname': newUname,
            'passwd': newPassword,
            'salt': newSalt,
            'homedir': newHomeDir
        }
        print('Adding user to sudoers file')
        sudoers.append(newUUID)
        print('Searching for program public keys directory')
        if (not os.path.exists('./files/progpubkeys')):
            print('Directory not found, creating new one')
            os.mkdir('./files/progpubkeys')
            filePerms['/progpubkeys'] = {'owner': 'root', 'permissions': 'rw-r--r--'}
        else:
            print('Directory already exists. Continuing.')
        
        print('Searching for builtin public key...')
        if (not os.path.exists('./files/progpubkeys/builtinpubkey.pem')):
            print('Key not found. Downloading.')
            createFile('/progpubkeys/builtinpubkey.pem', permissions='rw-r--r--')
            randosUtils.downloadFile('https://www.dropbox.com/scl/fi/9abkuoyh6dd0eco5yikrz/randosBuiltinPublicKey.pem?rlkey=satw67bs8w6xalost80ohe8lr&st=y4ns45ei&dl=1', './files/progpubkeys/builtinpubkey.pem') # ONLY LUNA (THE CREATOR) IS ALLOWED TO CHANGE THIS LINE!
        else:
            print('Builtin key found. Skipping.')
            print('You can download the builtin key at:')
            print('https://www.dropbox.com/scl/fi/9abkuoyh6dd0eco5yikrz/randosBuiltinPublicKey.pem?rlkey=satw67bs8w6xalost80ohe8lr&st=y4ns45ei&dl=0') # ONLY LUNA (THE CREATOR) IS ALLOWED TO CHANGE THIS LINE!
        print('Checking for program directory')
        if (not os.path.exists('./files/bin')):
            print('Program directory not found. Creating new one.')
            os.mkdir('./files/bin')
            filePerms['/bin'] = {'owner': 'root', 'permissions': 'rwxr-xr-x'}
        else:
            print('Program directory found. Continuing.')
        print('Checking for cfg directory')
        if (not os.path.exists('./files/cfg')):
            print('Config directory not found. Creating new one.')
            os.mkdir('./files/cfg')
            filePerms['/cfg'] = {'owner': 'root', 'permissions': 'rw-r--r--'}
        else:
            print('Config directory found. Continuing.')
        print('Checking for canRunAsIs config file')
        if (not os.path.exists('./files/cfg/canRunAsIs')):
            print('canRunAsIs config file not found. Creating new one.')
            createFile('/cfg/canRunAsIs', initialText='builtinpubkey.pem', permissions='rw-r--r--')
        else:
            print('canRunAsIs config file found. continuing')
        # Add defualt program files
        builtinPrograms = ['pwd', 'cd', 'ls']
        for prog in builtinPrograms:
            if os.path.exists('./files/bin/' + prog):
                print(prog + ' program file found. Skipping.')
            else:
                print(f'Downloading {prog}')
                createFile(f'/bin/{prog}', permissions='rwxr-xr-x')
                randosUtils.downloadFile(f'https://raw.githubusercontent.com/alfre375/randOS/main/{prog}', f'./files/bin/{prog}')
                utk, filesOfCorrespondingKeys, khv, res = randosUtils.validateProgram(f'/bin/{prog}')
                print(utk, filesOfCorrespondingKeys, khv, res)
                if ('builtinpubkey.pem' in filesOfCorrespondingKeys) and utk and khv and res:
                    print('Validation successful')
                else:
                    print('WARN: Validation failed. File may be tampered with. Deleting.')
                    os.remove(f'./files/bin/{prog}')
                    filePerms.remove(f'/bin/{prog}')
        if not ('/' in filePerms):
            filePerms['/'] = {
                'owner': 'root',
                'permissions': 'rw-r--r--'
            }
            updateFilePermsFile()
        print('You\'re all set! Now just log in with your new credentials!')
        break

updateFilePermsFile()

# Now the CLI simulation starts
try:
    while True:
        # Getting the username from the user
        uname: str = input('Please enter a username: ')
        passwd = getpass.getpass('Enter your password: ')
        userUUID = randosUtils.findUsernameByUUID(uname, users)
        if (userUUID == None):
            print('The username and passwords do not match')
            continue
        salt: str = users[userUUID]['salt']
        passwd = passwd + salt
        passwd = hashlib.sha256(passwd.encode('UTF-8')).hexdigest()
        if (passwd == users[userUUID]['passwd']):
            break
        print('The username and passwords do not match')
        continue
    print('Welcome, ' + uname)
    cwd: str = users[userUUID]['homedir']
    while True:
        try:
            cmd: str = input(coloured(uname, 'red') + '@' + socket.gethostname() + ' [' + cwd + '] '+coloured('$', 'green')+' ')
            cmds: list[str] = cmd.split(' ')
            if (cmd == ''):
                continue
            if (cmd == 'logout'):
                print('Saving files...')
                randosUtils.saveSystemFiles(users, sudoers)
                print('Goodbye')
                exit()
            information = {
                'directory':cwd,
                'root': str(os.path.abspath('./files')),
                'userUUID': userUUID
            }
            if cmds[0] == 'sudo':
                if userUUID in sudoers:
                    cmds.remove('sudo')
                    info = information
                    info['userUUID'] = 'root'
                    success, changes = randosUtils.executeCommand(cmds, True, info, filePerms)
                    continue
                else:
                    print('User is not in the sudoers file.')
                    continue
            success, changes = randosUtils.executeCommand(cmds, False, information, filePerms)
            if changes:
                if 'newFilePerms' in changes:
                    filePerms = changes['newFilePerms']
                    updateFilePermsFile()
                if 'newActiveDirectory' in changes:
                    cwd = changes['newActiveDirectory']
        except KeyboardInterrupt:
            print("")
            continue
except KeyboardInterrupt:
    print('Saving files...')
    randosUtils.saveSystemFiles(users, sudoers)
    print('Goodbye')
    exit()