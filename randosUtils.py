import base64
import hashlib
import json
import os
import requests # type: ignore
from cryptography.hazmat.primitives import hashes # type: ignore
from cryptography.hazmat.primitives.asymmetric import padding #type: ignore
from cryptography.hazmat.primitives import serialization #type: ignore

def validateProgram(filename: str, keysfoldername: str = '/progpubkeys'):
    # Load the JSON from the file
    data: dict = {}
    if not (os.path.exists('./files' + filename) and os.path.isfile('./files' + filename)):
        print('Unable to find the requested file')
        return (None, None, None, None)
    with open('./files' + filename, 'r') as inputfile:
        data = json.load(inputfile)

    if not ('publickey' in data and 'pubkeyhash' in data and 'code' in data and 'signature' in data):
        print('Program file missing important attributes')
        return (False, [], False, False)
    # Restore the original values
    publickey: bytes = base64.b64decode(data['publickey'])  # Decode Base64 to bytes
    pubkeyhash = data['pubkeyhash']  # Already the original hash string
    #permissions = data['permissions']  # Already the original list
    pycode = data['code']  # Already the original pycode 
    signature: bytes = base64.b64decode(data['signature'])  # Decode Base64 to bytes

    userTrustsKey: bool = False
    filesOfCorrespondingKeys: list = []
    #correspondingKey = b''
    keyHashValid: bool = False
    if os.path.exists('./files' + keysfoldername) and os.path.isdir('./files' + keysfoldername):
        for file in os.listdir('./files' + keysfoldername):
            #print(os.listdir('./files' + keysfoldername))
            #print(file)
            if os.path.isfile('./files'+keysfoldername+'/'+file):
                fc = b''
                #print(file)
                with open('./files'+keysfoldername+'/'+file,'rb') as keyfile:
                    fc = keyfile.read()
                if (fc == publickey):
                    #correspondingKey = fc
                    #print(file + ' is the corresponding key')
                    userTrustsKey = True
                    filesOfCorrespondingKeys.append(file)
        if hashlib.sha256(publickey).hexdigest() == pubkeyhash:
            #print('Public key hash valid')
            keyHashValid = True
    else:
        print('Unable to find the public keys directory')
    public_key = serialization.load_pem_public_key(publickey)

    try:
        public_key.verify(
            signature,
            hashlib.sha256(pycode.encode()).hexdigest().encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        #print("Signature validation successful.")
        return (userTrustsKey, filesOfCorrespondingKeys, keyHashValid, True)
    except Exception:
        #print(f"Signature validation failed")
        return (userTrustsKey, filesOfCorrespondingKeys, keyHashValid, False)

def findUsernameByUUID(username: str, users):
    for user in users:
        if (users[user]['uname'] == username):
            return user
    return None

def saveSystemFiles(users, sudoers):
    # Convert UUIDs to strings
    serialisable_sudoers = []
    for sudoer in sudoers:
        serialisable_sudoers.append(str(sudoer))
    with open('./files/sudoers.json', 'w') as sudoersfile:
        sudoersfile.write(json.dumps(serialisable_sudoers))
    # Convert UUID keys to strings
    serialisable_users = {str(key): value for key, value in users.items()}
    with open('./files/users.json', 'w') as usersfile:
        usersfile.write(json.dumps(serialisable_users))

def executeCommand(cmds: list, sudoPowers: bool):
    cmd = cmds[0]
    code = ''
    fc: dict = {}
    utk, filesOfCorrespondingKeys, khv, validation = validateProgram('./files/bin/' + cmd)
    if not (utk and khv and validation):
        print('Validation failed. Program may be tampered with or from an unauthorised source.')
        return False
    with open('./files/bin/' + cmd) as file:
        if isinstance(file, str):
            fc = json.load(file)
        else:
            fc = json.load(file.read())
    if ('sudo.runAsIs' in fc['permissions']):
        code = base64.b64decode(fc['code']).decode()
        if sudoPowers:
            exec(code)
            return True
        else:
            print('This action requires elevated privileges.')
            return False

def downloadFile(uri: str, filename: str):
    """
    Downloads a file from a given URI and saves it to a specified local filename.
    
    Parameters:
        uri (str): The URI to download the file from.
        filename (str): The path where the file will be saved locally.
    
    Raises:
        Exception: If there is an error during the file download.
    """
    try:
        print(f"Downloading file from {uri}...")
        response = requests.get(uri, stream=True)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):  # Download in chunks
                if chunk:  # Filter out keep-alive new chunks
                    file.write(chunk)
        print(f"File successfully downloaded and saved to {filename}.")
    except Exception as e:
        print(f"Failed to download the file: {e}")
        raise