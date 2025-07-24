import os
import sys
import csv
import json
import glob
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import  logging

#custom imports
from FwLibrary import diff_checker

class Assume:
    def __init__(self):
        pass

    def create_csv_file(self, path):
        open(path, 'w').close()
        print(f"created csv file: {path}")

    def create_aup_script_file(self, path):
        script_file = Path(path)
        script_file.parent.mkdir(parents=True, exist_ok=True)
        script_file.touch()
        print(f"created AUP script file: {path}")

    def clean_up(self):
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

def load_env(file_path: str):
    """ this function is for loading ENV """
    # checking if file exists
    if not os.path.exists(file_path):
        print(">>> ENV file id not exist at path: ", file_path)
        sys.exit(1)

    with open(file_path, 'r') as envFile:
        env = json.load(envFile)
        print ("ENV Loaded from file: ", file_path)
        return env

def threshold_check(value):
    """ @value: threshold value coming from ENV file """
    if not value:
        print(">>> Threshold is not set in ENV file.")
        value = 101
    else:
        int(value) if not isinstance(value, int) else None
    print(f"threshold is: {value} ")
    return value


def clean_csv(path: str):
    """
    Processes the given users CSV:
    - If the file exists:
      - Removes the header (first line)
      - Writes the result back to the same file with Unix-style line endings
    """
    if os.path.isfile(path):
        print(path)
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()[1:]  # Skip header
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            for line in lines:
                f.write(line.rstrip('\r\n') + '\n')
    else:
        print(f"File {path} does not exist.")

def sort_csv_by_column(prev_file_path, current_file_path, prev_out, current_out, column_name=None):
    
    # sorting prev file
    with open(prev_file_path, mode='r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        prev_file_data = list(reader)

    if not prev_file_data:
        print("CSV file is empty")

    # Use provided column or default to the first column
    sort_key = column_name if column_name else reader.fieldnames[0] # type: ignore
    if sort_key not in reader.fieldnames: # type: ignore
        raise ValueError(f"Column '{sort_key}' not found in CSV headers")
 
    sorted_prev_fle = sorted(prev_file_data, key=lambda x: x[sort_key])    
    print(f"file: {prev_file_path} sorted by: {sort_key}")

    with open(prev_out, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames) # type: ignore
        writer.writeheader()
        writer.writerows(sorted_prev_fle)
    print(f"sorted file saved at: {prev_out}")
    print("########################################################################")
  
    # sorting current file
    with open(current_file_path, mode='r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        current_file_data = list(reader)

    if not current_file_data:
        print("CSV file is empty")
    
    # Use provided column or default to the first column
    try:
        sort_key = column_name if column_name else reader.fieldnames[0] # type: ignore
        if sort_key not in reader.fieldnames: # type: ignore
            raise ValueError(f"Column '{sort_key}' not found in CSV headers")
    except Exception as e:
        print(f"Error: {e}")

    sorted_current_file = sorted(current_file_data, key= lambda x : x[sort_key])
    print(f"file {current_file_path} sorted by: {sort_key}")

    with open(current_out, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames) # type: ignore
        writer.writeheader()
        writer.writerows(sorted_current_file)

    print(f"sorted file saved at: {current_out}")
    print("#################################[ sorting done ]####################################")

def generate_add_discard_files(current_csv, previous_csv, add_csv, discard_csv):
    def read_rows(filepath):
        with open(filepath, newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
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
    logging.getLogger(__name__)
    env_file_path= '../env/fwDevEnv.json'
    assume = Assume()
    clean = input("Would you like to clean up after execution ? (yes/no): ")
    clean_up_flag = True if clean.lower() == 'yes' else False

    # load env if path is given in command line as arg-1 else load default.
    if len(sys.argv) > 1:
        env_file_path = sys.argv[1]
        env = load_env(env_file_path)
    else:
        env = load_env(env_file_path)

    # checking threshold
    threshold = threshold_check(env['threshold'])

    # preparation for while loop
    number_of_company = int(env['number_of_company'])
    all_companies = env['all_companies'] # this ia array of json
    src_dir = env['source_parent_dir']
    trgt_dir = env['target_parent_dir']

    index = 0
    print(len(all_companies))
    # iterating till value of number_of_company
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
        
        upload_dir = os.path.join(src_dir, company_name, 'UPLOAD')
        os.makedirs(upload_dir, exist_ok=True)

        print(f"upload dir created: {upload_dir}")

        ########################################################################################
        # creating _complete file
        complete_file_name = f'{company_name}_complete'
        complete_file = os.path.join(upload_dir, complete_file_name)
        open(complete_file, 'w').close()
        ########################################################################################

        complete_file_path = [os.path.basename(file) for file in glob.glob(os.path.join(upload_dir, "*_complete"))]
        print(complete_file_path)

        for file in complete_file_path:
            print(f"file: {file}")
            file_name = os.path.basename(file)
            prefix = file_name.split('_')[0]
            print(f"prefix: {prefix}")    

            user_csv = os.path.join(upload_dir, f'{prefix}_users.csv')
            ########################################################################################
            # creating csv file
            assume.create_csv_file(user_csv)
            #########################################################################################
            
            if not os.path.exists(user_csv):
                print(f"user_csv file not found: {user_csv}")
                sys.exit(1)
            else:
                print(f"your user_csv located at: {user_csv}")

            # checking utf-8 encoding
            assume.check_utf8(user_csv)

            # FileWatcherExpressEnhancement Step 1
            # storing paths of previous_check , previous_manual_check

            previous_check = os.path.join(trgt_dir, company_name , 'users.csv')
            previous_manual_check = os.path.join(trgt_dir, company_name , 'manual_users.csv')
            
            # creating previous_check and previous_manual_check files if not exist, if exist then skip creating, handling legacy mode too 
            if len(sys.argv) > 1  and sys.argv[2].lower() == 'legacy':
                print("running legacy version...")
                threshold = 101
                previous_check = Path(os.path.join(trgt_dir, company_name , 'blank.csv'))
                previous_manual_check = Path(os.path.join(trgt_dir, company_name , 'manual_blank.csv'))

                """ from pathlib import Path

                pathlib .Path().mkdir(parents=True, exist_ok=True) is a modern and clean way to create files,
                this way ensure that directory exists before creating file for preventing of errors.
                """
                previous_check.parent.mkdir(parents=True, exist_ok=True)
                previous_check.touch()
                
                previous_manual_check.parent.mkdir(parents=True, exist_ok=True)
                previous_manual_check.touch()
            else:
                previous_check = Path(previous_check)
                previous_manual_check = Path(previous_manual_check)
                
                if not previous_check.exists():
                    previous_check.parent.mkdir(parents=True, exist_ok=True)
                    previous_check.touch()
                    print(f"Created blank: {previous_check} file for first time run ")
                else: 
                    print(f"file detected at : {previous_check}")
                
                if not previous_manual_check.exists():
                    previous_manual_check.parent.mkdir(parents=True, exist_ok=True)
                    previous_manual_check.touch()
                    print(f"Created blank: {previous_manual_check} file for first time run ")
                else:
                    print(f"file detected at : {previous_manual_check}")
            
            # store paths of previous_check and previous_manual_check in a dictionary 

            # copy previous_check to previous_file
            previous_file = os.path.join(trgt_dir, company_name , 'previous.csv')
            shutil.copy2(previous_check, previous_file)

            # upload script
            # /usr/local/bin/python3.6 /home/ubuntu/allegoAdmin/scripts/channels/AUPChannelUploader.py ${channel_id} ${user_csv}

            ###########################################################################################
            script_file = './home/ubuntu/allegoAdmin/scripts/channels/AUPChannelUploader.py'
            assume.create_aup_script_file(script_file)
            channel_id = str(env["channel_id"])
            py = 'python3'
            ##########################################################################################

            cmd = [py, script_file, channel_id, user_csv]
            print(f"cmd: {cmd}")
            try: 
                subprocess.run(cmd)
            except Exception as e:
                print(f"Error: {e}")

            # Check estimated differences first CASE is based on exit codes. Skip if threshold = 101
            if threshold < 101:
                percent = diff_checker(previous_file , user_csv , threshold, "location",company_id, company_name )
                
                if percent == 1:
                    print("Diff Checker has stopped AUP")

                    # Remove *_complete files from UPLOAD directory
                    for f in os.listdir(upload_dir):
                        if f.endswith("_complete"):
                            os.remove(os.path.join(upload_dir, f))

                    # Move user_csv to aupFailureArchive directory
                    dest_file = os.path.join(trgt_dir, "aupFailureArchive", f"{prefix}_{company_name}")
                    shutil.move(user_csv, dest_file)
                    sys.exit(1)
                else:
                    print("Diff Checker has passed.")

            # copy previous_manual_check to previous_manual_file
            previous_manual_file = os.path.join(trgt_dir, company_name , 'manual_previous.csv')
            shutil.copy2(previous_manual_check, previous_manual_file)
            # End FileWatcherExpressEnhancement Step 1
            
            # Run dos2unix here to clean up hidden character else the match will fail
            # Create expected users.csv from new file
            # user_csv set further up for UTF8 checks
            clean_csv(user_csv)

            # FileWatcherExpressEnhancement Step 2
            # Compare new users.csv and previous.csv to populate staging tables.
            # If users.csv was blank from Step 1, addUpdate.csv should be a 1:1 copy of users.csv and disable.csv should be empty.

            # save addUpdate.csv and disable.csv file paths
            add_update_csv = os.path.join(trgt_dir, company_name, "addUpdate.csv")
            disable_csv = os.path.join(trgt_dir, company_name, "disable.csv")

            ################################################################################

            assume.create_csv_file(add_update_csv) if not os.path.exists(add_update_csv) else None
            assume.create_csv_file(disable_csv) if not os.path.exists(disable_csv) else None

            ################################################################################

            # rename both files to prevent overriding the data
            try: 
                os.rename(add_update_csv, f"{add_update_csv}.{prefix}")
                os.rename(disable_csv, f"{disable_csv}.{prefix}")
                print("Renaming done.")
            except FileNotFoundError as e:
                print(f"Error renaming files: {add_update_csv} and {disable_csv} with exception {e}")
                sys.exit(1)

            ##################################################
            # creating temp sort dir where we will save sort files
            # then process for add and discard
            # then delete this sort dir
            sort_dir = os.path.join(trgt_dir, company_name, "sort")
            os.makedirs(sort_dir, exist_ok=True)
            prev_out = os.path.join(sort_dir, "prevSorted.csv")
            curr_out = os.path.join(sort_dir, "currSorted.csv")
            ##################################################

            sort_csv_by_column(previous_file, previous_check,prev_out, curr_out,"EmployeeNumber")
            # in this function we are passing the sorted files to generate add and discard files
            generate_add_discard_files(prev_out,curr_out,add_update_csv,disable_csv)

            #################################################
            # clean temporary sort dir
            shutil.rmtree(sort_dir)
            print("temp sort dir was removed")
            #################################################
            # now we have addUpdate.csv and disable.csv files

            # Older implementation of groups.csb and userGroupMemberShip.csv
            src_groups_csv=os.path.join(upload_dir, f"{prefix}_groups.csv")
            trgt_groups_csv=os.path.join(trgt_dir,company_name,f"groups.csv")
            if os.path.exists(src_groups_csv):
                # mv & tail
                shutil.move(src_groups_csv, trgt_groups_csv)
                clean_csv(trgt_groups_csv)
            else:
                print(f"groups.csv file not found in upload dir: {upload_dir}")

            src_user_group_membership_csv= os.path.join(upload_dir, f"{prefix}_userGroupMembership.csv") 
            trgt_user_group_membership_csv= os.path.join(trgt_dir,company_name,f"userGroupMembership.csv")
            if os.path.exists(src_user_group_membership_csv):
                # mv
                shutil.move(src_user_group_membership_csv, trgt_user_group_membership_csv)
                # tail
                clean_csv(trgt_user_group_membership_csv)
            else:
                print(f"userGroupMembership.csv file not found in upload dir: {upload_dir}")
            
            # sunovion Legacy implementation
            src_fbt_user_csv=os.path.join(upload_dir, f"{prefix}_fbt_users.csv")
            trgt_fbt_user_csv = os.path.join(trgt_dir,company_name,f"fbt_users.csv")
            if os.path.exists(src_fbt_user_csv):
                # mv
                shutil.move(src_fbt_user_csv, trgt_fbt_user_csv)
                # tail
                clean_csv(trgt_fbt_user_csv)
            else:
                print(f"fbt_users.csv file not found in upload dir: {upload_dir}")

        # Manual File Support
            src_manual_user_csv= os.path.join(upload_dir, f"{prefix}_manual_users.csv")
            trg_manual_user_csv = os.path.join(trgt_dir, company_name, "manual_users.csv")
            if os.path.exists(src_manual_user_csv):
                # mv
                shutil.move(src_manual_user_csv, trg_manual_user_csv)
                # tail
                clean_csv(trg_manual_user_csv)
            else:
                print(f"manual_users.csv file not found in upload dir: {upload_dir}")
        
        # FileWatcherExpressEnhancement Step 3 - Manual Files
            manual_update_csv = os.path.join(trgt_dir, company_name, "manual_update.csv")
            if os.path.exists(manual_update_csv):
                # mv
                shutil.move(manual_update_csv, manual_update_csv)
            else:
                print(f"manual_update.csv file not found in upload dir: {upload_dir}")
            
            # comm -13 <(sort $previous_manual_file) <(sort ${TARGET_PARENT_DIR}${COMPANY[$index]}/manual_users.csv) > ${TARGET_PARENT_DIR}${COMPANY[$index]}/manual_update.csv
            cmd = [
                    "bash",
                    "-c",
                    "comm -13 <(sort {prev}) <(sort {curr}) > {out}".format(
                        prev=previous_manual_file,
                        curr=trg_manual_user_csv,
                        out=manual_update_csv
                    )
                ]
            try: 
                subprocess.run(cmd, check=True)
            except Exception as e:
                print(f"Error: {e}")
            
            #rm _complete file 
            src_complete_csv = os.path.join(upload_dir, f"{prefix}_complete.csv")
            if os.path.exists(src_complete_csv):
                # rm 
                shutil.rmtree(src_complete_csv)

            #
		    # now run the script to load the data into staging tables in the db
		    #
            allego_home = env["allego_home"]
            stage_script = os.path.join(allego_home, "conf", "import", "customer", company_name, f"setup_{company_name}.sql")

            #####################################################################
            # assumption file is there but, for now make this sql sh file
            stage_script = Path(stage_script)
            if not os.path.exists(stage_script):
                stage_script.parent.mkdir(parents=True, exist_ok=True)
                stage_script.touch()
                print(f"file : {stage_script} created")
            else:
                print(f"file : {stage_script} exists")
            ####################################################################

            print(f"calling {stage_script} {trgt_dir}{company_name}")
            try:
                subprocess.run([stage_script, f"{trgt_dir}{company_name}"], check=True)
            except Exception as e:
                print(f"Exception : {e}")
            
            #
		    # now run the script to load from staging into production - run this one asynchronously
		    #
            load_script = os.path.join(allego_home, "scripts", "import.sh")

            ########################################################################
            load_script = Path(load_script)
            if not os.path.exists(load_script):
                load_script.parent.mkdir(parents=True, exist_ok=True)
                load_script.touch()
                print(f"file : {load_script} created")
            else:
                print("loadFile is exist")
            # copy 
            shutil.copy2("../playGround.sh" , load_script)
            print("load sh file loaded to avoid error")
            #######################################################################

            print(f"calling {load_script} {company_id}")
            try:
                subprocess.Popen([load_script, str(company_id)])
            except Exception as e:
                print(f"Exception : {e}")

        print(f"========== iteration - {index} done ===========")
        index += 1

    if clean_up_flag :
        # deleting all files in upload directory
        assume.clean_up()
    print(f"========== script execution done ===========")

main()