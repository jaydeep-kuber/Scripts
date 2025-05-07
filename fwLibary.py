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
    print(f"Log: fwLib: file {os.path.basename(file_path)}Converted to Unix format.")

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

def count_lines_safe(file_path):
    """
    Safely counts lines in a file. Returns line count or -1 if file not found.
    """
    if not os.path.isfile(file_path):
        print(f"Error: File '{file_path}' does not exist!")
        return -1
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        return -1

import os

def read_sorted_lines(file_path):
    """
    Reads lines from file, strips newlines, sorts them.
    Returns sorted list or empty list if file missing.
    """
    if not os.path.isfile(file_path):
        print(f"Error: File '{file_path}' does not exist!")
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
            return sorted(lines)
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        return []

# this is main function
def diffChecker(threshold,Server_location, previousfile, currentfile, companyId):

    # Initialize variables
    diffCurrentCount=0
    diffPrevCount=0
    diffCount=0;
    diffRatio=0;
    myThreshold=threshold
    server_location=Server_location

    tempFileLoc = 'trg_home/ubuntu/temp/'
      # Temporary file location
    if not os.path.exists(tempFileLoc):
        os.makedirs(tempFileLoc)
        print(f"Log: fwLib: temp dir created for local") 

    if not os.path.exists('trg_home/ubuntu/allegoAdmin/scripts'):
        os.makedirs('trg_home/ubuntu/allegoAdmin/scripts')
        print(f"Log: fwLib: scripts dir created for local")

    CONFIG="trg_home/ubuntu/allegoAdmin/scripts/prod.json" 
    # Check if the configuration file exists
    if not os.path.isfile(CONFIG):
        open(CONFIG, 'w').close()  # Create an empty file:
        print(f"Log: fwLib: Configuration file created at {CONFIG}")

    # Get the list of companies from the environment configuration
    
    cid=companyId
    temp_p=f'trg_home/ubuntu/temp/diffprevious_${cid}.csv';
    temp_c=f'trg_home/ubuntu/temp/diffcurrent_${cid}.csv';

    # Create temporary files at the current location
    if not os.path.isfile(temp_p):
        open(temp_p, 'w').close()  # Create an empty file
    # copy the previous file to the temp file
    shutil.copyfile(previousfile, temp_p)
    
    if not os.path.isfile(temp_c):
        open(temp_c, 'w').close()  # Create an empty file
    # copy the current file to the temp file
    shutil.copyfile(currentfile, temp_c)

    dos2unix(temp_p)
    dos2unix(temp_c)

    # # Get the line count of the current file using wc -l equivalent
    # diffCurrentCount = sum(1 for _ in open(temp_c, 'r'))

    # # Get the line count of the previous file using wc -l equivalent
    # diffPrevCount = sum(1 for _ in open(temp_p, 'r'))
    
    lines_p = read_sorted_lines(temp_p)
    lines_c = read_sorted_lines(temp_c)

    diffCount = len(set(lines_p).intersection(lines_c))
    print(f"Common lines count: {diffCount}")


    diffCurrentCount = count_lines_safe(temp_c)
    diffPrevCount = count_lines_safe(temp_p)    
    print(f"Log: fwLib: Current file lines: {diffCurrentCount}")
    print(f"Log: fwLib: Previous file lines: {diffPrevCount}")
   

    # ################ FAIL CASE AND MAIL CASE ######################
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
    if diffCurrentCount == 0:        
        case1_subject = f"AUP Changeset Warning-Empty File: {companyId} and {DATE}"
        case1_body = f"Empty file Detected for companyId: {companyId}.  Check for a 0KB file or a _complete file without any paired users file."
        
        # Send email
        send_email(FROM_EMAIL, TO_EMAIL, case1_subject, case1_body)
        print(f"LOG: fwLib: Email sent to {TO_EMAIL} with subject: {case1_subject}")

        # run the script
        try:
            subprocess.run(CMD)
            print(f"LOG: fwLib: setCompanyOnHold.py script executed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error LOG fwLib: executing script: {e}")

        sys.exit(1)
    
    """ 
        >>> # Failure Case 2: Lots of missing Rows, not based on updates, very sensitive.
    """
    if diffPrevCount > diffCurrentCount:
        case2_subject = f"AUP Changeset Warning-Lots of missing Rows: {companyId} and {DATE}"
        ratio = ((diffPrevCount - diffCurrentCount) / diffPrevCount) * 100
        print(f"LOG: fwLib: PreviousCount > CurrentCount ratio: {round(ratio)}")
        
        if ratio > myThreshold:
            case2_body = f"Possible file truncation for company {companyId}.  File size is significantly smaller than the last run file or is corrupted."
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
    
    ratio = (diffCurrentCount - diffCount) / diffCurrentCount * 100
    print(f" Case 3 ratio: {round(ratio)}")

    if ratio > myThreshold:
        case3_subject = f"AUP Changeset Warning-Too many general changes: {companyId} and {DATE}"
        case3_body = f"Too many changes detected for company {companyId} ${diffCount} percent of the file requires updating, which is greater than the current threshold value of ${myThreshold} percent."

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

    print(f"lib -> No issues detected for company: {companyId}, AUP process can continue.")
