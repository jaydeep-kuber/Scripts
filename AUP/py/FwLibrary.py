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
    diff_count = subprocess.check_output(["bash", "-c", cmd_common], text=True).strip()

    # Get total line count of current file
    cmd_curr = ["wc", "-l", str(temp_c)]
    diff_current_count = subprocess.check_output(cmd_curr, text=True).split()[0]

    # Get total line count of previous file
    cmd_prev = ["wc", "-l", str(temp_p)]
    diff_previous_count = subprocess.check_output(cmd_prev, text=True).split()[0]

    print("Common rows:", diff_count)
    print("Current file line count:", diff_current_count)
    print("Previous file line count:", diff_previous_count)

    # email headers
    FROM="From: Ad-Hoc Reports System <no-reply@allego.com>"
    TO="jira@allego.atlassian.net"
    CC="operations@allego.com"
    DATE= datetime.now()
    # return 0
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
        setCompanyOnHold(scriptFile, CONFIG,cid)

if __name__ == "__main__":
    prevFile = "./home/ubuntu/allegoAdmin/workdir/solarcity/previous.csv"
    userFile = "./home/ubuntu/allegoAdmin/workdir/solarcity/users.csv"
    threshold = "5"
    loc = "123.456.789"
    cid = "14"
    cName = "comny"

    DiffChecker(prevFile, userFile, threshold, loc, cid, cName)  # call the function