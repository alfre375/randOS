import requests # type: ignore
import sys
import os
import randosUtils
import json
import base64

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

if len(cmds) <= 1: # type: ignore
    print('Specify an option')
    print('install/i (installs a program): installer i [program name]; can use -f to install without validation; -t to install and trust; -y to pre-confirm')
    print('trust (trusts a new keypair): installer trust [public key URI] [name]; can use -y to pre-confirm')
    print('revoke-trust/rt (revokes trust for a keypair): installer rt [name]; can use -y to preconfirm')
    print('uninstall (deletes a program): installer uninstall [program name]; can use -y to pre-confirm')
    print('update (updates repository files): installer update')

if cmds[0] == 'install' or cmds[0] == 'i': # type: ignore
    if len(cmds) <= 2: # type: ignore
        print('Must specify a program to install. Use as follows:')
        print('install/i: installer i [program name]; -t to install and trust; -y to pre-confirm')
        exit()
    progname = cmds[1] # type: ignore
    if not os.path.exists('./files/cfg/proginstaller/repositories'):
        print('Repositories folder not found. Run installer update.')
        raise randosUtils.ExecFinishedEarly
    for repo in os.listdir('./files/cfg/proginstaller/repositories'):
        repoRelative = './files/cfg/proginstaller/repositories/' + repo
        repoData: dict = {}
        with open(repoRelative, 'r') as repoFile:
            if isinstance(repoFile, str):
                repoData = json.load(repoFile)
            else:
                repoData = json.load(repoFile.read())
        if not (progname in repoData['programs']):
            continue
        progVerison = repoData['programs'][progname]['version']
        progDownloadURI = repoData['programs'][progname]['downloads'][progVerison]
        if not '-y' in cmds: # type: ignore
            conf = input(f'Would you like to install version {progVerison} of {progname}? [Y/n]')
            if conf.lower() == 'n':
                print('Aborting.')
                raise randosUtils.ExecFinishedEarly
        if os.path.exists('./files/bin/' + progname):
            print('Old version found. Temporarily backing old version up.')
            os.rename('./files/bin/' + progname, './files/bin/' + progname + '.backup')
        try:
            downloadFile(progDownloadURI, './files/bin/' + progname)
            print('Download finished. Removing backup.')
            os.remove('./files/bin/' + progname + '.backup')
            if '-t' in cmds: # type: ignore
                pubkey = b''
                keyexists = False
                with open('./files/bin/' + progname, 'rb') as progfile:
                    progjson: dict = {}
                    if isinstance(progfile, str):
                        progjson = json.load(progfile)
                    else:
                        progjson = json.load(progfile.read())
                    pubkey = base64.b64decode(progjson['publickey'])
                    progfile.close()
                for key in os.listdir('./files/progpubkeys'):
                    with open('./files/progpubkeys/' + key, 'rb') as keyfile:
                        if keyfile.read() == pubkey:
                            keyexists = True
                            break
                if not keyexists:
                    keyfilename = input('Enter a name for the file for the public key (without the extension): ') + '.pem'
                    with open(keyfilename, 'wb') as keyfile:
                        keyfile.write(pubkey)
                        keyfile.close()
                else:
                    print('This public key is already trusted')
        except Exception:
            if os.path.exists('./files/bin/' + progname + '.backup'):
                print('Download failed. Restoring old version.')
                os.rename('./files/bin/' + progname + '.backup', './files/bin/' + progname)
                print('Restoration finished.')
            else:
                print('Download failed')