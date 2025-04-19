import base64
import hashlib
import json
import os
import sys
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

if len(sys.argv) <= 1:
    print('Please provide the file to check')
    exit()

# Load the JSON from the file
with open(sys.argv[1], 'r') as inputfile:
    data = json.load(inputfile)

# Restore the original values
publickey = base64.b64decode(data['publickey'])  # Decode Base64 to bytes
pubkeyhash = data['pubkeyhash']  # Already the original hash string
permissions = data['permissions']  # Already the original list
pycode = data['code']  # Already the original pycode 
signature = base64.b64decode(data['signature'])  # Decode Base64 to bytes

# Print the restored values
#print("Public Key:", publickey)
#print("Public Key Hash:", pubkeyhash)
#print("Permissions:", permissions)
#print("Python Code:", pycode)  # Keep Base64 encoding as-is 
#print("Signature:", signature)

correspondingKey = b''
for file in os.listdir('.'):
    if os.path.isfile(file):
        fc = b''
        with open('./'+file,'rb') as keyfile:
            fc = keyfile.read()
        if (fc == publickey):
            correspondingKey = fc
            print(file + ' is the corresponding key')

if hashlib.sha256(correspondingKey).hexdigest() == pubkeyhash:
    print('Public key hash valid')

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
    print("Signature validation successful.")
except Exception as e:
    print(f"Signature validation failed: {e}")