import requests # type: ignore
import sys

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

if len(sys.argv) <= 1:
    print('Specify an option')
    print('install/i: installer i [program name]; can use -f to install without validation; -t to install and trust; -y to pre-confirm')
    print('trust: installer trust [public key URI] [name]; can use -y to pre-confirm')
    print('revoke-trust/rt: installer rt [name]; can use -y to preconfirm')
    print('uninstall: installer uninstall [program name]; can use -y to pre-confirm')

if sys.argv[0] == 'install' or sys.argv[0] == 'i':
    if len(sys.argv) <= 2:
        print('Must specify a program to install. Use as follows:')
        print('install/i: installer i [program name]; can use -f to install without validation; -t to install and trust; -y to pre-confirm')
        exit()
    progname = sys.argv[1]