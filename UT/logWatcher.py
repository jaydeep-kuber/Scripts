""" 
This is a simple script file which filter ERROR logs from all logs
"""

import os
import re
import sys
import time
import boto3
import json
import logging
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from logging.config import dictConfig

# --- File tracking ---
"""
    A dictionary to remember the last position (offset) for each log file.
    Prevents re-reading the same lines over and over.
"""
file_cursors = {}

# Extras
def makefile():
    for file in LOG_FILES:        
        open(file, "w").close() if not os.path.exists(file) else print("file is there")

# main
def setup_logging():
    # open json file
    with open('logging_conf.json', 'r') as f:
        log_conf = json.load(f)

    # auto configure logging dir
    for handler in log_conf.get('handlers', {}).values():
        if handler.get('class') == 'logging.FileHandler':
            log_file = handler.get('filename')
            if log_file:
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
    # apply logging configuration
    dictConfig(log_conf)

def send_to_sqs(message):
    try:
        sqs.send_message(
            QueueUrl=SQS_URL,
            MessageBody=json.dumps({"log": message})
        )
        logger.info(f"Message sent to SQS: {message}")
    except Exception as e:
        logger.error(f"Failed to send message with: {e}")

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
    logger.info("Starting log file monitoring...")
    for file in LOG_FILES:
        if not os.path.exists(file):
            logger.warning(f"Log file not found: {file}")
            continue

        file_cursors[file] = os.path.getsize(file)
        observer.schedule(handler, path=file, recursive=False)
        logger.info(f"Monitoring: {file}")

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def config_loader(path):
    sys.exit("please provide a .json file") if not path.endswith(".json") else None
    sys.exit("404: file not found... may you have mistak in path") if not os.path.exists(path)  else None
    
    #open json file
    with open(path, 'r') as f:
        configs = json.load(f)
    
    global REGION, SQS_URL, LOG_FILES
    REGION = configs['REGION']
    SQS_URL = configs['SQS_URL']
    LOG_FILES = configs['LOG_FILES']

    return True

if __name__ == "__main__":
    setup_logging()
    LOG_PATTERN = re.compile(r'error|critical|fatal|GET', re.IGNORECASE)
    logger = logging.getLogger("script")
    config_path = sys.argv[1] if len(sys.argv) > 1 else sys.exit("Please provice a config.json in first arg...")
    logger.info(f"Using configuring from: {config_path} file")

    if config_loader(config_path):
    # sqs client
        sqs = boto3.client('sqs', region_name=REGION)    
        start_monitoring()
    else:
        logger.error("Failed to load configuration.")
        sys.exit(1)