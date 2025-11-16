import sys
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import getpass
import base64
import json
import os
import interpreter
import re
from pathlib import Path

if len(sys.argv) <= 1:
    print('Options:')
    print('  encode: encodes the program into a file that can be read by randOS')
    print('  encode-as-is: like the encode option, but for programs that run with pyhton')
    print('  genkeypair: generate a public/private keypair supported for this purpose (required to build applications)')
    exit()
option = sys.argv[1]

if option == 'encode':
    print('Encoding file')
    privatekey = None
    codelines = None
    if len(sys.argv) < 6:
        print('Run: python3.13 encodeSoftware.py encode [PRIVATEKEY] [INPUT] [OUTPUT] [PUBLIC KEY] [VERISON INT INCREMENT]?')
        exit()
    with open(sys.argv[2], 'rb') as privatekeyfile:
        privatekey = privatekeyfile.read()
    with open(sys.argv[3], 'r') as inputfile:
        codelines = inputfile.readlines()
    pycode = ''
    perms = []
    for line in codelines:
        lines = line.split(' ')
        if lines[0] == 'PERMISSIONS':
            codelines.remove(line)
            newperms = lines[1].split(',')
            for perm in newperms:
                perms.append(perm.strip())
        else:
            pycode = pycode + '\n' + line
    """for line in codelines:
        linesplit = line.split(' ')
        pyline = ''
        if linesplit[0] == 'PERMISSIONS':
            newperms = linesplit[1].split(',')
            for perm in newperms:
                perms.append(perm)
        elif linesplit[0] == 'VAR':
            pyline = linesplit[1] + ' = testValueOf(' + line.split(' ',3)[3] + ', cmdPerms)'
        elif linesplit[0] == 'OUT':
            pyline = 'print('+ line.split(' ', 1)[1] +')'
        pycode = pycode + '\n' + pyline"""
    print('Pycode:\n' + pycode)
    # Get imports
    interpretationInstance = interpreter.InterpretationInstance({}, {})
    pycodeLexed = interpretationInstance.lex(pycode)
    REGEX_IMPORT = re.compile(r'''^\s*import ([\s\S]+)\s*$''')
    while True:
        stop = True
        for pyline in pycodeLexed:
            n = REGEX_IMPORT.match(pyline)
            if n:
                path_of_main = Path(sys.argv[3])
                path = (path_of_main.parent / n.group(1).strip()).resolve()
                if not os.path.exists(path):
                    raise Exception(f'No such file {path}')
                with open(path, 'r') as file:
                    if type(file) == str:
                        pycode.replace(f'import {n.group(1)}', file)
                    else:
                        pycode.replace(f'import {n.group(1)}', file)
        for pyline in pycodeLexed:
            if REGEX_IMPORT.match(pyline):
                stop = False
        if stop:
            break
    pycode = base64.b64encode(pycode.encode())
    pycodehash = hashlib.sha256(pycode).hexdigest()
    # Load the private key (handle encrypted or non-encrypted keys)
    try:
        private_key = serialization.load_pem_private_key(privatekey, password=None)
    except TypeError:
        password = getpass.getpass("Enter the password for the private key: ").encode()
        private_key = serialization.load_pem_private_key(privatekey, password=password)

    # Sign the hash with the private key
    signature = private_key.sign(
        pycodehash.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )

    # Validate the signature
    with open(sys.argv[5], 'rb') as publickeyfile:
        publickey = publickeyfile.read()
    public_key = serialization.load_pem_public_key(publickey)

    try:
        public_key.verify(
            signature,
            pycodehash.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        print("Signature validation successful.")
    except Exception as e:
        print(f"Signature validation failed: {e}")
        
    versionInt = 0
    if os.path.exists(sys.argv[4]):
        with open(sys.argv[4], 'r') as outputfile:
            if type(outputfile) != 'str':
                outputfile = outputfile.read()
            ofj = json.loads(outputfile)
            if ofj:
                versionInc = 1
                if len(sys.argv) >= 7:
                    versionInc = int(sys.argv[6])
                if 'version-int' in ofj:
                    versionInt = ofj['version-int'] + versionInc
    elif len(sys.argv) >= 7:
        versionInt = int(sys.argv[6])

    # Save the signature and hashed code to the output file
    out = {
        'publickey': base64.b64encode(publickey).decode(),
        'pubkeyhash': hashlib.sha256(publickey).hexdigest(),
        'permissions': perms,
        'code': pycode.decode(),
        'signature': base64.b64encode(signature).decode(),
        'version-int': versionInt
    }
    print(json.dumps(out, indent=4))
    with open(sys.argv[4], 'w') as outputfile:
        json.dump(out, outputfile, indent=4)
    print("Encoded and signed output saved.")
elif option == 'encode-as-is':
    print('Encoding file')
    privatekey = None
    pycode: str = ''
    if len(sys.argv) < 6:
        print('Run: python3.13 encodeSoftware.py encode-as-is [PRIVATEKEY] [INPUT] [OUTPUT] [PUBLIC KEY]')
        exit()
    with open(sys.argv[2], 'rb') as privatekeyfile:
        privatekey = privatekeyfile.read()
    with open(sys.argv[3], 'r') as inputfile:
        if isinstance(inputfile, str):
            pycode = inputfile
        else:
            pycode = inputfile.read()
    perms = ['sudo.runAsIs']
    print('Pycode:\n' + pycode)
    pycode = base64.b64encode(pycode.encode())
    pycodehash = hashlib.sha256(pycode).hexdigest()
    # Load the private key (handle encrypted or non-encrypted keys)
    try:
        private_key = serialization.load_pem_private_key(privatekey, password=None)
    except TypeError:
        password = getpass.getpass("Enter the password for the private key: ").encode()
        private_key = serialization.load_pem_private_key(privatekey, password=password)

    # Sign the hash with the private key
    signature = private_key.sign(
        pycodehash.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )

    # Validate the signature
    with open(sys.argv[5], 'rb') as publickeyfile:
        publickey = publickeyfile.read()
    public_key = serialization.load_pem_public_key(publickey)

    try:
        public_key.verify(
            signature,
            pycodehash.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        print("Signature validation successful.")
    except Exception as e:
        print(f"Signature validation failed: {e}")

    # Save the signature and hashed code to the output file
    out = {
        'publickey': base64.b64encode(publickey).decode(),
        'pubkeyhash': hashlib.sha256(publickey).hexdigest(),
        'permissions': perms,
        'code': pycode.decode(),
        'signature': base64.b64encode(signature).decode(),
    }
    print(json.dumps(out, indent=4))
    with open(sys.argv[4], 'w') as outputfile:
        json.dump(out, outputfile, indent=4)
    print("Encoded and signed output saved.")
elif option == 'genkeypair':
    print('Generating a new keypair')
    privateKeyFilename = None
    publicKeyFilename = None
    if len(sys.argv) < 4:
        print('Filenames not specified. Run: python3.13 encodeSoftware.py genkeypair [PRIVATE KEY FILENAME] [PUBLIC KEY FILENAME]')
        exit()
    else:
        privateKeyFilename = sys.argv[2]
        publicKeyFilename = sys.argv[3]

    # Ask if the user wants to add a password to the private key
    password = getpass.getpass('Enter a password for the private key (or leave blank for none): ')
    if not password == '':
        password = password.encode()
        encryption = serialization.BestAvailableEncryption(password)
    else:
        encryption = serialization.NoEncryption()

    # Generate RSA key pair
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    public_key = private_key.public_key()

    # Save the private key to a file
    with open(privateKeyFilename, 'wb') as private_file:
        private_file.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=encryption  # Password protection
            )
        )

    # Save the public key to a file
    with open(publicKeyFilename, 'wb') as public_file:
        public_file.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )

    print(f"Keypair generated and saved to {privateKeyFilename} and {publicKeyFilename} for private and public keys respectively")
else:
    print('To make a new keypair, run: python3.13 encodeSoftware.py genkeypair [PRIVATE KEY FILENAME] [PUBLIC KEY FILENAME]')
