import os
import sys
import glob
import time
import subprocess
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env.dev')
source_parent_dir = os.environ.get('SOURCE_PARENT_DIR').strip()

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


def gpg_decrypt(inFile: str, outFile: str, company: str, lggr=None):
    """
    Decrypt a GPG-encrypted file.
    """
    if lggr:
        lg = lggr
        lg.info("logger set for -> gpg decrpyt")
    fileName = os.path.basename(inFile)
    print(f'filename: {fileName}')
    prefix = fileName[:-9]
    print(f'prefix: {prefix}') 

    cmd = [
        'gpg', '--output' , outFile, inFile
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"Error during decryption: {e}")
        sys.exit(1)

#   touch /home/tiaa/UPLOAD/${prefix}_tiaa_complete
    upload_dir = os.path.join(source_parent_dir, company, 'UPLOAD')
    touchFileName = f'{prefix}_{company}_complete'
    touchFile = os.path.join(upload_dir, touchFileName)
    if not os.path.exists(touchFile):
        open(touchFile, 'w').close()

#   mv /home/tiaa/UPLOAD/${prefix}_users.csv /home/tiaa/archive
    archiveDir = os.path.join(source_parent_dir, company, 'archive')
    if not os.path.exists(archiveDir):
        os.makedirs(archiveDir)
    subprocess.run([
        'mv',
        os.path.join(upload_dir, f'{prefix}_users.csv'),
        archiveDir
    ])

#   rm /home/tiaa/UPLOAD/${prefix}_complete
    os.remove(os.path.join(upload_dir, f'{prefix}_complete'))

    return outFile

def pgp_decrypt(inFile: str, outFile: str, company: str, lggr=None):
    """
    Decrypt a PGP-encrypted file.
    """
    
    if lggr:
        lg = lggr
        lg.info("logger set for -> pgp decrpyt")
    fileName = os.path.basename(inFile)
    print(f'filename: {fileName}')
    prefix = fileName[:-17]
    print(f'prefix: {prefix}') 

    cmd = [
        'gpg', '--output' , outFile, inFile
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"Error during decryption: {e}")
        sys.exit(1)
    
    upload_dir = os.path.join(source_parent_dir, company, 'UPLOAD')
    touchFileName = f'{prefix}_complete'
    touchFile = os.path.join(upload_dir, touchFileName)
    
    #   touch /home/kronos/UPLOAD/${prefix}_complete
    if not os.path.exists(touchFile):
        open(touchFile, 'w').close()

    #   mv /home/kronos/UPLOAD/*.pgp /home/kronos/archive
    archiveDir = os.path.join(source_parent_dir, company, 'archive')
    if not os.path.exists(archiveDir):
        os.makedirs(archiveDir)
    
    pgpFiles = glob.glob(os.path.join(upload_dir, '*.pgp'))
    subprocess.run([
        'mv',
        pgpFiles,
        archiveDir
    ])