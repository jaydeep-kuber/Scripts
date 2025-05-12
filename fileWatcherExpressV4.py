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

def compare_user_files(previous_file, current_file, add_update_file, disable_file):
    try:
        # Read and sort previous file
        with open(previous_file, 'r') as f:
            previous_lines = sorted(line.strip() for line in f if line.strip())

        # Read and sort current file
        with open(current_file, 'r') as f:
            current_lines = sorted(line.strip() for line in f if line.strip())

        # Use sets for comparison
        previous_set = set(previous_lines)
        current_set = set(current_lines)

        # Users in current but not in previous (add/updated users)
        add_update_lines = sorted(current_set - previous_set)

        # Users in previous but not in current (to disable)
        disable_lines = sorted(previous_set - current_set)

        # Write addUpdate.csv
        with open(add_update_file, 'w') as f:
            for line in add_update_lines:
                f.write(f"{line}\n")

        # Write disable.csv
        with open(disable_file, 'w') as f:
            for line in disable_lines:
                f.write(f"{line}\n")

        print(f" addUpdate written to: {add_update_file}")
        print(f" disable written to: {disable_file}")

    except FileNotFoundError as e:
        print(f" File not found: {e.filename}")
    except Exception as e:
        print(f" Unexpected error: {e}")


################################################################################################

import os

def remove_csv_header(src_file, dest_file, logger=None):
    """
    Copy content from src_file to dest_file skipping the first line (header).
    """
    try:
        if not os.path.isfile(src_file):
            print(f"Source file does not exist: {src_file}")
            return False

        if os.path.isfile(dest_file):
            print(f"Destination file already exists: {dest_file}")
            return False
        with open(src_file, 'r', errors='ignore') as infile, open(dest_file, 'w') as outfile:
            next(infile, None)  # skip header
            for line in infile:
                outfile.write(line)

        print(f"Header removed and saved to: {dest_file}")
        return True

    except Exception as e:
        print(f"Error removing header: {e}")
        return False

###############################################################################################
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

######################################################################################################

companies = os.environ.get('COMPANY').split(',')
companiesId = os.environ.get('COMPANY_ID').split(',')
source_parent_dir = os.environ.get('SOURCE_PARENT_DIR').strip()
target_parent_dir = os.environ.get('TARGET_PARENT_DIR').strip()

######################################################################################################

threshold = os.environ.get('myTHRESHOLD').strip()
if not threshold:
    print(" threshold is unset, defaulting to 101")
    threshold = 101
else:
    print(f" threshold is set to '{threshold}'")
    try:
        threshold = int(threshold)
        if threshold <= 0:
            print("Error  threshold must be a positive integer. Defaulting to 101.")
    except ValueError:
        print("Error  threshold must be a valid integer. Defaulting to 101.")

######################################################################################################

number_of_companies = os.environ.get('NUMBER_OF_COMPANIES').strip()
# getting the number of companies from the environment variable and checking if it is a valid integer.
try:
    number_of_companies = int(number_of_companies)
except ValueError:
    print("Error  NUMBER_OF_COMPANIES must be an integer.")
    sys.exit(1)

# Error Handling: Check if number_of_companies is a positive integer
if number_of_companies <= 0:
    print("Error  NUMBER_OF_COMPANIES must be a positive integer.")
    sys.exit(1)

######################################################################################################
# 	while [ $index -lt $NUMBER_OF_COMPANIES ]
index = 0
while index < number_of_companies:
    # brefore processing, check if the index is within bounds because if the number of companies is less than the number of company IDs, it will throw an error. 
    if index >= len(companies) and index >= len(companiesId):
        print(f"Error: i think there is mistake in the number of companies and company IDs, please check the env file.")
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

    path_uploadDir = f'{source_parent_dir}{company}/UPLOAD'
    
    # check if the path exists
    if not os.path.exists(path_uploadDir):
        lg.error(f' path {path_uploadDir} does not exist')
        sys.exit(1)
    lg.info(f' UPLOAD dir location: {path_uploadDir}')

    _completeFileName = f'{company}_complete'
    _completeFilePath = os.path.join(path_uploadDir, _completeFileName)

    # check if the _complete file exists
    if not os.path.exists(_completeFilePath):
        lg.error(f' _complete file {path_uploadDir} does not exist')
        sys.exit(1)
    lg.info(f' _complete file location: {_completeFilePath}')

    # Now in result we have _complete file created in the UPLOAD dir
    # we will begine find *_complete files in the UPLOAD dir
    # and then we will process them one by one
    # get the list of _complete files in the UPLOAD dir
    
    searchPattern = '*_complete'
    completeFilesList = [os.path.basename(file).strip() for file in glob.glob(f'{path_uploadDir}/{searchPattern}')]
    
    # check if the list is empty
    if not completeFilesList:
        lg.error(f' no _complete files found in {path_uploadDir} dir')
        continue
    else:
        lg.info(f'for {company}: list of _complete files in {path_uploadDir} dir \n {completeFilesList}')

    # setting offset to -9 to get the prefix of the file name beacuse len(*_complete) = 9
    offset = -9
    for i ,f in enumerate(completeFilesList):
    
        # extracting the file name from the path and getting the prefix
        baseName = os.path.basename(f)
        prefix = baseName[:offset]
        lg.info(f' Runnig for file:{f}, prefix is: {prefix}')

        # from prefix get usersCSV.csv file
        # useCsvInSourceDir = f'{prefix}_users.csv' these files are same
        usersCsvInSourceDir = f'{prefix}_users.csv'
        usersCSV = os.path.join(path_uploadDir, usersCsvInSourceDir)
        # now we have {company}_users.csv file as usersCSV file as path.
        # so, usersCSV = path to company_users.csv file.
        
        # check if the usersCSV file exists
        if not os.path.exists(usersCSV):
            lg.error(f' usersCSV file {usersCSV} does not exist')
            continue
        else:
            lg.info(f' usersCSV file location: {usersCSV}')
    
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
        """ STEP-1 """
        lg.info(f' =========== MOVING FURTHER FOR STEP-1  =========== ')
        path_companyInTargetDir = f'{target_parent_dir}/{company}' # .../workdir/company
        usersCsvInTargetDir = 'users.csv'
        manualUsersCsvInTargetDir = f'manual_users.csv'

        # we need to create above 2 files if not exists
        # first check if the target dir exists if not then create it
        if not os.path.exists(path_companyInTargetDir):
            os.makedirs(path_companyInTargetDir)
            lg.info(f' Directory {path_companyInTargetDir} created')
        else:
            lg.info(f' Directory {path_companyInTargetDir} already exists')
        
        # create path for users.csv and manual_users.csv
        # ex: {target_p_dir}/{company}/users.csv
        # ex: {target_p_dir}/{company}/manual_users.csv
        prevCheck = os.path.join(path_companyInTargetDir, usersCsvInTargetDir)
        prevManualCheck = os.path.join(path_companyInTargetDir, manualUsersCsvInTargetDir)

        # very first handling legacy case ,  we have flagLegacy var above for this.
        if len(sys.argv) > 2:
            if sys.argv[2].lower() == 'legacy':
                lg.info(" LEGACY MODE ENABLED..., STARTING LEGACY MODE")
                threshold = 101
                
                # for legacy mode we need to create blank files
                prevCheck = f'{path_companyInTargetDir}/blank.csv'
                prevManualCheck = f'{path_companyInTargetDir}/manual_blank.csv'
                
                if not os.path.exists(prevCheck): open(prevCheck, 'w').close()
                if not os.path.exists(prevManualCheck): open(prevManualCheck, 'w').close()
                
                if os.path.exists(prevCheck) and os.path.exists(prevManualCheck):
                    lg.info(f' {os.path.basename(prevCheck)} file created at {prevCheck}')
                    lg.info(f' {os.path.basename(prevManualCheck)} file created at {prevManualCheck}')
                lg.info(" EXIT FOR LEGACY MODE")
            else:
                lg.info(" Legacy mode not enabled")
        else:
            # check if the users.csv file exists in target dir if not create blank file
            open(prevCheck, 'w').close() if not os.path.exists(prevCheck) else lg.info(f' file {os.path.basename(prevCheck)} already exists at {prevCheck}')

            # check if the manual_users.csv file exists in target dir if not create blank file
            open(prevManualCheck, 'w').close() if not os.path.exists(prevManualCheck) else lg.info(f' file {os.path.basename(prevManualCheck)} already exists at {prevManualCheck}')

            lg.info(f' prev check files : \n {prevCheck} \n {prevManualCheck}')

        # previousCSV file name
        prevCsvFileInTargetDir = 'previous.csv'
        prevFile = os.path.join(path_companyInTargetDir, prevCsvFileInTargetDir)
        lg.info(f' previous.csv file location: {prevFile}')
        shutil.copy2(prevCheck, prevFile)
        lg.info(f' file {prevCheck} copied to {prevFile}')
        # Upload usersCSV file to channel in AUP Company
        script_path = 'AUP/'
        script_name = 'AUPChannelUploader.py'
        py_path = 'python3'            
        # define the full path to the script
        script_full_path = os.path.join(script_path, script_name)
        channelid = os.environ.get('CHANNEL_ID').strip() # just to ignore warning, this is temporary value.
        
        # define the command to run the script
        cmd = [py_path, script_full_path, channelid, usersCSV]
        # just run the command, not carrying about the output.
        try:
            subprocess.run(cmd)
            lg.info(f"  {script_name} script executed successfully.")
        except subprocess.CalledProcessError as e:
            lg.info(f"Error  executing script: {e}")
        
        
        if threshold < 101:
            lg.info(f" threshold is set to {threshold}, running diffChecker")
            server_location = 'ap-south-1' # just to ignore warning, this is temporary value.

            percent = diffChecker(threshold, server_location, prevFile, usersCSV, company_id)
            if percent == 1 :
                lg.info(f" diffChecker returned {percent}, Diff checker stopped AUP")
			    
                # remove _complete file
                rmfile = f'{_completeFilePath}'
                os.remove(rmfile)
                lg.info(f'{rmfile} file removed from {path_uploadDir}')

                archive_dir = 'aupFailureArchive'
                archive_dir_loc = f'{target_parent_dir}/{archive_dir}'
                os.makedirs(archive_dir_loc) if not os.path.exists(archive_dir_loc) else lg.info(f" ARCHIVE DIR EXISTS AT: {archive_dir_loc}")

                completeFile = f'{archive_dir_loc}/{_completeFileName}'
                
                # check if archive file is already there
                if os.path.exists(completeFile):
                    os.remove(completeFile)
                    lg.info(f' {completeFile} is alerdy exists so removed first')
                    
                shutil.move(usersCSV, archive_dir_loc)
                lg.info(f"{usersCSV} file moved to {archive_dir_loc} location")
                sys.exit(1)
            else:
                lg.info(f" diffChecker returned {percent}, Diffchecker passed!!")

        # Copy previous manual_users.csv 
 		#	(or blank one you just touched, or blank one you forced in there), 
 		#	as manual_previous.csv
        # manual_previous name 
        manualPrevFile = 'manual_previous.csv'
        manualPrevFilePath = os.path.join(path_companyInTargetDir, manualPrevFile)
        lg.info(f' manual_previous.csv file location: {manualPrevFilePath}')

        # check if the manual_previous.csv file exists in target dir if not create blank file
        open(manualPrevFilePath, 'w').close() if not os.path.exists(manualPrevFilePath) else lg.info(f' file {os.path.basename(manualPrevFilePath)} already exists at {manualPrevFilePath}')

        # Copy the previous manual_users.csv to manual_previous.csv
        shutil.copy2(prevManualCheck, manualPrevFilePath)
        lg.info(f' file {prevManualCheck} copied to {manualPrevFilePath}')

        lg.info(f' =========== END OF STEP-1  =========== ')
        """ END OF STEP-1 """
        """ STEP-2 """
        lg.info(f' =========== MOVING FURTHER FOR STEP-2  =========== ')

        # If ${usersCSV} (a CSV file path) exists and is a regular file ➔ then execute the block inside.
        # Check if the file exists
        if os.path.isfile(usersCSV):
            lg.info(f' file {os.path.basename(usersCSV)} exists at {usersCSV}')
        
        # Move the CSV file ➔ into the TARGET_PARENT_DIR folder under that company. 
        # And rename it during the move ➔ as users.csv.<prefix>
        newUsersCSV = f'users.csv.{prefix}'
        newUsersCSVPath = os.path.join(path_companyInTargetDir, newUsersCSV)
        lg.info(f' new users.csv file location: {newUsersCSVPath}')
        shutil.move(usersCSV, newUsersCSVPath)
        lg.info(f' file {usersCSV} moved to {newUsersCSVPath}')

        dst_file = f'{path_companyInTargetDir}/users.csv'
        # create the destination file if it doesn't exist
        if not os.path.exists(dst_file):
            open(dst_file, 'w').close()
            lg.info(f' file {os.path.basename(dst_file)} created at {dst_file}')
        else:
            lg.info(f' file {os.path.basename(dst_file)} already exists at {dst_file}')

        remove_csv_header(newUsersCSVPath, dst_file, lg)
        lg.info(f' file {newUsersCSVPath} header removed and saved to {dst_file}')
        dos2unix(dst_file)
        lg.info(f' dos2unix run on {dst_file}')

        #path to addUpdate.csv and disable.csv
        addUpdateCSV = f'{path_companyInTargetDir}/addUpdate.csv'
        disableCSV = f'{path_companyInTargetDir}/disable.csv'
        
        mv_addUpdateCSVName = f'addUpdate.csv.{prefix}'
        mv_disableCSVName = f'disable.csv.{prefix}'
        
        mv_addUpdateCSV = os.path.join(path_companyInTargetDir, mv_addUpdateCSVName)
        mv_disableCSV = os.path.join(path_companyInTargetDir, mv_disableCSVName)
        
        lg.info(f' addUpdate.csv file location: {addUpdateCSV}')
        lg.info(f' disable.csv file location: {disableCSV}')
        lg.info(f' mv_addUpdateCSV file location: {mv_addUpdateCSV}')
        lg.info(f' mv_disableCSV file location: {mv_disableCSV}')
        # if the addUpdate.csv and disable.csv files exist then move to addUpdateCSV.<prefix> and disableCSV.<prefix>        
        shutil.move(addUpdateCSV, mv_addUpdateCSV) if os.path.exists(addUpdateCSV) else lg.info(f' file {os.path.basename(addUpdateCSV)} does not exist at {addUpdateCSV}')

        shutil.move(disableCSV, mv_disableCSV) if os.path.exists(disableCSV) else lg.info(f' file {os.path.basename(disableCSV)} does not exist at {disableCSV}')


        compare_user_files(prevFile, f'{path_companyInTargetDir}/users.csv',
                          f'{path_companyInTargetDir}/addUpdate.csv', f'{path_companyInTargetDir}/disable.csv')
        
        lg.info(f' =========== END OF STEP-2  =========== ')
        """ END OF STEP-2 """

        # older implementation of groups.csv and userGroupMembership.csv 
        groupsCSVFileName = f'{prefix}_groups.csv'
        groupsCSV = os.path.join(path_uploadDir, groupsCSVFileName)
        mv_groupsCSVFileName = f'groups.csv.{prefix}'
        mv_groupsCSV = os.path.join(path_companyInTargetDir, mv_groupsCSV)
        lg.info(f' groupsCSV file location: {groupsCSV}')
        lg.info(f' mv_groupsCSV file location: {mv_groupsCSV}')

        shutil.move(groupsCSV, mv_groupsCSV) if os.path.exists(groupsCSV) else lg.info(f' file {os.path.basename(groupsCSV)} does not exist at {groupsCSV}')
        
        remove_csv_header(groupsCSV, mv_groupsCSV, lg)
        lg.info(f' file {groupsCSV} header removed and saved to {mv_groupsCSV}')
    
        userGroupMembershipCSVFileName = f'{prefix}_userGroupMembership.csv'
        userGroupMembershipCSV = os.path.join(path_uploadDir, userGroupMembershipCSVFileName)
        mv_userGroupMembershipCSVFileName = f'userGroupMembership.csv.{prefix}'
        mv_userGroupMembershipCSV = os.path.join(path_companyInTargetDir, mv_userGroupMembershipCSVFileName)
        lg.info(f' userGroupMembershipCSV file location: {userGroupMembershipCSV}')
        lg.info(f' mv_userGroupMembershipCSV file location: {mv_userGroupMembershipCSV}')
        
        shutil.move(userGroupMembershipCSV, mv_userGroupMembershipCSV) if os.path.exists(userGroupMembershipCSV) else lg.info(f' file {os.path.basename(userGroupMembershipCSV)} does not exist at {userGroupMembershipCSV}')
        
        remove_csv_header(userGroupMembershipCSV, mv_userGroupMembershipCSV, lg)
        lg.info(f' file {userGroupMembershipCSV} header removed and saved to {mv_userGroupMembershipCSV}')

        # sunovion Legacy implementation
        lg.info(f' =========== MOVING FURTHER FOR SUNOVION LEGACY  =========== ')
        fbtUsersCSVFileName = f'{prefix}_fbt_users.csv'
        fbtUsersCSV = os.path.join(path_uploadDir, fbtUsersCSVFileName)
        mv_fbtUsersCSVFileName = f'fbt_users.csv'
        mv_fbtUsersCSV = os.path.join(path_companyInTargetDir, mv_fbtUsersCSVFileName)
        lg.info(f' fbtUsersCSV file location: {fbtUsersCSV}')
        lg.info(f' mv_fbtUsersCSV file location: {mv_fbtUsersCSV}')

        shutil.move(fbtUsersCSV, mv_fbtUsersCSV) if os.path.exists(fbtUsersCSV) else lg.info(f' file {os.path.basename(fbtUsersCSV)} does not exist at {fbtUsersCSV}')

        manualUsersCSVFileName = f'{prefix}_manual_users.csv'
        manualUsersCSV = os.path.join(path_uploadDir, manualUsersCSVFileName)

        shutil.move(manualUsersCSV, mv_fbtUsersCSV) if os.path.exists(manualUsersCSV) else lg.info(f' file {os.path.basename(manualUsersCSV)} does not exist at {manualUsersCSV}')

        # fw enhancement step 3 - manual files
        manualUpadateCSV = f'{path_companyInTargetDir}/manual_users.csv'
        mv_manualUpadateCSV = f'{path_companyInTargetDir}/{manualUpadateCSV}.{prefix}'

        lg.info(f' manualUpadateCSV file location: {manualUpadateCSV}')
        lg.info(f' mv_manualUpadateCSV file location: {mv_manualUpadateCSV}')
        shutil.move(manualUpadateCSV, mv_manualUpadateCSV) if os.path.exists(manualUpadateCSV) else lg.info(f' file {os.path.basename(manualUpadateCSV)} does not exist at {manualUpadateCSV}')     

        # Load into staging and production
    lg.info("======================================================")
    print("=========================================================")
    index += 1