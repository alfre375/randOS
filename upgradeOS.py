from termcolor import colored

print('Checking system version...')
print(f'System running version {version}') #type: ignore
print('Getting latest version of randos.py')
import randosUtils
try:
    randosUtils.downloadFile('https://raw.githubusercontent.com/alfre375/randOS/refs/heads/main/randos.py', './randos.py')
except Exception:
    print(colored('ERROR_FATAL: Unable to download randos.py', 'red'))