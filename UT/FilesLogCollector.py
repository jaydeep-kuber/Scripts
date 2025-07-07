""" 
This is a simple script file which filter ERROR logs from all logs
"""

import os
import re
import sys
import time
import boto3
import json
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- File tracking ---
"""
    A dictionary to remember the last position (offset) for each log file.
    Prevents re-reading the same lines over and over.
"""
file_cursors = {}

# Extras
def makefile():
    # TODAY = datetime.now().strftime("%Y-%m-%d")
    containers = ["soil-api-gateway", "soil-okr"]
    for container in containers:
        os.makedirs(f"{LOG_ROOT}/{container}", exist_ok=True) if not os.path.exists(f"{LOG_ROOT}/{container}") else print("Directory exist")
        fileName = f"{container}_.log"
        file = os.path.join(f"{LOG_ROOT}/{container}", fileName)
        open(file, "w").close() if not os.path.exists(file) else print("file is there")

#main
def send_to_sqs(message):
    try:
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps({"log": message})
        )
        print(f"Sent to SQS: {message}")
    except Exception as e:
        print(f"Failed to send: {e}")

def read_new_lines(filepath):
    """ 
        If it's the first time seeing this file, we skip old content.
        We set cursor to end of file (like tail -f).
        This avoids reading logs that already happened.
    """
    if filepath not in file_cursors:
        file_cursors[filepath] = os.path.getsize(filepath) # rtn file size in bytes 10KB → returns 10240
        return  # first run, skip existing lines

    """ 
        We open the file, jump to last known position using seek().
        readlines() gets all new lines.
        f.tell() gets the new position — updated in file_cursors. 
    """
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        f.seek(file_cursors[filepath]) # moves file pointer to byte position 
        new_lines = f.readlines()
        file_cursors[filepath] = f.tell() # returns the current position in bytes

    for line in new_lines:
        if LOG_PATTERN.search(line):
            send_to_sqs(line.strip())

# --- Watchdog Handler ---
class LogChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith(".log"): # type: ignore
            return # We ignore folders or files that don’t end in .log.
        read_new_lines(event.src_path)

# --- Setup Watchdog Observer ---
def start_monitoring():
    observer = Observer()
    handler = LogChangeHandler()

    for container in CONTAINERS:
        log_dir = os.path.join(LOG_ROOT, container)
        today_file = os.path.join(log_dir, f"{container}_.log")

        if not os.path.exists(today_file):
            print(f"Log file not found: {today_file}")
            continue

        file_cursors[today_file] = os.path.getsize(today_file)
        observer.schedule(handler, path=log_dir, recursive=False)
        print(f"Watching: {today_file}")

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def config_loader(path):
    print("please provide a .json file") if not path.endswith(".json") else None


if __name__ == "__main__":
    
    REGION = 'ap-south-1'
    QUEUE_URL = ""
    sqs = boto3.client('sqs', region_name=REGION)
    
    # --- Config ---
    LOG_ROOT = "/home/jay/work/scripts/UT/logs/"
    CONTAINERS = ["soil-api-gateway", "soil-okr"]
    TODAY = datetime.now().strftime("%Y-%m-%d")
    LOG_PATTERN = re.compile(r'error|critical|fatal', re.IGNORECASE)

    config_path = sys.argv[1] if len(sys.argv) > 1 else sys.exit("Please provice a config.json in first arg...")
    print(f"Configuring from: {config_path} file")
    config_loader(config_path)
    start_monitoring()
    # makefile()