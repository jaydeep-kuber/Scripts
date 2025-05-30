import os
import sys
import csv
import json
import glob
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

#custom imports
from FwLibrary import DiffChecker

class Assume:
    def __init__(self):
        pass
    
    def createCompleteFile(self,path):
        open(path, 'w').close()
        print(f"created file: {path}")

    def createCSVFile(self, path):
        open(path, 'w').close()
        print(f"created csv file: {path}")

    def createAUPscriptFile(self, path):
        script_file = Path(path)
        script_file.parent.mkdir(parents=True, exist_ok=True)
        script_file.touch()
        print(f"created AUP script file: {path}")

    def cleanUP(self):
        print("cleaning up...")
        os.system("rm -r ./home/*")
    
    def check_utf8(self, file_path: str) -> int:
        print("Checking UTF8 format")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                while f.read(1024):  # Read in chunks
                    pass
            print("UTF 8 Check Passed")
            return 0
        except UnicodeDecodeError:
            print("UTF 8 Formatting has invalid characters; exiting")
            sys.exit(1)

def loadEnv(filePath: str):
    """ this function is for loading ENV """
    # checking if file exists
    if not os.path.exists(filePath):
        print(">>> ENV file id not exist at path: ", filePath)
        sys.exit(1)
    # if yes then open and read it.
    with open(filePath, 'r') as envFile:
        env = json.load(envFile)
        print ("ENV Loaded from file: ", filePath)
        return env

def thresholdCheck(value):
    """ @value: threshol value coming from ENV file """
    if not value:
        print(">>> Threshold is not set in ENV file.")
        value = 101
    else:
        int(value) if not isinstance(value, int) else None
    print(f"thresold is: {value} ")
    return value

import os

def cleanCSV(path: str):
    """
    Processes the given users CSV:
    - If the file exists:
      - Removes the header (first line)
      - Writes the result back to the same file with Unix-style line endings
    """
    if os.path.isfile(path):
        print(path)
        
        # Read lines, skip the first (header), normalize line endings
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()[1:]  # Skip header

        # Write back without header and with Unix line endings
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            for line in lines:
                f.write(line.rstrip('\r\n') + '\n')
    else:
        print(f"File {path} does not exist.")

def sort_csv_by_column(prevFilePath, currentFilePath, prevOut, currntOut, column_name=None):
    
    # sorting prev file
    with open(prevFilePath, mode='r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        prevFileData = list(reader)

    if not prevFileData:
        print("CSV file is empty")

    # Use provided column or default to the first column
    sort_key = column_name if column_name else reader.fieldnames[0] # type: ignore
    if sort_key not in reader.fieldnames: # type: ignore
        raise ValueError(f"Column '{sort_key}' not found in CSV headers")
 
    sortedPrevFile = sorted(prevFileData, key=lambda x: x[sort_key])    
    # print(sortedPrevFile)
    print(f"file: {prevFilePath} sorted by: {sort_key}")

    with open(prevOut, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames) # type: ignore
        writer.writeheader()
        writer.writerows(sortedPrevFile)
    print(f"sorted file saved at: {prevOut}")
    print("########################################################################")
  
    # sorting current file
    with open(currentFilePath, mode='r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        currentFileData = list(reader)

    if not currentFileData:
        print("CSV file is empty")
    
    # Use provided column or default to the first column
    sort_key = column_name if column_name else reader.fieldnames[0] # type: ignore
    if sort_key not in reader.fieldnames: # type: ignore
        raise ValueError(f"Column '{sort_key}' not found in CSV headers")
    
    sortedCurrentFile = sorted(currentFileData, key= lambda x : x[sort_key])
    # print(sortedCurrentFile)
    print(f"file {currentFilePath} sorted by: {sort_key}")

    with open(currntOut, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames) # type: ignore
        writer.writeheader()
        writer.writerows(sortedCurrentFile)

    print(f"sorted file saved at: {currntOut}")
    print("#################################[ sorting done ]####################################")

def generate_add_discard_files(current_csv, previous_csv, add_csv, discard_csv):
    def read_rows(filepath):
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = [tuple(row) for row in reader]
        return header, rows

    # Read both CSVs
    current_header, current_rows = read_rows(current_csv)
    previous_header, previous_rows = read_rows(previous_csv)

    # Optional: Check if headers match
    if current_header != previous_header:
        raise ValueError("Headers do not match between current and previous CSV files")

    # Convert to sets for comparison
    current_set = set(current_rows)
    previous_set = set(previous_rows)

    add_rows = current_set - previous_set  # new rows
    discard_rows = current_set & previous_set  # existing rows

    # Write add.csv
    with open(add_csv, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(current_header)
        writer.writerows(add_rows)
    print("file add.csv generated")

    # Write discard.csv
    with open(discard_csv, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(current_header)
        writer.writerows(discard_rows)
    print("file discard.csv generated")
    print("#################################[ add/discard files generated ]####################################")

def main():
    # default path
    envFilePath= '../env/fwDevEnv.json'
    assume = Assume()
    clean = input("Would you like to clean up after execution ? (yes/no): ")
    clean_up_flag = True if clean.lower() == 'yes' else False

    # load env if path is given in command line as arg-1 else load defaul.
    if len(sys.argv) > 1:
        envFilePath = sys.argv[1]
        env = loadEnv(envFilePath)
    else:
        env = loadEnv(envFilePath)

    # cheking thresold
    threshold = thresholdCheck(env['threshold'])

    # preparation for while loop
    number_of_company = int(env['number_of_company'])
    all_companies = env['all_companies'] # this ia array of json
    src_dir = env['source_parent_dir']
    trgt_dir = env['target_parent_dir']

    index = 0
    print(len(all_companies))
    # itrating till value of number_of_company
    while index < number_of_company:
        
        if env['number_of_company'] != len(all_companies):
            print(">>> number_of_company is not equal to number of companies in env file.")
            sys.exit(1)
        # getting company name and id
        company_name = all_companies[index]['cmp_name']
        company_id = all_companies[index]['cmp_id']
        print(f"checking: {index} , {datetime.now()}")
        print(f"company name: {company_name}")
        print(f"company id: {company_id}")
        
        # ${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/ = /home/company_name/UPLOAD/
        upload_dir = os.path.join(src_dir, company_name, 'UPLOAD')
        os.makedirs(upload_dir, exist_ok=True)

        print(f"upload dir created: {upload_dir}")

        ########################################################################################
        # creating _complete file
        complete_file = os.path.join(upload_dir, f'{company_name}_complete')
        assume.createCompleteFile(complete_file)
        ########################################################################################

        completeFile_lst = [os.path.basename(file) for file in glob.glob(os.path.join(upload_dir, "*_complete"))]
        print(completeFile_lst)

        for file in completeFile_lst:
            print(f"file: {file}")
            # getting file name
            fileName = os.path.basename(file)
            # getting prefix
            prefix = fileName.split('_')[0]
            print(f"prefix: {prefix}")    

            # storing 'usersCSV' file path.
            usersCSV = os.path.join(upload_dir, f'{prefix}_users.csv')
            
            ########################################################################################
            # creating csv file
            assume.createCSVFile(usersCSV)
            #########################################################################################
            
            if not os.path.exists(usersCSV):
                print(f"usersCSV file not found: {usersCSV}")
                sys.exit(1)
            else:
                print(f"your usersCSV located at: {usersCSV}")

            # checking utf-8 encoding
            assume.check_utf8(usersCSV)

            # FileWatcherExpressEnhancement Step 1
            # storing paths of previousCheck , previousManualCheck

            previousCheck = os.path.join(trgt_dir, company_name , 'users.csv')
            previousManualCheck = os.path.join(trgt_dir, company_name , 'manual_users.csv')
            
            # creating previousCheck and previousManualCheck files if not exist if exist then skip creating, handling legacy mode too 
            if len(sys.argv) > 1  and sys.argv[2].lower() == 'legacy':
                print("running legacy version...")
                threshold = 101
                previousCheck = Path(os.path.join(trgt_dir, company_name , 'blank.csv'))
                previousManualCheck = Path(os.path.join(trgt_dir, company_name , 'manual_blank.csv'))

                """ from pathlib import Path

                pathlib .Path().mkdir(parents=True, exist_ok=True) is a modern and clean way to create files, this way ensure that directory exists before creating file for preventing of errors.
                """
                previousCheck.parent.mkdir(parents=True, exist_ok=True)
                previousCheck.touch()
                
                previousManualCheck.parent.mkdir(parents=True, exist_ok=True)
                previousManualCheck.touch()
            else:
                previousCheck = Path(previousCheck)
                previousManualCheck = Path(previousManualCheck)
                
                if not previousCheck.exists():
                    previousCheck.parent.mkdir(parents=True, exist_ok=True)
                    previousCheck.touch()
                    print(f"Created blank: {previousCheck} file for first time run ")
                else: 
                    print(f"file detected at : {previousCheck}")
                
                if not previousManualCheck.exists():
                    previousManualCheck.parent.mkdir(parents=True, exist_ok=True)
                    previousManualCheck.touch()
                    print(f"Created blank: {previousManualCheck} file for first time run ")
                else:
                    print(f"file detected at : {previousManualCheck}")
            
            # store paths of previousCheck and previousManualCheck in a dictionary 

            # copy previousCheck to previousFile
            previousFile = os.path.join(trgt_dir, company_name , 'previous.csv')
            shutil.copy2(previousCheck, previousFile)

            # uplaod script
            # /usr/local/bin/python3.6 /home/ubuntu/allegoAdmin/scripts/channels/AUPChannelUploader.py ${channelid} ${usersCSV}

            ###########################################################################################
            script_file = './home/ubuntu/allegoAdmin/scripts/channels/AUPChannelUploader.py'
            assume.createAUPscriptFile(script_file)
            channelId = str(env["channelId"])
            py = 'python3'
            ##########################################################################################

            CMD = [py, script_file, channelId, usersCSV]
            print(f"CMD: {CMD}")
            try: 
                subprocess.run(CMD)
            except Exception as e:
                print(f"Error: {e}")

            # Check estimated differences first CASE is based on exit codes. Skip if threshold = 101
            if threshold < 101:
                # true then do something 
                percent = DiffChecker(previousFile , usersCSV , threshold, "location" )
                
                if percent == 1:
                    print("Diff Checker has stopped AUP")

                    # Remove *_complete files from UPLOAD directory
                    # upload_dir = os.path.join(src_dir, company_name, "UPLOAD")
                    for file in os.listdir(upload_dir):
                        if file.endswith("_complete"):
                            os.remove(os.path.join(upload_dir, file))

                    # Move usersCSV to aupFailureArchive directory
                    dest_file = os.path.join(trgt_dir, "aupFailureArchive", f"{prefix}_{company_name}")
                    shutil.move(usersCSV, dest_file)
                    sys.exit(1)
                else:
                    print("Diff Checker has passed.")

            # copy previousManualCheck to previousFileManual
            previousFileManual = os.path.join(trgt_dir, company_name , 'previous_manual.csv')
            shutil.copy2(previousManualCheck, previousFileManual)
            # End FileWatcherExpressEnhancement Step 1
            
            # Run dos2unix here to clean up hidden character else the match will fail
            # Create expected users.csv from new file
            # usersCSV set further up for UTF8 checks
    	    # usersCSV=${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/${prefix}_users.csv
            cleanCSV(usersCSV)

            # FileWatcherExpressEnhancement Step 2
            # Compare new users.csv and previous.csv to populate staging tables.
            # If users.csv was blank from Step 1, addUpdate.csv should be a 1:1 copy of users.csv and disable.csv should be empty.

            # save addUpdate.csv and disable.csv file paths
            addUpdateCSV = os.path.join(trgt_dir, company_name, "addUpdate.csv")
            disableCSV = os.path.join(trgt_dir, company_name, "disable.csv")

            ################################################################################

            assume.createCSVFile(addUpdateCSV) if not os.path.exists(addUpdateCSV) else None
            assume.createCSVFile(disableCSV) if not os.path.exists(disableCSV) else None

            ################################################################################

            # rename both files to prevent overriding the data
            try: 
                os.rename(addUpdateCSV, f"{addUpdateCSV}.{prefix}")
                os.rename(disableCSV, f"{disableCSV}.{prefix}")
                print("Renaming done.")
            except:
                print(f"Error renaming files: {addUpdateCSV} and {disableCSV}")
                print("seems like there is no file or remamed exist... exiting from script.")
                sys.exit(1)

            # now perform line diff 
            # step-1 sort file. based on id column
            # sort_csv_by_column("../py/home/ubuntu/allegoAdmin/workdir/solarcity/previous.csv", "../py/home/ubuntu/allegoAdmin/workdir/solarcity/users.csv", "id")
            # generate_add_discard_files("./sorted_currnt.csv","./sorted_prev.csv","./sortedFiles/add.csv","./sortedFiles/discar.csv")

            ##################################################
            # creating temp sort dir where we will save sort files
            # then process for add and discard
            # then delete this sort dir
            sort_dir = os.path.join(trgt_dir, company_name, "sort")
            os.makedirs(sort_dir, exist_ok=True)
            prevOut = os.path.join(sort_dir, "prevSorted.csv")
            currOut = os.path.join(sort_dir, "currSorted.csv")
            ##################################################

            sort_csv_by_column(previousFile, previousCheck,prevOut, currOut,"EmployeeNumber")
            # in this fuction we are passing the sorted files to generate add and discard files
            generate_add_discard_files(prevOut,currOut,addUpdateCSV,disableCSV)

            #################################################
            # clean temporary sort dir
            shutil.rmtree(sort_dir)
            print("temp sort dir was removed")
            #################################################
            # now we have addUpdate.csv and disable.csv files

            # Older implementatiosn of groups.csb and userGroupMemberShip.csv
            #store path of grps csv
            src_groupsCSV=os.path.join(upload_dir, f"{prefix}_groups.csv")
            trgt_groupsCSV=os.path.join(trgt_dir,company_name,f"groups.csv")
            if os.path.exists(src_groupsCSV):
                # mv
                shutil.move(src_groupsCSV, trgt_groupsCSV)
                # tail
                cleanCSV(trgt_groupsCSV)
            else:
                print(f"groups.csv file not found in upload dir: {upload_dir}")

            src_userGroupMembershipCSV= os.path.join(upload_dir, f"{prefix}_userGroupMembership.csv") 
            trgt_userGroupMembershipCSV= os.path.join(trgt_dir,company_name,f"userGroupMembership.csv")
            if os.path.exists(src_userGroupMembershipCSV):
                # mv
                shutil.move(src_userGroupMembershipCSV, trgt_userGroupMembershipCSV)
                # tail
                cleanCSV(trgt_userGroupMembershipCSV)
            else:
                print(f"userGroupMembership.csv file not found in upload dir: {upload_dir}")
            
		# sunovion Legacy implementation
            src_fbtUsersCSV=os.path.join(upload_dir, f"{prefix}_fbt_users.csv")
            trgt_fbtUsersCSV = os.path.join(trgt_dir,company_name,f"fbt_users.csv")
            if os.path.exists(src_fbtUsersCSV):
                # mv
                shutil.move(src_fbtUsersCSV, trgt_fbtUsersCSV)
                # tail
                cleanCSV(trgt_fbtUsersCSV)
            else:
                print(f"fbt_users.csv file not found in upload dir: {upload_dir}")

        # Manual File Support
            src_manualUsersCSV= os.path.join(upload_dir, f"{prefix}_manual_users.csv")
            trg_manualUsersCSV = os.path.join(trgt_dir, company_name, "manual_users.csv")
            if os.path.exists(src_manualUsersCSV):
                # mv
                shutil.move(src_manualUsersCSV, trg_manualUsersCSV)
                # tail
                cleanCSV(trg_manualUsersCSV)
            else:
                print(f"manual_users.csv file not found in upload dir: {upload_dir}")
        
        # FileWatcherExpressEnhancement Step 3 - Manual Files
            manualUpdateCSV = os.path.join(trgt_dir, company_name, "manual_update.csv")
            if os.path.exists(manualUpdateCSV):
                # mv
                shutil.move(manualUpdateCSV, manualUpdateCSV)
            else:
                print(f"manual_update.csv file not found in upload dir: {upload_dir}")
        print(f"========== iteration - {index} done ===========")
        index += 1

    if clean_up_flag :
        # deleting all files in upload directory
        assume.cleanUP()
    print(f"========== script execution done ===========")


main()