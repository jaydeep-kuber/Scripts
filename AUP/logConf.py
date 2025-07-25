import  json
from logging.config import dictConfig

def setup_logging(path: str, filename: str):
    # load file
    with open(path, 'r') as logfile:
        log_conf = json.load(logfile)

    for handler in log_conf.get("handler", {}).values():
        if handler.get("filename") == '__LOGFILE__':
            handler['filename'] = filename
        log_conf["disable_existing_loggers"] = False
    dictConfig(log_conf)