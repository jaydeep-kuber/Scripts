import json
import os
from logging.config import  dictConfig

def setup_logging():
    # --- vars
    logging_json = "logging.json"
    with open(logging_json, 'r') as logfile:
        config = json.load(logfile)

    # auto create log dir if it doesn't exist
    for handler in config.get("handlers", {}).values():
        if handler.get("class") == "logging.FileHandler":
            log_file = handler.get("filename")
            if log_file:
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
    dictConfig(config)