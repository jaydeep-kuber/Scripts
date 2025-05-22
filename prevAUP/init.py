import shutil
import os
from datetime import datetime 
from dotenv import load_dotenv
import sys

def initFileStructure(envFile, copyCsv=0):

    load_dotenv(dotenv_path=envFile)
    print(f' Loaded env file from arg: {envFile}' )
    
    companies = os.environ.get('COMPANY').split(',')
    source_parent_dir = os.environ.get('SOURCE_PARENT_DIR').strip()
    target_parent_dir = os.environ.get('TARGET_PARENT_DIR').strip()
    allego_home = os.environ.get('ALLEGO_HOME').strip()
    
    if not os.path.exists(allego_home):
        os.makedirs(allego_home, exist_ok=True)
        print(f'your allegoHome: {allego_home}')

    scriptDirInTarget = os.path.join(allego_home, 'scripts','channels')
    script_file = os.path.join(scriptDirInTarget, 'AUPChannelUploader.py')
    if not os.path.exists(scriptDirInTarget):
        os.makedirs(scriptDirInTarget)
        print(f'Created: {scriptDirInTarget}')
    open(script_file, 'w').close()

    if not os.path.exists(f'{allego_home}/scripts'):
        os.makedirs(f'{allego_home}', exist_ok=True)
    open(f'{allego_home}/scripts/setCompanyOnHold.py', 'w').close()

    importSh = os.path.join(allego_home, 'scripts' , 'import.sh')
    if not os.path.exists(importSh):
        open(importSh, 'w').close()
        print(f'Created: {importSh}')

    # Create file prefix with current date in YYYYMMDD format
    filePrefix = datetime.now().strftime("%Y%m%d")
    _completeFileName =  f'{filePrefix}_complete'
    # make src + company and UPLOAD dir dirs
    for cmp in companies:
        companyDirInSrc = os.path.join(source_parent_dir, cmp.strip())
        os.makedirs(companyDirInSrc, exist_ok=True)
        print(f'Created: {companyDirInSrc} ')

        companyDirInTarg = os.path.join(target_parent_dir, cmp.strip())
        os.makedirs(companyDirInTarg, exist_ok=True)
        print(f'Created: {companyDirInTarg} ')

        #UPLAOD 
        uploadDirInSrc = os.path.join(companyDirInSrc, 'UPLOAD')
        os.makedirs(uploadDirInSrc, exist_ok=True)
        print(f'Created: {uploadDirInSrc} ')

        # creting compete file if not exists
        completeFile = os.path.join(uploadDirInSrc, _completeFileName)
        if not os.path.exists(completeFile):
            open(completeFile, 'w').close()
            print(f'_complete Created: {completeFile} ')
        else: 
            print(f'_complete already exists: {completeFile} ')
        
        csvFileName= f'{filePrefix}_users.csv'
        csvFileInScr = os.path.join(uploadDirInSrc, csvFileName)

        # making csv file if it is not there
        if not os.path.exists(csvFileInScr):
            open(csvFileInScr, 'w').close()
            print(f'Csv file Created: {csvFileInScr} ') 
        else:
            print(f'Csv file already exists: {csvFileInScr} ')
        
        addUpdateCSV = os.path.join(target_parent_dir, cmp, 'addUpdate.csv')
        if not os.path.exists(addUpdateCSV):
            open(addUpdateCSV, 'w').close()
            print(f'Created: {addUpdateCSV} ')
        
        disableCSV = os.path.join(target_parent_dir, cmp, 'disable.csv')
        if not os.path.exists(disableCSV):
            open(disableCSV, 'w').close()
            print(f'Created: {disableCSV} ')

        stageScript = os.path.join(allego_home, 'conf', 'import' , 'customer' , cmp , f'setup_{cmp}.py')
        stageDirPath = os.path.join(allego_home, 'conf', 'import' , 'customer' , cmp)
        os.makedirs(stageDirPath, exist_ok=True)
        print(f'Created: {stageDirPath}')
        if not os.path.exists(stageScript):
            open(stageScript,'w').close()
            print(f' scr Created: {os.path.basename(stageScript)}')

        dataCsv = './orgData.csv'
        if copyCsv:
            # filling _completeFile
            shutil.copy2(dataCsv,completeFile)
            print(f'Copied: {dataCsv} to {completeFile}')
            # fillin csv file 
            shutil.copy2(dataCsv, csvFileInScr)
            print(f'Copied: {dataCsv} to {csvFileInScr}')

args = len(sys.argv)        
if args > 1:
    envFile = sys.argv[1]
    initFileStructure(envFile)
else:
    print("Please provide an env file as an argument.")
    sys.exit(1)

if args > 2:
    flag = sys.argv[2]
    initFileStructure(envFile, copyCsv=flag)
else: 
    print("to copy data provide second arg as 1")