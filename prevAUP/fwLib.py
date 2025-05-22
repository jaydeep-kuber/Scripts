import os
import subprocess
import shutil
from datetime import datetime

def diffChecker(previousFile, usersCSV, threshold, location, cmpny, cid , lggr=None):
    if lggr:
        lg = lggr
        lg.info(f"Logger set for {os.path.basename(__file__)} ")
    lg.info("diffchecker started")

    diffCurrentCount=0
    diffPrevCount=0
    diffCount=0
    diffRatio=0
    myT=threshold
    server=location

    cid = cid
    temp_p = f'./tmp/diffprevious_{cid}.csv'
    temp_c = f'./tmp/diffcurrent_{cid}.csv'

    CONFIG = '/home/ubuntu/allegoAdmin/scripts/prod.json'
    lg.info(f"config path: {CONFIG}")
    
    if os.path.exists(temp_p):
        shutil.copyfile(previousFile, temp_p)
        lg.info(f"previous file copied to {temp_p}")
    
    if os.path.exists(temp_c):
        shutil.copyfile(usersCSV, temp_c)
        lg.info(f"current file copied to {temp_c}")
    
    try:
        subprocess.run(['dos2unix', temp_p], check=True)
        subprocess.run(['dos2unix', temp_c], check=True)
        lg.info("dos2unix done for both file")
    except Exception as e:
        lg.error(f"Exception in library dos2unix: {str(e)}")
    
    # diffcount

    try:
        # Line 1: comm with process substitution
        diff_count_cmd = f"comm -12 <(sort {temp_p}) <(sort {temp_c}) | wc -l"
        diffCount = subprocess.run(diff_count_cmd, shell=True, capture_output=True, text=True, executable="/bin/bash").stdout.strip()
        lg.info(f"Common lines count: {diffCount}")

        # Line 2: wc -l for current file
        diffCurrentCount = subprocess.run(["wc", "-l", temp_c], capture_output=True, text=True).stdout.strip().split()[0]
        lg.info(f"Log: fwLib: Current file lines: {diffCurrentCount}")

        # Line 3: wc -l for previous file
        diffPreviousCount = subprocess.run(["wc", "-l", temp_p], capture_output=True, text=True).stdout.strip().split()[0]
        lg.info(f"Log: fwLib: Previous file lines: {diffPreviousCount}")

    except Exception as e:
        lg.error(f"Exception in library diffcount: {str(e)}")
    
    diffCount = int(diffCount)
    diffCurrentCount = int(diffCurrentCount)
    
    FROM="From: Ad-Hoc Reports System <no-reply@allego.com>"
    TO="jira@allego.atlassian.net"
    CC="operations@allego.com" 
    DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Failure Case 1: "Empty" File
    if diffCurrentCount == 0:
        CASE_1_SUBJECT = f"AUP Changeset Warning-Empty File: {cmpny} - {DATE}"
        CASE_1_BODY = f"Empty file Detected for company: {cmpny}.  Check for a 0KB file or a _complete file without any paired users file."

        # send email
        cmd = [
                "aws", "ses", "send-email",
                "--from", "email-admin@allego.com",
                "--destination", '{"ToAddresses":["jira@allego.atlassian.net"]}',
                "--message", f"""{{"Subject":{{"Data":"{CASE_1_SUBJECT}"}},\
                "Body":{{"Text":{{"Data":"{CASE_1_BODY}"}}}}}}""",
                "--region", "us-east-1"
            ]
        mailCode = subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        lg.info(f"Email sent with exit code: {mailCode}")

        # company on hold 
        holdResult = subprocess.run(
            ["/usr/local/bin/python3.6", "/home/ubuntu/allegoAdmin/scripts/setCompanyOnHold.py", CONFIG, str(cid)],
            capture_output=True,  # Optional: capture stdout/stderr
            text=True             # Decode output as text instead of bytes
        )
        return 1   
    
    # Failure Case 2: Lots of missing Rows, not based on updates, very sensitive.
    if diffPrevCount > diffCurrentCount:
        CASE_2_SUBJECT = f"AUP Changeset Warning-Lots of missing Rows: {cmpny} - {DATE}"

        if diffPreviousCount == 0 : 
            diffRatio = 0
        else:
            diffRatio = int(((diffPrevCount - diffCurrentCount) / diffPrevCount) * 100)
        lg.info(f"PreviousCount > CurrentCount ratio: {round(diffRatio)}")

        if diffRatio > myT:
            CASE_2_BODY = f"Possible file truncation for company {cmpny}.  File size is significantly smaller than the last run file or is corrupted."

            # send email
            cmd = [
                "aws", "ses", "send-email",
                "--from", "email-admin@allego.com",
                "--destination", '{"ToAddresses":["jira@allego.atlassian.net"]}',
                "--message", f"""{{"Subject":{{"Data":"{CASE_2_SUBJECT}"}},\
                "Body":{{"Text":{{"Data":"{CASE_2_BODY}"}}}}}}""",
                "--region", "us-east-1"
            ]

            mailCode = subprocess.run(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            lg.info(f"Email sent with exit code: {mailCode}")

            # company on hold
            holdResult = subprocess.run(
                ["/usr/local/bin/python3.6", "/home/ubuntu/allegoAdmin/scripts/setCompanyOnHold.py", CONFIG, cid],
                capture_output=True,  # Optional: capture stdout/stderr
                text=True             # Decode output as text instead of bytes
            )
            return 1
        
    # Failure Case 3: Too many general changes

    # Prevent division by zero
    if diffCurrentCount == 0:
        diffRatio = 0
    else:
        diffRatio = int(((diffCurrentCount - diffCount) / diffCurrentCount) * 100)
        lg.info(f"CurrentCount > Count ratio: {diffRatio}")
    
    if diffRatio > myT:
        CASE_3_SUBJECT = f"AUP Changeset Warning-Too many general changes: {cmpny} - {DATE}"
        CASE_3_BODY = f"Possible file truncation for company {cmpny}. {diffRatio} percent of the file requires updating, which is greater than the current threshold value of {myT} percent."

        # send email
        cmd = [
            "aws", "ses", "send-email",
            "--from", "email-admin@allego.com ",
            "--destination", '{"ToAddresses":["jira@allego.atlassian.net"]}',
            "--message", f"""{{"Subject":{{"Data":"{CASE_3_SUBJECT}"}},\
            "Body":{{"Text":{{"Data":"{CASE_3_BODY}"}}}}}}""",
            "--region", "us-east-1"
        ]

        mailCode = subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        lg.info(f"Email sent with exit code: {mailCode}")

        # company on hold
        holdResult = subprocess.run(
            ["/usr/local/bin/python3.6", "/home/ubuntu/allegoAdmin/scripts/setCompanyOnHold.py", CONFIG, cid],
            capture_output=True,  # Optional: capture stdout/stderr
            text=True             # Decode output as text instead of bytes
        )
        return 1
    
    # Range of changes ok
    TO="lperrault@allego.com"
    SUBJECT=f"AUP Safe Launch Notification: {server}"
# Compose the message
    message = (
        f"{diffRatio} percent of the userbase is changing, less than the current threshold of "
        f"{myT} percent. AUP now running for Company: {cmpny}"
    )

    # Run the mutt command with sudo
    subprocess.run(
        ["sudo", "mutt", "-s", SUBJECT, "-e", f"my_hdr {FROM}", TO],
        input=message,
        text=True
    )
    return 0