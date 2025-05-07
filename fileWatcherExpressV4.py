import subprocess
import sys
from dotenv import load_dotenv
import os
from datetime import datetime
import glob
import shutil

from fwLibary import diffChecker
from helpers import helper

""" PENDING SECTION

    # ===============[LOG SETTINGS] =========================
    exec >> /home/ubuntu/logs/filewatcher.log.`date +"%Y.%m.%d"`
    exec 2>&1

    echo "running filewatcher `date`"

    # ===============[ENVIRONMENT SETTINGS] =========================
    ## this line sources the environment variables from `fileWatcherEnv.sh` file
    ## `fileWatcherEnv.sh` needs to present on sys location.
    . /home/ubuntu/allegoAdmin/scripts/fileWatcherEnv.sh

    ## Import Helper Functions
    . /home/ubuntu/allegoAdmin/scripts/fwLibrary.sh

"""
## check for override of env vars passed in as an arg
    # Load environment variables from file if given in arg 1 else default .env file.

env_file = '.env.dev'
if len(sys.argv) > 1:
    env_file = sys.argv[1] 
    load_dotenv(dotenv_path=env_file, override=True)
    print(f'LOG: FWExpressV4.py: Loaded env file from arg: {env_file}' )
else:
    load_dotenv(dotenv_path=env_file, override=True)
    print(f'LOG: FWExpressV4.py: loaded env file from default: {env_file}')

## Default threshold if not set to 101 in order to ignore threshold functions
    # Logic Plan:
        # Read env var THRESHOLD.
        # If not set ➔ default to 101.
        # Else ➔ check if it’s a valid positive integer.
        # If invalid ➔ print error or fallback to default
threshold = os.environ.get('myTHRESHOLD')
if not threshold:
    print("LOG: FWExpressV4.py: threshold is unset, defaulting to 101")
    threshold = 101
else:
    print(f"LOG: FWExpressV4.py: threshold is set to '{threshold}'")
    # Error Handling: Validate if it's a number
    try:
        threshold = int(threshold)
        if threshold <= 0:
            print("Error LOG: FWExpressV4.py: threshold must be a positive integer. Defaulting to 101.")
            threshold = 101
    except ValueError:
        print("Error LOG: FWExpressV4.py: threshold must be a valid integer. Defaulting to 101.")
        threshold = 101

""" PENDING SECTION

exec >> /home/ubuntu/logs/filewatcher.log.${COMPANY[$index]}.`date +"%Y.%m.%d"`
exec 2>&1

"""

companies = os.environ.get('COMPANY').split(',')
companiesId = os.environ.get('COMPANY_ID').split(',')
source_parent_dir = os.environ.get('SOURCE_P_DIR').strip()
target_parent_dir = os.environ.get('TARGET_P_DIR').strip()
number_of_companies = os.environ.get('NUMBER_OF_COMPANIES').strip()

# getting the number of companies from the environment variable and checking if it is a valid integer.
try:
    number_of_companies = int(number_of_companies)
except ValueError:
    print("Error LOG: FWExpressV4.py: NUMBER_OF_COMPANIES must be an integer.")
    # number_of_companies = len(companies)
    sys.exit(1)

# Error Handling: Check if number_of_companies is a positive integer
if number_of_companies <= 0:
    print("Error LOG: FWExpressV4.py: NUMBER_OF_COMPANIES must be a positive integer.")
    sys.exit(1)

# 	while [ $index -lt $NUMBER_OF_COMPANIES ]
index = 0
while index < number_of_companies:
    # brefore processing, check if the index is within bounds because if the number of companies is less than the number of company IDs, it will throw an error. 
    if index >= len(companies) and index >= len(companiesId):
        print(f"Error LOG: FWExpressV4.py:  Index out of bounds for companies or companiesId.")
        break

    # Process each company
    company = companies[index].strip()
    company_id = companiesId[index].strip()
    print(f'========================== {company} ======================')
    print(f"LOG: FWExpressV4.py: Checking {index} {datetime.now().strftime('%a %b %d %H:%M:%S %Z %Y')}")
    print(f'LOG: FWExpressV4.py: company is:{company}')
    print(f'LOG: FWExpressV4.py: company id is:{company_id}')

    # ASSUMPTION: in production, we have _compete file at ${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/ location.
        # but in dev, we have to create the directory and file too.
    upload_dir = f'{source_parent_dir}/{company}/UPLOAD'
    helper.makeCompleteFile(company, upload_dir)

    if os.path.exists(upload_dir):
        print(f'LOG: FWExpressV4.py: {upload_dir} exists')
        matched_files = [os.path.basename(file).strip() for file in glob.glob(f'{upload_dir}/*_complete')]
        print(f'LOG: FWExpressV4.py: matched files are: {matched_files}')

        offset = -9
        for file in matched_files:
            baseName = os.path.basename(file)
            # gettigng prefix of the file name
            prefix = baseName[:offset]
            print(f'LOG: FWExpressV4.py: {file} and prefix is: {prefix}')

            # from this prefix i get userCSV.csv file 
            userCSV = f'{upload_dir}/{prefix}_users.csv'
            
            # ASSUMPTION: I HAVE THIS FILE IN THIS UPLOAD DIR.
                # BUT FOR DEV I NEED TO MAKE SURE IT IS THERE
            if not os.path.exists(userCSV):
                open(userCSV, 'w').close()
                print(f'LOG: FWExpressV4.py: file {os.path.basename(userCSV)} created at {userCSV}')
            else:
                print(f'LOG: FWExpressV4.py: file {os.path.basename(userCSV)} already exists at {userCSV}')

            # UTF-8 Check (equivalent to shell's iconv)
            if company_id in (218, 120):
                print("LOG: FWExpressV4.py: Checking UTF8 format")
                try:
                    with open(userCSV, 'r', encoding='utf-8') as f:
                        f.read()  # Try reading entire file
                        print("LOG: FWExpressV4.py: UTF-8 Check Passed")
                except UnicodeDecodeError:
                    print("Error LOG: FWExpressV4.py: UTF-8 Formatting has invalid characters; exiting")
                    sys.exit(1)
            # FileWatcherExpress updates are part of AAR-1339
            # FileWatcherExpressEnhancement Step 1

                        #  target dir path check 
            target_dir = f'{target_parent_dir}/{company}'
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
                print(f'LOG: FWExpressV4.py: Directory {target_dir} created')
            else:
                print(f'LOG: FWExpressV4.py: Directory {target_dir} already exists')

                
            prevCheck = f'{target_parent_dir}/{company}/users.csv'
            prevManualCheck = f'{target_parent_dir}/{company}/manual_users.csv'

            print(f'LOG: FWExpressV4.py: prev check files : \n {prevCheck} \n {prevManualCheck}')

            # very first handling legacy case ,  we have flagLegacy var above for this.
            if len(sys.argv) > 2:
                if sys.argv[2].lower() == 'legacy':
                    print("LOG: FWExpressV4.py: Legacy mode enabled")
                    threshold = 101
                    prevCheck = f'{target_parent_dir}/{company}/blank.csv'
                    prevManualCheck = f'{target_parent_dir}/{company}/manual_blank.csv'

                    if not os.path.exists(prevCheck): open(prevCheck, 'w').close()
                    if not os.path.exists(prevManualCheck): open(prevManualCheck, 'w').close()

                    print(f'LOG: FWExpressV4.py: file {os.path.basename(prevCheck)} created at {prevCheck}')
                    print(f'LOG: FWExpressV4.py: file {os.path.basename(prevManualCheck)} created at {prevManualCheck}')
                    print("LOG: FWExpressV4.py: Legacy mode done")
            else:
                print("LOG: FWExpressV4.py: Legacy mode not enabled")

            # here i need to check if the users.csv file exists in target dir if not then i need to create it
                # when AUP have first time run then it has no users.csv file


            # check if the prevCheck file exists
            if not os.path.exists(prevCheck):
                open(prevCheck, 'w').close()
                print(f'LOG: FWExpressV4.py: file {os.path.basename(prevCheck)} created at {prevCheck}')
            else:
                print(f'LOG: FWExpressV4.py: file {os.path.basename(prevCheck)} already exists at {prevCheck}')
            
            # check if the prevManualCheck file exists
            if not os.path.exists(prevManualCheck):
                open(prevManualCheck, 'w').close()
                print(f'LOG: FWExpressV4.py: file {os.path.basename(prevManualCheck)} created at {prevManualCheck}')
            else:
                print(f'LOG: FWExpressV4.py: file {os.path.basename(prevManualCheck)} already exists at {prevManualCheck}')

            # check if previous.csv file exists which is the copy of users.csv file
            prevFile = f'{target_parent_dir}/{company}/previous.csv'
            if not os.path.exists(prevFile):
                open(prevFile, 'w').close()
                print(f'LOG: FWExpressV4.py: file {os.path.basename(prevFile)} created at {prevFile}')
            else:
                print(f'LOG: FWExpressV4.py: file {os.path.basename(prevFile)} already exists at {prevFile}')
            
            shutil.copy2(prevCheck, prevFile)

            # Upload usersCSV file to channel in AUP Company
            script_path = 'AUP/'
            script_name = 'AUPChannelUploader.py'
            py_path = 'python3'            
            # define the full path to the script
            script_full_path = os.path.join(script_path, script_name)
            channelid = '1' # just to ignore warning, this is temporary value.
            
            # define the command to run the script
            cmd = [py_path, script_full_path, channelid, userCSV]
            # just run the command, not carrying about the output.
            try: 
                subprocess.run(cmd)
                print(f" LOG: FWExpressV4.py: {script_name} script executed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"Error LOG: FWExpressV4.py: executing script: {e}")

            if threshold < 101:
                print(f"LOG: FWExpressV4.py: threshold is less than 101")
                server_location = 'ap-south-1' # just to ignore warning, this is temporary value.
                percent = diffChecker(threshold, server_location, prevFile, userCSV, company_id)
            else:
                print("LOG: FWExpressV4.py: threshold is greater than 101")

    print("=========================================================")
    index += 1