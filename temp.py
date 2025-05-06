# import shutil

# shutil.copy2('parentDir/sunovion/UPLOAD/sunovion_complete', 'parentDir/sunovion/UPLOAD/sunovion_users.csv')

import datetime
from helpers import helper
from utils import env_conf
import subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# helper.CSVfiller('users.csv', 'src_home/sunovion/UPLOAD/sunovion_users.csv', 20)

# def send_email(from_email, to_email, subject, body):
#     smtp_user = env_conf.SMTP_USER
#     smtp_pass = env_conf.SMTP_PASS
#     SMTP_SERVER = 'smtp.gmail.com' #'smtp.yourprovider.com'
#     SMTP_PORT = 587
    
#     print(f" -> SMTP_USER: {smtp_user}")
#     print(f" -> SMTP_PASS: {smtp_pass}")

#     # Create the message
#     msg = MIMEMultipart()
#     msg['From'] = from_email
#     msg['To'] = to_email
#     msg['Subject'] = subject

#     print(f" -> Sending email \n From: {from_email} \n To: {to_email} \n subject: {subject}")
#     print(f" -> body: {body}")
#     # Attach the body
#     msg.attach(MIMEText(body, 'plain'))

#     # Send the email
#     with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
#         server.starttls()
#         server.login(smtp_user, smtp_pass)
#         server.sendmail(from_email, to_email, msg.as_string())

# DATE = f"{datetime.datetime.now():%d-%m-%Y %H:%M:%S}"
# FROM_EMAIL = 'jayofficial085@gmail.com'
# TO_EMAIL = 'developerjay297@gmail.com'
# SUBJECT = f"Script testing mail. {DATE}"
# BODY = f"Hello, this is a test email sent from Python script. {DATE}"
# send_email(FROM_EMAIL, TO_EMAIL, SUBJECT, BODY)

CONFIG= 'config'
companyId = '1'
py_path = 'python3'
script_path = 'trg_home/ubuntu/allegoAdmin/scripts/'
script_name = 'setCompanyOnHold.py'
CMD = [py_path,script_path,script_name,CONFIG,companyId]

try:
    subprocess.run(CMD)
    print(f" >>>>> setCompanyOnHold.py script executed successfully.")
except subprocess.CalledProcessError as e:
    print(f"Error executing script: {e}")