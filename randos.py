# Imports
import json
import os
import uuid
import random
import hashlib
import randosUtils
import getpass
import socket

# Searching for ./files and creating if necessary
if (not os.path.exists('./files')):
    os.mkdir('./files')

# Getting user file and creating if necessary
if (not os.path.exists('./files/users.json')):
    with open('./files/users.json', 'w') as usersfile:
        usersfile.write("{"+"}")
        usersfile.close()
users = None
with open('./files/users.json', 'r') as usersfile:
    users = json.load(usersfile)

# Getting sudoers file and creating if necessary
if (not os.path.exists('./files/sudoers.json')):
    with open('./files/sudoers.json', 'w') as sudoersfile:
        sudoersfile.write("[]")
        sudoersfile.close()
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
        if (not os.path.exists('./files/home')):
            os.mkdir('./files/home')
        if (os.path.exists('./files' + newHomeDir)):
            clearPath = input('The home directory for your user already exists. Would you like to clear it? [y/N]')
            if (clearPath.capitalize() == 'Y'):
                os.removedirs('./files' + newHomeDir)
                os.mkdir('./files' + newHomeDir)
        else:
            os.mkdir('./files' + newHomeDir)
        newUUID = str(uuid.uuid4())
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
        else:
            print('Directory already exists. Continuing.')
        
        print('Searching for builtin public key...')
        if (not os.path.exists('./files/progpubkeys/builtinpubkey.pem')):
            print('Key not found. Downloading.')
            randosUtils.downloadFile('https://www.dropbox.com/scl/fi/9abkuoyh6dd0eco5yikrz/randosBuiltinPublicKey.pem?rlkey=satw67bs8w6xalost80ohe8lr&st=y4ns45ei&dl=1', './files/progpubkeys/builtinpubkey.pem') # ONLY LUNA (THE CREATOR) IS ALLOWED TO CHANGE THIS LINE!
        else:
            print('Builtin key found. Skipping.')
            print('You can download the builtin key at:')
            print('https://www.dropbox.com/scl/fi/9abkuoyh6dd0eco5yikrz/randosBuiltinPublicKey.pem?rlkey=satw67bs8w6xalost80ohe8lr&st=y4ns45ei&dl=0') # ONLY LUNA (THE CREATOR) IS ALLOWED TO CHANGE THIS LINE!
        print('Checking for program directory')
        if (not os.path.exists('./files/bin')):
            print('Program directory not found. Creating new one.')
            os.mkdir('./files/bin')
        else:
            print('Program directory found. Continuing.')
        print('Checking for cfg directory')
        if (not os.path.exists('./files/cfg')):
            print('Config directory not found. Creating new one.')
            os.mkdir('./files/cfg')
        else:
            print('Config directory found. Continuing.')
        print('Checking for canRunAsIs config file')
        if (not os.path.exists('./files/cfg/canRunAsIs')):
            print('canRunAsIs config file not found. Creating new one.')
            with open('./files/cfg/canRunAsIs', 'w') as craiFile:
                craiFile.write('builtinpubkey.pem')
                craiFile.close()
        else:
            print('canRunAsIs config file found. continuing')
        # Add defualt program files
        builtinPrograms = ['pwd']
        for prog in builtinPrograms:
            if os.path.exists('./files/bin/' + prog):
                print(prog + ' program file found. Skipping.')
            else:
                print(f'Downloading {prog}')
                randosUtils.downloadFile(f'https://raw.githubusercontent.com/alfre375/randOS/main/{prog}', f'./files/bin/{prog}')
                utk, filesOfCorrespondingKeys, khv, res = randosUtils.validateProgram(f'/bin/{prog}')
                print(utk, filesOfCorrespondingKeys, khv, res)
                if ('builtinpubkey.pem' in filesOfCorrespondingKeys) and utk and khv and res:
                    print('Validation successful')
                else:
                    print('WARN: Validation failed. File may be tampered with. Deleting.')
                    os.remove(f'./files/bin/{prog}')
        print('You\'re all set! Now just log in with your new credentials!')
        break

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
    cwd = users[userUUID]['homedir']
    while True:
        cmd = input(uname + '@' + socket.gethostname() + ' [' + cwd + '] $ ')
        cmds = cmd.split(' ')
        if (cmd == ''):
            continue
        if cmds[0] == 'sudo':
            if userUUID in sudoers:
                cmds.remove('sudo')
                randosUtils.executeCommand(cmds, True)
                continue
            else:
                print('User is not in the sudoers file.')
                continue
        randosUtils.executeCommand(cmds, False)
except KeyboardInterrupt:
    print('Saving files...')
    randosUtils.saveSystemFiles(users, sudoers)
    print('Goodbye')
    exit()