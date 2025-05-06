# py package imports
import os
import glob
import sys
import shutil
import subprocess
import random
# custom imports
from fwLibary import diffChecker
from utils import env_conf, logger
from helpers import helper

# ======================[envs]======================================

companies = env_conf.COMPANY # company names
company_ides = env_conf.COMPANY_ID # company ids
number_of_companies = int(env_conf.NUMBER_OF_COMPANIES)

source_parent_dir = env_conf.SOURCE_PARENT_DIR #~/work/scripts/home/
target_parent_dir = env_conf.TARGET_PARENT_DIR # ~/work/scripts/home/ubuntu/allegoAdmin/workdir/

threshold = int(env_conf.MYTHRESHOLD) # default value is 30


#getting current file name.
filename = os.path.basename(__file__) 

## check for override of env vars passed in as an arg
""" 
	for now this sections is pending
"""

## Default threshold if not set to 101 in order to ignore threshold functions
if threshold == '' or threshold is None:
	print("threshold is unset")
	threshold = 101  
print(f"threshold is set to '{threshold}'")

index = 0
while index < number_of_companies:
	company = companies[index]
	company_id = int(company_ides[index])

	print(f" >>>>> Company: {company}")
	print(f" >>>>> Company ID: {company_id}")

	#
   	# check to see if complete file is present
   	#
	
	# creating working directory for the company, for testing purposes
	# source
	if not os.path.exists(source_parent_dir):
		os.makedirs(source_parent_dir)
		print(f" >>>>> SOURCE DIR CREAED")

	# target
	if not os.path.exists(target_parent_dir):
		os.makedirs(target_parent_dir)
		print(f" >>>>> TARGET DIR CREAED")
	
	# creating upload directory for the company in source parent dir
	UPLOAD_DIR = f'{source_parent_dir}/{company.strip()}/UPLOAD'
	
	if not os.path.exists(UPLOAD_DIR):
		os.makedirs(UPLOAD_DIR)
		print(f" >>>>> UPLOAD DIR CREAED")
	
	# search_pattern = os.path.join(source_parent_dir, company.strip(), 'UPLOAD', '*_complete')
	# search_pattern = '*_complete'
	# print(f">>>>> FILE PATTERN: {search_pattern}")

	# creating _complete files 
	_file = f"{company}_complete"
	helper.make_cmpFile(UPLOAD_DIR,_file)

	# _complete_files = [os.path.basename(file) for file in glob.glob(f'{dest_Dir}/*_complete')]

	matched_files = [os.path.basename(file).strip() for file in glob.glob(f'{UPLOAD_DIR}/*_complete')]
	print(f" >>>>> MATCHED FILES: {matched_files}")
	
	offset = -9
	for i , f in enumerate(matched_files):
		print(f" >>>>> FILE: {f}")
		prefix = f[:offset]	
		print(f" >>>>> PREFIX: {prefix}")
		
		_file = f"{prefix}_users"
		userCSV = helper.makeCSV(UPLOAD_DIR,_file)
		helper.CSVfiller('users.csv', userCSV)
		print(f" >>>>> USER CSV: {userCSV}")

		# UTF-8 Check (equivalent to shell's iconv)
		if company_id in (218, 120):
			print("Checking UTF8 format")
			try:
				with open(userCSV, 'r', encoding='utf-8') as f:
					f.read()  # Try reading entire file
					print("UTF-8 Check Passed")
			except UnicodeDecodeError:
				print("UTF-8 Formatting has invalid characters; exiting")
				sys.exit(1)

		# TASK-1:
		# Make two new target files, by comparisons to the previous run's version of users.csv
		# addUpdate.csv		# disable.csv 

		# TASK-2:
		# If no users.csv file exists in this workdirectory (first run of AUP or a hard reset), 
		# touch one as blank, This task also needs to be done for manual files. 

		# TASK-3:
		# Get previous file.  At this step, 
			# it should always be users.csv inside the workdir 
			# (minus the header). If it doesn't exist, touch a blank one.
		
		# LEASY - TASK:
		# If user provides "legacy" flag, make a blank previous.csv to reset

		# we need to create two new target files, for that we need previousversion of users.csv. 
		# check if previous file exists, if not then create a blank file.

		""" Start Step 1  """

		# (assumption) -> company directory is already created in the target parent dir.
		# but for development purposes we are creating it here.
		if not os.path.exists(f"{target_parent_dir}/{company.strip()}"):
			os.makedirs(f"{target_parent_dir}/{company.strip()}")
			print(f" >>>>> TARGET COMPANY DIR CREAED")
		
		# generate random number between 5 to 20
		# number = random.randint(5, 20) 
		# check if previous file exists, if not then create a blank file.
		prev_UserFilePath = f"{target_parent_dir}/{company.strip()}/users.csv"
		if not os.path.exists(prev_UserFilePath):
			# create a blank file
			open(prev_UserFilePath, 'w').close()
			helper.CSVfiller('users.csv', prev_UserFilePath)
			print(f" >>>>> PREVIOUS USER FILE CREAED")
		else:
			helper.CSVfiller('users.csv', prev_UserFilePath)
		# do same for prev manual file
		
		prev_ManualUserFilePath = f"{target_parent_dir}/{company.strip()}/manual_users.csv"
		if not os.path.exists(prev_ManualUserFilePath):
			# create a blank file
			open(prev_ManualUserFilePath, 'w').close()
			helper.CSVfiller('users.csv', prev_ManualUserFilePath)
			print(f" >>>>> PREVIOUS MANUAL USER FILE CREAED")
		else:
			helper.CSVfiller('users.csv', prev_ManualUserFilePath)

		# (assumption) -> check if previous.csv exists, if not then create a blank file.
		prevUserCSV = f"{target_parent_dir}/{company.strip()}/previous.csv"
		if not os.path.exists(prevUserCSV):
			# create a blank file
			open(prevUserCSV, 'w').close()
			print(f" >>>>> PREVIOUS FILE CREAED at {prevUserCSV}")
			shutil.copy2(prev_UserFilePath, prevUserCSV)
		else:
			shutil.copy2(prev_UserFilePath, prevUserCSV)
		print(">>>>> USERS.CSV copied to PREVIOUS.CSV")

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
			print(f" >>>>> {script_name} script executed successfully.")
		except subprocess.CalledProcessError as e:
			print(f"Error executing script: {e}")

		# Check estimated differences first CASE is based on exit codes. Skip if threshold = 101
		if threshold < 101:
			server_location = 'ap-south-1' # just to ignore warning, this is temporary value.
			percent = diffChecker(threshold, server_location, prevUserCSV, userCSV, index)	
			# percent = 1
			if percent == 1 :
				print("DIFF CHECKER HAS STOPPED THE AUP PROCESS")
				
				# Remove _complete file and archive Users file when AUP fails
				# remove _complete file
				os.remove(f"{UPLOAD_DIR}/*_complete")
				print(f" >>>>> {_file} file removed")

				# move the file to archive location
				archive_dir = 'aupFailureArchive'
				archive_locatoin = f"{target_parent_dir}/{archive_dir}/arch_{company.strip()}"
				if not os.path.exists(archive_locatoin):
					os.makedirs(archive_locatoin)
					print(f" >>>>> ARCHIVE DIR CREAED")
				shutil.move(userCSV, archive_locatoin)
				print(f" >>>>> {userCSV} file moved to archive location")
				sys.exit(1)

		""" End Step 1 """
	print("-----------------------------------")

	index += 1