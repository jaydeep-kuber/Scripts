""" 
This is a simple script file which filter ERROR logs from all logs
"""

import os
import sys
import boto3
import json
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
REGION = 'ap-south-1'
QUEUE_URL = os.getenv("SQS_URL_STD")

sqs_client = boto3.client('sqs', region_name=REGION)

# Extras
def makefile(loc):
    TODAY = datetime.now().strftime("%Y-%m-%d")
    fileName = f"{TODAY}.log"
    file = os.path.join(loc, fileName)
    open(file, "w").close() if not os.path.exists(file) else print("file is there")

def send_to_sqs(message):
    try:
        sqs_client.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps({"log": message})
        )
        print(f"Sent to SQS: {message}")
    except Exception as e:
        print(f"Failed to send: {e}")

# filelogscanner.py


def scan_logs(logDir, pattern):
    TODAY = datetime.now().strftime("%Y-%m-%d")

    if not os.path.isdir(logDir):
        print(f"Log directory not found: {logDir}")
        return

    # Step 1: Find today's log files
    found_any = False
    for filename in os.listdir(logDir):
        if filename.endswith(f"{TODAY}.log"):
            found_any = True
            full_path = os.path.join(logDir, filename)
            print(f"Scanning: {full_path}")
            
            if os.path.getsize(full_path) == 0:
                    print(f"File is empty: {full_path}")
                    return
            
            try:
                with open(full_path, "r", encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if pattern.search(line):
                            send_to_sqs(line)
            except Exception as e:
                print(f"Failed to read file {full_path}: {e}")

    if not found_any:
        print(f" No log files for today ({TODAY}) found in {logDir}")
        return

if __name__ == "__main__":
    # --- Config ---
    LOG_DIR = "logs"
    LOG_PATTERN = re.compile(r'error|critical|fatal', re.IGNORECASE)
    scan_logs(LOG_DIR, LOG_PATTERN)
    # makefile(LOG_DIR)