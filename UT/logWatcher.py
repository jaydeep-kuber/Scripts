""" 
This is a simple script file which filter ERROR logs from all logs
"""

import os
import re
import sys
import time
import queue
import boto3
import json
import logging
import threading
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
error_q = queue.Queue()
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

def send_to_sns(message):
    pass

def email_msg_maker(line, buffer, stillCollecting):
    """ 
        re => 2025-07-09 14:43:52 + "ERROR"
        If line starts with timestamp AND contains "ERROR":
            If we were already collecting:
                - Finish previous error block - Push the block to queue - Clear buffer
            Start a new error block:
                - Add current line to buffer - Set collecting = True

        Else if line starts with timestamp (but no "ERROR"):
            If we were collecting:
                - Finish current error block - Push block to queue - Clear buffer - Set collecting = False
            Else:
                - Ignore the line

        Else (line has no timestamp):
            If collecting:
                - This line is part of current traceback - Append to buffer

        Return updated buffer and collecting flag 
    """

def read_new_lines(filepath):
    """ 
        If it's the first time seeing this file, we skip old content.
        We set cursor to end of file (like tail -f).
        This avoids reading logs that already happened.
    """
    logger.info(f"Reading new lines from: {filepath}")
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
        if TIMESTAMP_RE.search(line): # re for timestamp
            if LOG_PATTERN.search(line):
                sns.publish(
                TopicArn=TOPIC_ARN,
                Subject="🚨 Error Digest",
                Message=line.strip()
                )
            
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
    
    global REGION, TOPIC_ARN, LOG_FILES
    REGION = configs['REGION']
    TOPIC_ARN = configs['TOPIC_ARN']
    LOG_FILES = configs['LOG_FILES']

    return True

if __name__ == "__main__":
    # setting up logging
    setup_logging()
    logger = logging.getLogger("script")

    # setting up timer to prevent mail overhead
    COOLDOWN = 60  # in seconds
    last_sent_time = 0 # in seconds
    current_time = time.time()

    # define pattern using re. 
    # LOG_PATTERN = re.compile(r'error|critical|fatal', re.IGNORECASE)
    LOG_PATTERN = re.compile(r'error|exception|traceback|fatal|fail(ed)?|panic|crash|unhandled', re.IGNORECASE)

    TIMESTAMP_ERROR_RE = re.compile(r'^\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}.*ERROR', re.IGNORECASE)
    TIMESTAMP_RE = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}')

    # check if config file is provided
    config_path = sys.argv[1] if len(sys.argv) > 1 else sys.exit("Please provice a config.json in first arg...")
    logger.info(f"Using configuring from: {config_path} file")

    # Error Queue
    if config_loader(config_path):
        # sqs client
        # sqs = boto3.client('sqs', region_name=REGION)    
        sns = boto3.client('sns', region_name=REGION)
        logger.error("Failed to create SNS client...") if not sns else logger.info("SNS client created successfully.")
        start_monitoring()
    else:
        logger.error("Failed to load configuration.")
        sys.exit(1)