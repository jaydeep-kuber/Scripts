import os
import sys
import time
import subprocess
import json
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env.dev')

def getFileMetaData(filePath):

    if not os.path.exists(filePath):
        print(f"File does not exist at -> {filePath}")
        return
     
    print("File Name:", os.path.basename(filePath))
    stats = os.stat(filePath)
    print("Size:", stats.st_size)
    print("Permissions:", oct(stats.st_mode)[-3:])
    print("Last modified:", time.ctime(stats.st_mtime))
    print("Last accessed:", time.ctime(stats.st_atime))


def gpg_encrypt(filename: str, key_path: str, **kwargs):
    """
    Encrypt a file using GPG with symmetric encryption.

    :param filename: Path to the input file to encrypt.
    :param key_path: Path to the file containing the passphrase.
    :param kwargs: Optional GPG options as keyword arguments.
    """
    aglo = kwargs.get('aglo', 'AES256')
    output = kwargs.get('output', f'{filename}.gpg')
    extra_args = kwargs.get('extra_args', [])
    if not os.path.exists(key_path):
        print(f"Key file does not exist at -> {key_path}")
        return
    

    cmd = [
        'gpg', '--symmetric',
        '--cipher-algo', aglo,
        '--batch', '--yes',
        '--passphrase-file', key_path,
        '--output', output,
        *extra_args,
        filename
    ]

    subprocess.run(cmd, check=True)
    print("file saved at: ", output)
    return output


def gpg_decrypt(filename: str, key_path: str, **kwargs):
    """
    Decrypt a GPG-encrypted file using a passphrase.

    :param filename: Path to the encrypted .gpg file.
    :param key_path: Path to the file containing the passphrase.
    :param kwargs: Optional GPG options as keyword arguments.
    """
    outFile = kwargs.get('outFile', filename.replace('.gpg', ''))
    extra_args = kwargs.get('extra_args', [])

    cmd = [
        'gpg', '--batch', '--yes',
        '--passphrase-file', key_path,
        '--output', outFile,
        '--decrypt',
        *extra_args,
        filename
    ]

    subprocess.run(cmd, check=True)
    return outFile


def load_env():
    envJsonFilePath = 'envJson/fileWatcherEnv.json'

    with open(envJsonFilePath) as envJson:  
        env = json.load(envJson)
    print("env loaded")
    return env

if __name__ == "__main__":
    jsonEnv = load_env()
    # print(jsonEnv)
    # number_of_company = jsonEnv['number_of_company']
    # print(number_of_company)
    allCompJsonArry = jsonEnv['allCompanies']
    print(allCompJsonArry)
    print(allCompJsonArry[0].get('cmp_name'))