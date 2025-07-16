import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

def send_mail(from_email, to_email, subject, body):
    region = "us-east-1"
    
    # Build the command
    cmd = [
        "aws", "ses", "send-email",
        "--from", from_email,
        "--destination", f'{{"ToAddresses":["{to_email}"]}}',
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

def set_company_on_hold(filepath, prod_config, cid):

    py = "python3"
    cmd = [py, filepath, prod_config, cid]
    try:
        subprocess.run(cmd, check=True)
        print("Company on hold successfully.")
    except subprocess.CalledProcessError as e:  
        print(f"Exception occurred : {e}")
    return 1       

def diff_checker(prev_file, user_file, threshold, location, cid, cmp_name):
    server=location
    prod_config=Path("/home/ubuntu/allegoAdmin/scripts/prod.json")
    
    cid = cid
    temp_p = Path(f"/tmp/diff_previous_{cid}.csv") 
    temp_c = Path(f"/tmp/diff_current_{cid}.csv")

    shutil.rmtree(temp_p) if os.path.exists(temp_p) else None
    shutil.rmtree(temp_c) if os.path.exists(temp_c) else None

    # make empty 2 files
    temp_p.parent.mkdir(parents=True, exist_ok=True)
    temp_p.touch()

    temp_c.parent.mkdir(parents=True, exist_ok=True)
    temp_c.touch()

    # Copy files to tmp because dos2unix is annoying
    shutil.copy2(prev_file, temp_p)
    shutil.copy2(user_file, temp_c)

    try:
        # dos2unix is annoying so we copy to tmp
        subprocess.run(['dos2unix', temp_p], check=True)
        subprocess.run(['dos2unix', temp_c], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Exception in FwLib : {e}")

    # Get number of common lines
    cmd_common = f"comm -12 <(sort {temp_p}) <(sort {temp_c}) | wc -l"
    diff_count = int(subprocess.check_output(["bash", "-c", cmd_common], text=True).strip())

    # Get total line count of current file
    cmd_curr = ["wc", "-l", str(temp_c)]
    diff_current_count = int(subprocess.check_output(cmd_curr, text=True).split()[0])

    # Get total line count of previous file
    cmd_prev = ["wc", "-l", str(temp_p)]
    diff_previous_count = int(subprocess.check_output(cmd_prev, text=True).split()[0])

    print("Common rows:", diff_count)
    print("Current file line count:", diff_current_count)
    print("Previous file line count:", diff_previous_count)

    # email headers
    from_email="From: Ad-Hoc Reports System <no-reply@allego.com>"
    to_email="jira@allego.atlassian.net"
    cc="operations@allego.com"
    date= datetime.now()

    #CASE-1    
    if diff_current_count == 0:
        case_1_subject = f"AUP Changeset Warning-Empty File: {cmp_name} {date}"
        case_1_body=f"Empty file Detected for Company: {cmp_name}.  Check for a 0KB file or a _complete file without any paired users file."
        send_mail(
            from_email="email-admin@allego.com",
            to_email="jira@allego.atlassian.net",
            subject= case_1_subject,
            body=case_1_body
        )
        # Set Company on hold until the issue resolves
        script_file = Path("./home/ubuntu/allegoAdmin/scripts/set_company_on_hold.py")
        ############ creating file before running script
        script_file.parent.mkdir(parents=True, exist_ok=True)
        if not script_file:
            script_file.touch()
            print("Company hold file created")
        else:
            print("Company hold file is present")
        ##################################################
        set_company_on_hold(script_file, prod_config,cid)
        return 1
    
    # Failure Case 2: Lots of missing Rows, not based on updates, very sensitive.
    if diff_previous_count > diff_current_count:
        case_2_subject=f"AUP Changeset Warning-Lots of missing Rows: {cmp_name} {date}"
        
        if diff_previous_count != 0:
            diff_ratio = int(((diff_previous_count - diff_current_count) / diff_previous_count) * 100)
        else:
            diff_ratio = 0  #
        
        if diff_ratio > threshold:
            case_2_body=f"Possible file truncation for company {cmp_name}.  File size is significantly smaller than the last run file or is corrupted."
            send_mail(
                from_email="email-admin@allego.com",
                to_email="jira@allego.atlassian.net",
                subject= case_2_subject,
                body=case_2_body
            )   
        # Set Company on hold until the issue resolves
        script_file = Path("./home/ubuntu/allegoAdmin/scripts/set_company_on_hold.py")
        set_company_on_hold(script_file, prod_config,cid)
        return 1

    # Failure Case 3: Too many general changes

    if diff_current_count != 0:
        diff_ratio = int(((diff_current_count - diff_count) / diff_current_count) * 100)
    else:
        diff_ratio = 0  

    if diff_ratio > threshold:
        case_3_subject=f"AUP Changeset Warning-Too many general changes: ${cmp_name} ${date}"
        case_3_body=f"Too many changes detected for company ${cmp_name}. ${diff_ratio} percent of the file requires updating, which is greater than the current threshold value of ${threshold} percent."

        send_mail(
                from_email="email-admin@allego.com",
                to_email="jira@allego.atlassian.net",
                subject= case_3_subject,
                body=case_3_body
            )   
        # Set Company on hold until the issue resolves
        script_file = Path("./home/ubuntu/allegoAdmin/scripts/set_company_on_hold.py")
        set_company_on_hold(script_file, prod_config,cid)
        return 1

    # Range of changes ok
    to_email="lperrault@allego.com"
    subject=f"AUP Safe Launch Notification: ${server}"
    message = (
        f"{diff_ratio} percent of the userbase is changing, "
        f"less than the current threshold of {threshold} percent. "
        f"AUP now running for Company: {cmp_name}"
    )
    # Use subprocess to send the email
    try:
        subprocess.run(
            ['sudo', 'mutt', '-s', subject, '-e', f"my_hdr {from_email}", to_email],
            input=message.encode(),
            check=True
        )
    except subprocess.CalledProcessError as e:
        print("Failed to send email:", e)
        sys.exit(1)

    return 0