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
# loading env
companies = os.environ.get('COMPANY').split(',')
companiesId = os.environ.get('COMPANY_ID').split(',')
source_parent_dir = os.environ.get('SOURCE_PARENT_DIR').strip()
target_parent_dir = os.environ.get('TARGET_PARENT_DIR').strip()
channel_id = os.environ.get('CHANNEL_ID').strip()
location = os.environ.get('LOCATION').strip()
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
# getting the number of companies from the environment variable and checking if it is a valid integer.

number_of_companies = os.environ.get('NUMBER_OF_COMPANIES').strip()
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
index = 0
while index < number_of_companies:
  
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
    
    upload_dir = os.path.join(source_parent_dir, company, 'UPLOAD')
    pattern = os.path.join(upload_dir, '*_complete')

    for filepath in glob.glob(pattern):
        if os.path.isfile(filepath):
            lg.info(f' filepath is:{filepath}')
            fileName = os.path.basename(filepath)
            lg.info(f' fileName is:{fileName}')
            prefix = fileName[:-9]
            lg.info(f' prefix is:{prefix}')
        

        """ file Metadata case: 
            this is a feature enhancement. do it later
            
            case: AUP rund on current date file but clients can sent dile which is created yesterday but sent today. so i need to identify then file creation using file metadata. 
        """

        usersCSV = os.path.join(upload_dir, f'{prefix}_users.csv')
    
        # checking if file is exist 
        if not os.path.exists(usersCSV):
            lg.error(f'{usersCSV} file is not present, stopping and terminating script with exit code 1')
            sys.exit(1)
        
        if company_id in ('218','120'):
           try:
               subprocess.run(['iconv','-f','UTF-8', usersCSV, '-o','/dev/null'
                               ], check=True)
               lg.info("UTF-8 check passed")
           except subprocess.CalledProcessError:
               lg.error("UTF-8 formatting invalid; aborting")
               sys.exit(1)

        previousCheck = os.path.join(target_parent_dir, company , 'users.csv') 
        previousManualCheck = os.path.join(target_parent_dir, company, 'manual_users.csv')

        # legacy mode
        if len(sys.argv) > 2:
            if sys.argv[2].lower() == 'legacy':
                lg.info("RUNNING LEGACY VERSION WITH FULL FILE")
                threshold = 101
                
                previousCheck = os.path.join(target_parent_dir, company , 'blank.csv') 
                previousManualCheck = os.path.join(target_parent_dir, company, 'manual_blank.csv')

                # creating blank file
                open(previousCheck, 'w').close()
                open(previousManualCheck, 'w').close()
            else: 
                lg.info("NO LEGACY PARAMETER")
        else:
            # checking if users & manual_users is exists else create it.
            # for users.csv
            if os.path.exists(previousCheck):
                lg.info(f'{os.path.basename(previousCheck)} is exists at: \n{previousCheck}')
            else:
                open(previousCheck, 'w').close()
                lg.info(f'file created at:\n {previousCheck} ') 
            
            #for manual_users.csv
            if os.path.exists(previousManualCheck):
                lg.info(f'{os.path.basename(previousManualCheck)} is exist at: \n {previousManualCheck}') 
            else:
                open(previousManualCheck, 'w').close()
                lg.info(f'file crated at: \n {previousManualCheck}')

            previousFile= os.path.join(target_parent_dir, company, 'previous.csv')
            
            # copy exixting user.csv file (or just creaed above blank file ) in previous.csv file
            if not os.path.exists(previousFile):
                open(previousFile, 'w').close()
                lg.info(f'{os.path.basename(previousFile)}, is not exist so created.')
            shutil.copy2(previousCheck, previousFile)
            lg.info(f'COPY: \n from: {previousCheck} \n to: {previousFile}')

            # upload file to channel in AUP Company
            # /usr/local/bin/python3.6 /home/ubuntu/allegoAdmin/scripts/channels/AUPChannelUploader.py ${channelid} ${usersCSV}
            pyLoc = 'python3'
            scriptLoc = './home/ubuntu/allegoAdmin/scripts/channels/AUPChannelUploader.py'
            CMD_aupChannel = [pyLoc, scriptLoc, channel_id , usersCSV]
            try:
                subprocess.run(CMD_aupChannel)
            except subprocess.CalledProcessError as e:
                lg.error(f"Error occurred while running AUPChannelUploader: \n  {str(e)}")

            # Check estimated differences first CASE is based on exit codes. Skip if threshold = 101
            if threshold < 101:  
                # percent = diffChecker(previousFile, usersCSV, threshold, location)
                percent = 0
                if percent == 1 :
                    lg.info(f" diffChecker returned {percent}, Diff Checker has stopped AUP ")
                    archive_dir = os.path.join(target_parent_dir, 'aupFailureArchive')
                    os.makedirs(archive_dir, exist_ok=True)
                    
                    try:
                        subprocess.run(['mv', usersCSV, os.path.join( archive_dir, f'{prefix}_{company}')])
                    except Exception as e:
                        lg.error(f"Error occurred while moving file: \n  {str(e)}")

                    for f in glob.glob(pattern): os.remove(f)

                    sys.exit(1)
                else:
                    lg.info(f" diffChecker returned {percent}, Diff Checker has passed AUP ")
            
            # copy existing manual_users.csv (or new blank created) in manual_previous.csv
            previousManualFile = os.path.join(target_parent_dir, company, 'manual_previous.csv')
            if not os.path.exists(previousManualFile):
                open(previousManualFile, 'w').close()
                lg.info(f'{os.path.basename(previousManualFile)}, is not exist so created.')
            shutil.copy2(previousManualCheck, previousManualFile)
            lg.info(f'COPY: \n from: {previousManualCheck} \n to: {previousManualFile}')

            # Create expected users.csv from new file
            # Run dos2unix here to clean up hidden character else the match will fail
            # usersCSV set further up for UTF8 checks

            if os.path.exists(usersCSV):
                lg.info(f'{usersCSV}')

                # creating new file to get desired file.
                newFile = os.path.join(target_parent_dir, company, f'users.csv.{prefix}')

                # 1. mv (move)
                try: 
                    subprocess.run(['mv', usersCSV, newFile], check=True)  
                    lg.info(f'file moved from {usersCSV} to {newFile}')
                    # 2. tail (skip header)
                    subprocess.run(['bash', '-c', f'tail -n +2 {newFile} > {usersCSV}'], check=True)
                    lg.info(f'tail: header removed')   
                    # 3. dos2unix (convert line endings)
                    subprocess.run(['dos2unix', newFile, usersCSV], check=True)
                    lg.info('dos2unix done')
                except Exception as e:
                    lg.error(f'Exeption in mv,tail, dos2unix , {str(e)}')
            else: 
                lg.log(f'{usersCSV} is not exists')

            lg.info("END OF STEP - 1") # checked done.

            # paths of addUpdate and disable csv
            addUpdateCSV = os.path.join(target_parent_dir, company, 'addUpdate.csv')
            disableCSV = os.path.join(target_parent_dir, company, 'disable.csv')
            
            if not os.path.exists(addUpdateCSV):
                open(addUpdateCSV, 'w').close()
                lg.info(f'{os.path.basename(addUpdateCSV)}, is not exist so created.')
            
            if not os.path.exists(disableCSV):
                open(disableCSV, 'w').close()
                lg.info(f'{os.path.basename(disableCSV)}, is not exist so created.')

            tmp_addUpdate = os.path.join(target_parent_dir, company, f'addUpdate.csv.{prefix}')

            if os.path.exists(addUpdateCSV):
                # 1. mv (move)
                subprocess.run(['mv', addUpdateCSV, tmp_addUpdate], check=True)
                lg.info(f'{addUpdateCSV} is moved to {tmp_addUpdate}')
            else:
                lg.error(f'{addUpdateCSV} is not exists')
            
            tmp_disable = os.path.join(target_parent_dir, company, f'disable.csv.{prefix}')
            if os.path.exists(disableCSV):
                # 1. mv (move)
                subprocess.run(['mv', disableCSV, tmp_disable], check=True)
                lg.info(f'{disableCSV} is moved to {tmp_disable}')
            else:
                lg.error(f'{disableCSV} is not exists')

            try:
                subprocess.run(['bash', '-c', f"comm -13 <(sort {previousFile}) <(sort {os.path.join(target_parent_dir,company,'users.csv')}) > {addUpdateCSV}"],
                                executable='/bin/bash')
                lg.log("Done comm for addUser")
                subprocess.run(['bash', '-c', f"comm -23 <(sort {previousFile}) <(sort {os.path.join(target_parent_dir,company,'users.csv')}) > {disableCSV}"],
                                executable='/bin/bash')
                lg.info("Done comm for disable")
            except Exception as e:
                lg.error(f'Exeption in comm, {str(e)}') 

            lg.info("END OF STEP - 2")
            # end of step 2

            groupsCSV = os.path.join(upload_dir, f'{prefix}_groups.csv')

            if not os.path.exists(groupsCSV):
                open(groupsCSV, 'w').close()
                lg.info(f'{os.path.basename(groupsCSV)}, is not exist so created.')
            
            if os.path.exists(groupsCSV):
                # 1. mv (move)
                subprocess.run(['mv', groupsCSV, os.path.join(target_parent_dir, company, f'groups.csv.{prefix}')], check=True)
                lg.info(f'{groupsCSV} is moved to {os.path.join(target_parent_dir, company, f"groups.csv.{prefix}")}')
                
                # 2. tail (skip header)
                subprocess.run(['bash', '-c', f'tail -n +2 {os.path.join(target_parent_dir, company, f"groups.csv.{prefix}")} > {groupsCSV}'], check=True)

            # sunvion legacy
            fbtUsersCSV = os.path.join(upload_dir,f'{prefix}_fbt_users.csv')
            if not os.path.exists(fbtUsersCSV):
                open(fbtUsersCSV, 'w').close()
                lg.info(f'{os.path.basename(fbtUsersCSV)}, is not exist so created.')

            if os.path.exists(fbtUsersCSV):
                # 1. mv (move)
                subprocess.run(['mv', fbtUsersCSV, os.path.join(target_parent_dir, company, f'fbt_users.csv.{prefix}')], check=True)
                lg.info(f'{fbtUsersCSV} is moved to {os.path.join(target_parent_dir, company, f"{prefix}_fbt_users.csv")}')

                #tail 
                subprocess.run(['bash', '-c', f'tail -n +2 {os.path.join(target_parent_dir, company, f"fbt_users.csv.{prefix}")} > {fbtUsersCSV}'], check=True)

            # manual support
            manualUsersCSV= os.path.join(upload_dir, f'{prefix}_manual_users.csv')
            if not os.path.exists(manualUsersCSV):
                open(manualUsersCSV, 'w').close()
                lg.info(f'{os.path.basename(manualUsersCSV)}, is not exist so created.')

            if os.path.exists(manualUsersCSV):
                # 1. mv (move)
                subprocess.run(['mv', manualUsersCSV, os.path.join(target_parent_dir, company, f'manual_users.csv.{prefix}')], check=True)
                lg.info(f'{manualUsersCSV} is moved to {os.path.join(target_parent_dir, company, f"{prefix}_manual_users.csv")}')

                #tail
                subprocess.run(['bash', '-c', f'tail -n +2 {os.path.join(target_parent_dir, company, f"manual_users.csv.{prefix}")} > {manualUsersCSV}'], check=True)

            # for update file 
            manualUpdateCSV = os.path.join(target_parent_dir, company, f'manual_update.csv')
            if not os.path.exists(manualUpdateCSV):
                open(manualUpdateCSV, 'w').close()
                lg.info(f'{os.path.basename(manualUpdateCSV)}, is not exist so created.')

            if os.path.exists(manualUpdateCSV):
                # 1. mv (move)
                subprocess.run(['mv', manualUpdateCSV, os.path.join(target_parent_dir, company, f'manual_update.csv.{prefix}')], check=True)
                lg.info(f'{manualUpdateCSV} is moved to {os.path.join(target_parent_dir, company, f"{prefix}_manual_update.csv")}')

            try:
                subprocess.run(['bash', '-c', f"comm -13 <(sort {previousManualFile}) <(sort {os.path.join(target_parent_dir,company,'manual_users.csv')}) > {manualUpdateCSV}"],
                                executable='/bin/bash')
            except Exception as e:
                lg.error(f'Exeption in manual update {str(e)}')

            # Remove complete file after processing
            pattern1 = os.path.join(upload_dir,  f'{prefix}_complete')
            for f in glob.glob(pattern1): 
                os.remove(f)

            #
   			# now run the script to load the data into staging tables in the db
   			#
            allegoHome = os.environ.get('ALLEGO_HOME').strip()
            stageScript = os.path.join(allegoHome, 'conf', 'import' , 'customer' , company , f'setup_{company}.py')
            # Echo the staging script command
            lg.info(f"calling {stageScript} {os.path.join(target_parent_dir, company)}")

            # Execute the staging script
            try:
                subprocess.run([stageScript, os.path.join(target_parent_dir, company)], check=True)
            except subprocess.CalledProcessError as e:
                lg.error(f"Error executing staging script: {str(e)}") 
            
            #
   			# now run the script to load from staging into production - run this one asynchronously
   			#
               
            loadScript = os.path.join(allegoHome, 'scripts', 'import.sh')
            # Echo the load script command
            lg.info(f"calling {loadScript} {company}")
            try:
                subprocess.run([loadScript, company], check=True)
                lg.info(f"load script executed successfully")
                # Remove complete file after processing
            except Exception as e:
                lg.error(f"Error executing load script: {str(e)}")

    index += 1