import subprocess
import sys
from dotenv import load_dotenv
import os
from datetime import datetime
import glob
import shutil

from utils import custom_logger
from fwLibary import diffChecker, dos2unix
from helpers import helper


def compare_files(previous_file, current_file, addupdate_file, disable_file):
    try:
        # Read and sort previous file lines
        with open(previous_file, 'r') as f:
            prev_lines = sorted(f.readlines())
            
        # Read and sort current file lines    
        with open(current_file, 'r') as f:
            curr_lines = sorted(f.readlines())
            
        # Find lines in current but not in previous (addUpdate)
        with open(addupdate_file, 'w') as f:
            for line in curr_lines:
                if line not in prev_lines:
                    f.write(line)
                    
        # Find lines in previous but not in current (disable)            
        with open(disable_file, 'w') as f:
            for line in prev_lines:
                if line not in curr_lines:
                    f.write(line)
                    
        print(f"LOG: Generated {addupdate_file} and {disable_file}")
        
    except Exception as e:
        print(f"Error comparing files: {e}")
        return False
    
    return True

################################################################################################

env_file = '.env.dev'

scriptName  = os.path.basename(__file__)
loggers = {}

if len(sys.argv) > 1:
    env_file = sys.argv[1] 
    load_dotenv(dotenv_path=env_file, override=True)
    print(f' Loaded env file from arg: {env_file}' )
else:
    load_dotenv(dotenv_path=env_file, override=True)
    print(f' loaded env file from default: {env_file}')

companies = os.environ.get('COMPANY').split(',')
companiesId = os.environ.get('COMPANY_ID').split(',')
source_parent_dir = os.environ.get('SOURCE_P_DIR').strip()
target_parent_dir = os.environ.get('TARGET_P_DIR').strip()
number_of_companies = os.environ.get('NUMBER_OF_COMPANIES').strip()
threshold = os.environ.get('myTHRESHOLD)')

if not threshold:
    print(" threshold is unset, defaulting to 101")
    threshold = 101
else:
    print(f" threshold is set to '{threshold}'")
    try:
        threshold = int(threshold)
        if threshold <= 0:
            print("Error  threshold must be a positive integer. Defaulting to 101.")
            threshold = 101
    except ValueError:
        print("Error  threshold must be a valid integer. Defaulting to 101.")
        threshold = 101

# getting the number of companies from the environment variable and checking if it is a valid integer.
try:
    number_of_companies = int(number_of_companies)
except ValueError:
    print("Error  NUMBER_OF_COMPANIES must be an integer.")
    # number_of_companies = len(companies)
    sys.exit(1)

# Error Handling: Check if number_of_companies is a positive integer
if number_of_companies <= 0:
    print("Error  NUMBER_OF_COMPANIES must be a positive integer.")
    sys.exit(1)

# 	while [ $index -lt $NUMBER_OF_COMPANIES ]
index = 0
while index < number_of_companies:
    # brefore processing, check if the index is within bounds because if the number of companies is less than the number of company IDs, it will throw an error. 
    if index >= len(companies) and index >= len(companiesId):
        print(f"Error   Index out of bounds for companies or companiesId.")
        break

    # Process each company
    company = companies[index].strip()
    company_id = companiesId[index].strip()
    lg = custom_logger.setup_logger(scriptName, company)
    lg.info(f'logger setted up for - {company} ')

    lg.info(f'========================== {company} ======================')
    lg.info(f" Checking {index} {datetime.now().strftime('%a %b %d %H:%M:%S %Z %Y')}")
    lg.info(f' company is:{company}')
    lg.info(f' company id is:{company_id}')

    # logger set up 
    # ASSUMPTION: in production, we have _compete file at ${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/ location.
        # but in dev, we have to create the directory and file too.
    upload_dir = f'{source_parent_dir}/{company}/UPLOAD'
    helper.makeCompleteFile(company, upload_dir)

    if os.path.exists(upload_dir):
        lg.info(f'{upload_dir} exists')
        matched_files = [os.path.basename(file).strip() for file in glob.glob(f'{upload_dir}/*_complete')]
        lg.info(f'matched files are: {matched_files}')

        offset = -9
        for file in matched_files:
            baseName = os.path.basename(file)
            # gettigng prefix of the file name
            prefix = baseName[:offset]
            lg.info(f' {file} and prefix is: {prefix}')

            # from this prefix i get usersCSV.csv file 
            usersCSV = f'{upload_dir}/{prefix}_users.csv'
            
            # ASSUMPTION: I HAVE THIS FILE IN THIS UPLOAD DIR.
                # BUT FOR DEV I NEED TO MAKE SURE IT IS THERE
            if not os.path.exists(usersCSV):
                open(usersCSV, 'w').close()
                lg.info(f' file {os.path.basename(usersCSV)} created at {usersCSV}')
            else:
                lg.info(f' file {os.path.basename(usersCSV)} already exists at {usersCSV}')

            # UTF-8 Check (equivalent to shell's iconv)
            if company_id in (218, 120):
                lg.info(" Checking UTF8 format")
                try:
                    with open(usersCSV, 'r', encoding='utf-8') as f:
                        f.read()  # Try reading entire file
                        lg.info(" UTF-8 Check Passed")
                except UnicodeDecodeError:
                    lg.info(" UTF-8 Formatting has invalid characters; exiting")
                    sys.exit(1)
            # FileWatcherExpress updates are part of AAR-1339
            # FileWatcherExpressEnhancement Step 1

                        #  target dir path check 
            targetCompanyDir = f'{target_parent_dir}/{company}'
            if not os.path.exists(targetCompanyDir):
                os.makedirs(targetCompanyDir)
                lg.info(f' Directory {targetCompanyDir} created')
            else:
                lg.info(f' Directory {targetCompanyDir} already exists')

                
            prevCheck = f'{targetCompanyDir}/users.csv'
            prevManualCheck = f'{targetCompanyDir}/manual_users.csv'

            lg.info(f' prev check files : \n {prevCheck} \n {prevManualCheck}')

            # very first handling legacy case ,  we have flagLegacy var above for this.
            if len(sys.argv) > 2:
                if sys.argv[2].lower() == 'legacy':
                    lg.info(" Legacy mode enabled")
                    threshold = 101
                    prevCheck = f'{targetCompanyDir}/blank.csv'
                    prevManualCheck = f'{targetCompanyDir}/manual_blank.csv'

                    if not os.path.exists(prevCheck): open(prevCheck, 'w').close()
                    if not os.path.exists(prevManualCheck): open(prevManualCheck, 'w').close()

                    lg.info(f' file {os.path.basename(prevCheck)} created at {prevCheck}')
                    lg.info(f' file {os.path.basename(prevManualCheck)} created at {prevManualCheck}')
                    lg.info(" Legacy mode done")
            else:
                lg.info(" Legacy mode not enabled")

            # here i need to check if the users.csv file exists in target dir if not then i need to create it
                # when AUP have first time run then it has no users.csv file


            # check if the prevCheck file exists
            if not os.path.exists(prevCheck):
                open(prevCheck, 'w').close()
                lg.info(f' file {os.path.basename(prevCheck)} created at {prevCheck}')
            else:
                lg.info(f' file {os.path.basename(prevCheck)} already exists at {prevCheck}')
            
            # check if the prevManualCheck file exists
            if not os.path.exists(prevManualCheck):
                open(prevManualCheck, 'w').close()
                lg.info(f' file {os.path.basename(prevManualCheck)} created at {prevManualCheck}')
            else:
                lg.info(f' file {os.path.basename(prevManualCheck)} already exists at {prevManualCheck}')

            # check if previous.csv file exists which is the copy of users.csv file
            prevFile = f'{targetCompanyDir}/previous.csv'
            if not os.path.exists(prevFile):
                open(prevFile, 'w').close()
                lg.info(f' file {os.path.basename(prevFile)} created at {prevFile}')
            else:
                lg.info(f' file {os.path.basename(prevFile)} already exists at {prevFile}')
            
            shutil.copy2(prevCheck, prevFile)

            # Upload usersCSV file to channel in AUP Company
            script_path = 'AUP/'
            script_name = 'AUPChannelUploader.py'
            py_path = 'python3'            
            # define the full path to the script
            script_full_path = os.path.join(script_path, script_name)
            channelid = '1' # just to ignore warning, this is temporary value.
            
            # define the command to run the script
            cmd = [py_path, script_full_path, channelid, usersCSV]
            # just run the command, not carrying about the output.
            try: 
                subprocess.run(cmd)
                lg.info(f"  {script_name} script executed successfully.")
            except subprocess.CalledProcessError as e:
                lg.info(f"Error  executing script: {e}")

            if threshold < 101:
                lg.info(f" threshold is less than 101")
                server_location = 'ap-south-1' # just to ignore warning, this is temporary value.
                percent = diffChecker(threshold, server_location, prevFile, usersCSV, company_id)
                if percent == 1 :
                    lg.info(f" diffChecker returned 1, Diff checker stopped AUP")
				    # remove _complete file
                    rmfile = f"{upload_dir}/{prefix}_complete"
                    os.remove(rmfile)
                    
                    archive_dir = 'aupFailureArchive'
                    archive_dir_loc = f'{target_parent_dir}/{archive_dir}'
                    if not os.path.exists(archive_dir_loc):
                        os.makedirs(archive_dir_loc)
                        lg.info(f" ARCHIVE DIR CREAED")

                    archFile = f"{archive_dir_loc}/{prefix}_complete"
                    cvsfile = f'{archive_dir_loc}/{prefix}_users.csv'
                    # check if archive file is already there
                    if os.path.isfile(cvsfile):
                        os.remove(cvsfile)    
                    shutil.move(usersCSV, archive_dir_loc)

                    lg.info(f"{usersCSV} file moved to archive location")
                    sys.exit(1)
                else:
                    lg.info(" percent is 0")
            else:
                lg.info(" Diffchecker passed!!")

            # Copy previous manual_users.csv 
 			#	(or blank one you just touched, or blank one you forced in there), 
 			#	as manual_previous.csv
            if os.path.exists(prevManualCheck):
                shutil.copy2(prevManualCheck, f'{targetCompanyDir}/manual_previous.csv')
                lg.info(f' file {os.path.basename(prevManualCheck)} copied to {targetCompanyDir}/manual_previous.csv')
            else:
                shutil.copy2(prevCheck, f'{targetCompanyDir}/manual_previous.csv')
                lg.info(f' file {os.path.basename(prevCheck)} copied to {targetCompanyDir}/manual_previous.csv')

            # end of STEP-1
            
            # Create expected users.csv from new file
            # Run dos2unix here to clean up hidden character else the match will fail
            # usersCSV set further up for UTF8 checks

            if os.path.isfile(usersCSV):
                lg.info(f' file {os.path.basename(usersCSV)} exists at {usersCSV}')
                # run dos2unix on the file
                # rename user file
                os.makedirs(f'{targetCompanyDir}/', exist_ok=True) # make sure the target dir exists
                fileLoc = f'{targetCompanyDir}/users.csv.{prefix}'
                shutil.copy2(usersCSV,fileLoc)
                lg.info(f' file {os.path.basename(usersCSV)} moved to {fileLoc}')
                
                users_csv_clean = os.path.join(targetCompanyDir, 'users.csv')
                try:
                    with open(fileLoc, 'r') as infile, open(users_csv_clean, 'w', encoding='utf-8') as outfile:
                            next(infile)  # Skip header
                    for line in infile:
                        outfile.write(line)
                        lg.info(f"Header removed, saved clean file to {users_csv_clean}")
                except Exception as e:
                    lg.info(f"Error during header removal: {e}")
    
                dos2unix(usersCSV)
                lg.info(f' dos2unix run on {usersCSV}')
            
            addUpdateCSV = f'{targetCompanyDir}/addUpdate.csv'
            disableCSV = f'{targetCompanyDir}/disable.csv'

            mv_addUpdateCSV = f'{addUpdateCSV}.{prefix}'
            mv_disableCSV = f'{disableCSV}.{prefix}'
            
            # Create directory if it doesn't exist
            os.makedirs(targetCompanyDir, exist_ok=True)
            
            # Create files if they don't exist
            if not os.path.exists(addUpdateCSV):
                open(addUpdateCSV, 'w').close()
                lg.info(f' file {os.path.basename(addUpdateCSV)} created at {addUpdateCSV}')
            else:
                lg.info(f' file {os.path.basename(addUpdateCSV)} already exists at {addUpdateCSV}')
                
            if not os.path.exists(disableCSV):
                open(disableCSV, 'w').close() 
                lg.info(f' file {os.path.basename(disableCSV)} created at {disableCSV}')
            else:
                lg.info(f' file {os.path.basename(disableCSV)} already exists at {disableCSV}')
                
            if not os.path.exists(mv_addUpdateCSV):
                open(mv_addUpdateCSV, 'w').close()
                lg.info(f' file {os.path.basename(mv_addUpdateCSV)} created at {mv_addUpdateCSV}')
            else:
                lg.info(f' file {os.path.basename(mv_addUpdateCSV)} already exists at {mv_addUpdateCSV}')
                
            if not os.path.exists(mv_disableCSV):
                open(mv_disableCSV, 'w').close()
                lg.info(f' file {os.path.basename(mv_disableCSV)} created at {mv_disableCSV}')
            else:
                lg.info(f' file {os.path.basename(mv_disableCSV)} already exists at {mv_disableCSV}')              
            
            # Check if addUpdate.csv exists and move it with prefix
            if os.path.isfile(addUpdateCSV):
                shutil.copy2(addUpdateCSV, mv_addUpdateCSV)
                lg.info(f' file {os.path.basename(addUpdateCSV)} moved to {mv_addUpdateCSV}')   

            if os.path.isfile(disableCSV):
                shutil.copy2(disableCSV, mv_disableCSV)
                lg.info(f' file {os.path.basename(disableCSV)} moved to {mv_disableCSV}')

            # Compare sorted files to generate addUpdate.csv and disable.csv

            # Call function with file paths
            compare_files(prevFile, 
                f'{targetCompanyDir}/users.csv',
                f'{targetCompanyDir}/addUpdate.csv',
                f'{targetCompanyDir}/disable.csv')        

            groupsCSV=f'{source_parent_dir}/{company}/UPLOAD/{prefix}_groups.csv'
            if os.path.exists(groupsCSV):
                lg.info(f' file {os.path.basename(groupsCSV)} copied to {targetCompanyDir}/groups.csv')
            else:
                open(f'{targetCompanyDir}/{prefix}_groups.csv', 'w').close()
                lg.info(f' file groups.csv created at {targetCompanyDir}/groups.csv')
    lg.info("======================================================")
    print("=========================================================")
    index += 1