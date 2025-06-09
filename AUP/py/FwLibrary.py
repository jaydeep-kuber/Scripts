import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

def sendMail(FROM, TO, subject, body, region=None):
    region = region if region else "us-east-1"
    
    # Build the command
    cmd = [
        "aws", "ses", "send-email",
        "--from", FROM,
        "--destination", f'{{"ToAddresses":["{TO}"]}}',
        "--message", f'{{"Subject":{{"Data":"{subject}"}},'
                     f'"Body":{{"Text":{{"Data":"{body}"}}}}}}',
        "--region", region
    ]

    # Run the command silently (suppress output like >/dev/null 2>&1)
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Email sent successfully.")
    except subprocess.CalledProcessError as e:
        print("Failed to send email:", e)

def setCompanyOnHold(filePath, CONFIG, cid):
#    /usr/local/bin/python3.6 /home/ubuntu/allegoAdmin/scripts/setCompanyOnHold.py ${CONFIG} ${cid}
    py = "python3"
    CMD = [py, filePath, CONFIG, cid]
    try:
        subprocess.run(CMD, check=True)
        print("Company on hold successfully.")
    except subprocess.CalledProcessError as e:  
        print(f"Exeprion : {e}")
    return 1       

def DiffChecker(prevFile, userFile, threshold, location, cid, cName):
    diffCurrentCount=0;
    diffPrevCount=0;
    diffCount=0;
    diffRatio=0;
    myT=threshold;
    server=location;
    CONFIG=Path("/home/ubuntu/allegoAdmin/scripts/prod.json")
    
    cid = cid
    temp_p = Path(f"/tmp/diffprevious_{cid}.csv") 
    temp_c = Path(f"/tmp/diffcurrent_{cid}.csv")

    shutil.rmtree(temp_p) if os.path.exists(temp_p) else None
    shutil.rmtree(temp_c) if os.path.exists(temp_c) else None

    # make empty 2 files
    temp_p.parent.mkdir(parents=True, exist_ok=True)
    temp_p.touch()

    temp_c.parent.mkdir(parents=True, exist_ok=True)
    temp_c.touch()

    # Copy files to tmp becauae dos2unix is annoying
    shutil.copy2(prevFile, temp_p)
    shutil.copy2(userFile, temp_c)

    try:
        # dos2unix is annoying so we copy to tmp
        subprocess.run(['dos2unix', temp_p], check=True)
        subprocess.run(['dos2unix', temp_c], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Exeption in FwLib : {e}")

    # Get number of common lines
    cmd_common = f"comm -12 <(sort {temp_p}) <(sort {temp_c}) | wc -l"
    diff_count = int(subprocess.check_output(["bash", "-c", cmd_common], text=True).strip())
    # diff_count = int (diff_count)

    # Get total line count of current file
    cmd_curr = ["wc", "-l", str(temp_c)]
    diff_current_count = int(subprocess.check_output(cmd_curr, text=True).split()[0])
    # diff_current_count = int(diff_current_count)

    # Get total line count of previous file
    cmd_prev = ["wc", "-l", str(temp_p)]
    diff_previous_count = int(subprocess.check_output(cmd_prev, text=True).split()[0])
    # diff_previous_count = int(diff_previous_count)

    print("Common rows:", diff_count)
    print("Current file line count:", diff_current_count)
    print("Previous file line count:", diff_previous_count)

    # email headers
    FROM="From: Ad-Hoc Reports System <no-reply@allego.com>"
    TO="jira@allego.atlassian.net"
    CC="operations@allego.com"
    DATE= datetime.now()

    #CASE-1    
    if diff_current_count == 0:
        CASE_1_SUBJECT = f"AUP Changeset Warning-Empty File: {cName} {DATE}"
        CASE_1_BODY=f"Empty file Detected for Company: {cName}.  Check for a 0KB file or a _complete file without any paired users file."
        sendMail(
            FROM="email-admin@allego.com",
            TO="jira@allego.atlassian.net",
            subject= CASE_1_SUBJECT,
            body=CASE_1_BODY
        )
    # Set Company on hold until the issue resolves
        scriptFile = Path("./home/ubuntu/allegoAdmin/scripts/setCompanyOnHold.py")
        ############ creating file before running script
        scriptFile.parent.mkdir(parents=True, exist_ok=True)
        if not scriptFile:
            scriptFile.touch()
            print("Company hold file creted")
        else:
            print("Comapany hold file is present")
        ##################################################
        setCompanyOnHold(scriptFile, CONFIG,cid)
        return 1
    
    # Failure Case 2: Lots of missing Rows, not based on updates, very sensitive.
    if diff_previous_count > diff_current_count:
        CASE_2_SUBJECT=f"AUP Changeset Warning-Lots of missing Rows: {cName} {DATE}"
        
        if diff_previous_count != 0:
            diff_ratio = int(((diff_previous_count - diff_current_count) / diff_previous_count) * 100)
        else:
            diff_ratio = 0  #
        
        if diff_ratio > myT:
            CASE_2_BODY=f"Possible file truncation for company {cName}.  File size is significantly smaller than the last run file or is corrupted."
            sendMail(
                FROM="email-admin@allego.com",
                TO="jira@allego.atlassian.net",
                subject= CASE_2_SUBJECT,
                body=CASE_2_BODY
            )   
        # Set Company on hold until the issue resolves
        scriptFile = Path("./home/ubuntu/allegoAdmin/scripts/setCompanyOnHold.py")
        setCompanyOnHold(scriptFile, CONFIG,cid)
        return 1

    # Failure Case 3: Too many general changes

    if diff_current_count != 0:
        diff_ratio = int(((diff_current_count - diff_count) / diff_current_count) * 100)
    else:
        diff_ratio = 0  

    if diff_ratio > myT:
        CASE_3_SUBJECT=f"AUP Changeset Warning-Too many general changes: ${cName} ${DATE}";
        CASE_3_BODY=f"Too many changes detected for company ${cName}. ${diffRatio} percent of the file requires updating, which is greater than the current threshold value of ${myT} percent.";

        sendMail(
                FROM="email-admin@allego.com",
                TO="jira@allego.atlassian.net",
                subject= CASE_3_SUBJECT,
                body=CASE_3_BODY
            )   
        # Set Company on hold until the issue resolves
        scriptFile = Path("./home/ubuntu/allegoAdmin/scripts/setCompanyOnHold.py")
        setCompanyOnHold(scriptFile, CONFIG,cid)
        return 1

    # Range of changes ok
    TO="lperrault@allego.com"
    SUBJECT="AUP Safe Launch Notification: ${server}"
    message = (
        f"{diff_ratio} percent of the userbase is changing, "
        f"less than the current threshold of {myT} percent. "
        f"AUP now running for Company: {cName}"
    )
    # Use subprocess to send the email
    try:
        subprocess.run(
            ['sudo', 'mutt', '-s', SUBJECT, '-e', f"my_hdr {FROM}", TO],
            input=message.encode(),
            check=True
        )
    except subprocess.CalledProcessError as e:
        print("Failed to send email:", e)
        sys.exit(1)

    return 0

# if __name__ == "__main__":
#     prevFile = "./home/ubuntu/allegoAdmin/workdir/solarcity/previous.csv"
#     userFile = "./home/ubuntu/allegoAdmin/workdir/solarcity/users.csv"
#     threshold = "5"
#     loc = "123.456.789"
#     cid = "14"
#     cName = "comny"

#     DiffChecker(prevFile, userFile, threshold, loc, cid, cName)  # call the function