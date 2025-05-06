""" 
* ===========================================================================
* Copyright 2015, Allego Corporation, MA USA
*
* This file and its contents are proprietary and confidential to and the sole
* intellectual property of Allego Corporation.  Any use, reproduction,
* redistribution or modification of this file is prohibited except as
* explicitly defined by written license agreement with Allego Corporation.
* ===========================================================================

* ===========================================================================
fileWatcher.sh

watch a set of directories for inbound files used for user provisioning.
when files come in, move to a separate directory, and kick off import scripts
* ===========================================================================
 
AUP diff checker diffChecker (previousfile, currentfile, threshold,Server_location) 

"""
# py packages
import datetime
import os
import shutil

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import subprocess
import sys
# custom imports
from utils import env_conf

def dos2unix(file_path):
    with open(file_path, 'rb') as f:
        content = f.read()

    # Replace CRLF (\r\n) with LF (\n)
    content = content.replace(b'\r\n', b'\n')

    with open(file_path, 'wb') as f:
        f.write(content)
    print(f"lib -> file {os.path.basename(file_path)}Converted to Unix format.")

def send_email(from_email, to_email, subject, body):
    smtp_user = env_conf.SMTP_USER
    smtp_pass = env_conf.SMTP_PASS
    SMTP_SERVER = 'smtp.gmail.com' #'smtp.yourprovider.com'
    SMTP_PORT = 587
    # Create the message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach the body
    msg.attach(MIMEText(body, 'plain'))

    # Send the email
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(from_email, to_email, msg.as_string())

# this is main function
def diffChecker(threshold,Server_location, previousfile, currentfile, idx):

    # Initialize variables
    curntFile_lineCount=0
    prevFile_lineCount=0
    prev_curnt_diffCount=0
    myThreshold=threshold
    server_location=Server_location

    CONFIG="trg_home/ubuntu/allegoAdmin/scripts/prod.json" 

    # Get the list of companies from the environment configuration
    company = env_conf.COMPANY[idx].strip()
    companyId = env_conf.COMPANY_ID[idx].strip()
    
    tempFileLoc = 'trg_home/ubuntu/temp/'
      # Temporary file location
    if not os.path.exists(tempFileLoc):
        os.makedirs(tempFileLoc)
        print(f"lib -> temp dir created for local") 

    # Make temp files split by companyId
    tempPrevFileName=f"{tempFileLoc}diffPrev_{company}_{companyId}.csv"
    tempCurrFileName=f"{tempFileLoc}diffCurnt_{company}_{companyId}.csv"

    # Create temporary files at the current location
    if not os.path.isfile(tempPrevFileName):
        open(tempPrevFileName, 'w').close()  # Create an empty file
    # copy the previous file to the temp file
    shutil.copyfile(previousfile, tempPrevFileName)
    
    if not os.path.isfile(tempCurrFileName):
        open(tempCurrFileName, 'w').close()  # Create an empty file
    # copy the current file to the temp file
    shutil.copyfile(currentfile, tempCurrFileName)

    dos2unix(tempPrevFileName)
    dos2unix(tempCurrFileName)

    # Get the line count of the current file
    with open(tempCurrFileName, 'r') as f:
        for line in f:
            curntFile_lineCount += 1
    print(f"lib -> Current file line count: {curntFile_lineCount}")
    
    # Get the line count of the previous file
    with open(tempPrevFileName, 'r') as f:
        for line in f:
            prevFile_lineCount += 1
    print(f"lib -> Previous file line count: {prevFile_lineCount}")
    
    # Get the difference count
    with open(tempPrevFileName, 'r') as f1, open(tempCurrFileName, 'r') as f2:
        for line1, line2 in zip(f1, f2):
            if line1 != line2:
                prev_curnt_diffCount += 1
    print(f"lib -> Previous and current file difference count: {prev_curnt_diffCount}")
   

    ################ FAIL CASE AND MAIL CASE ######################
    FROM_EMAIL = 'jayofficial085@gmail.com'
    TO_EMAIL = 'developerjay297@gmail.com'
    SUBJECT = f"Script testing mail."
    DATE = f"{datetime.datetime.now():%d-%m-%Y %H:%M:%S}"

    py_path = 'python3'
    script_path = 'trg_home/ubuntu/allegoAdmin/scripts/'
    script_name = 'setCompanyOnHold.py'
    CMD = [py_path,script_path,script_name,CONFIG,companyId]
   
    """ 
        >>> Failure Case 1: "Empty Current File"
    """
    if curntFile_lineCount == 0:        
        case1_subject = f"AUP Changeset Warning-Empty File: {company} and {DATE}"
        case1_body = f"Empty file Detected for Company: {company}.  Check for a 0KB file or a _complete file without any paired users file."
        
        # Send email
        send_email(FROM_EMAIL, TO_EMAIL, case1_subject, case1_body)
        print(f"Email sent to {TO_EMAIL} with subject: {case1_subject}")

        # run the script
        try:
            subprocess.run(CMD)
            print(f"lib -> setCompanyOnHold.py script executed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error executing script: {e}")

        sys.exit(1)
    
    """ 
        >>> # Failure Case 2: Lots of missing Rows, not based on updates, very sensitive.
    """
    if prevFile_lineCount > curntFile_lineCount:
        case2_subject = f"AUP Changeset Warning-Lots of missing Rows: {company} and {DATE}"
        ratio = ((prevFile_lineCount - curntFile_lineCount) / prevFile_lineCount * 100)
        print(f"PreviousCount > CurrentCount ratio: {round(ratio)}")
        
        if ratio > myThreshold:
            case2_body = f"Possible file truncation for company {company}.  File size is significantly smaller than the last run file or is corrupted."
            # Send email
            send_email(FROM_EMAIL, TO_EMAIL, case2_subject, case2_body)
            print(f"Email sent to {TO_EMAIL} with subject: {case2_subject}")

            # run the script
            try:
                subprocess.run(CMD)
                print(f"lib -> setCompanyOnHold.py script executed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"Error executing script: {e}")

            sys.exit(1)
    
    """
        >>> # Failure Case 3: Too many general changes
            # Compute Diffs/RowCount ratio, send value back to filewatcher to evaluate.
    """
    
    ratio = (curntFile_lineCount - prev_curnt_diffCount) / curntFile_lineCount * 100
    print(f" Case 3 ratio: {round(ratio)}")

    if ratio > myThreshold:
        case3_subject = f"AUP Changeset Warning-Too many general changes: {company} and {DATE}"
        case3_body = f"Too many changes detected for company {company} ${prev_curnt_diffCount} percent of the file requires updating, which is greater than the current threshold value of ${myThreshold} percent."

        # Send email
        send_email(FROM_EMAIL, TO_EMAIL, case3_subject, case3_body)
        print(f" Email sent to {TO_EMAIL} with subject: {case3_subject}")
        # run the script
        try:
            subprocess.run(CMD)
            print(f"lib -> setCompanyOnHold.py script executed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error executing script: {e}")
        sys.exit(1)

    print(f"lib -> No issues detected for company: {company}, AUP process can continue.")
