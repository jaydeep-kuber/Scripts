import os
import json
import sys
import glob
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

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



        print(f"========== iteration - {index} done ===========")
        index += 1

    if clean_up_flag :
        # deleting all files in upload directory
        assume.cleanUP()
    print(f"========== script execution done ===========")


main()