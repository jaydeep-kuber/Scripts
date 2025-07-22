import json
import logging
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

from py.FwLibrary import diff_checker

ENV = {}

# Global logger
logger = logging.getLogger("FileWatcher")
logger.setLevel(logging.DEBUG)  # Or INFO

formatter = logging.Formatter(
        fmt="[%(asctime)s] | %(levelname)s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

# consol handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
    logger.addHandler(console_handler)
# Store current handler so we can remove it when switching
current_handler = None
def setup_logging(filename: str):
    global current_handler

    # Remove existing file handler if any
    if current_handler:
        logger.removeHandler(current_handler)
        current_handler.close()

    file_handler = RotatingFileHandler(
        filename,
        mode='a'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    current_handler = file_handler

    return logger

class FileMapManager:
    def __init__(self, home_path: str):
        self.home_path = Path(home_path).expanduser().resolve()
        self.file_map = {} # {"filename":"path of file till dir"}

    def add_file(self, filename: str , absolute_path: str):
        """
            Add a file-to-directory mapping.
            Validates that filename has no slashes and path is not absolute.
        """

        if '/' in filename:
            raise ValueError("Filename must not contain slash, check your filename.")
        if not Path(absolute_path).is_absolute():
            raise ValueError("Expected absolute file path")

        self.file_map[filename] = Path(absolute_path)
        logger.debug(f"[+] File mapping done, Key: '{filename}', Value: '{absolute_path}'")

    def create_files(self):
        """
            Creates each file in the map under home_path/relative_dir.
            Skips if the file already exists.
        """
        # creating Home
        self.home_path.mkdir(parents=True, exist_ok=True) if not self.home_path.exists() else print(f"[*] Existing home path -> {self.home_path}")

        for file , dir_path in self.file_map.items():
            file_path = dir_path / file

            print(f"[DEBUG] fullpath -> {file_path}")
            dir_path.mkdir(parents=True, exist_ok=True)

            if file_path.exists():
                logger.info(f"[*] Existing file: {file_path}")
                continue
            file_path.touch()

    def clean_up(self, del_files: list[str]):
        """
            This function clean files created bt this class.
        """

        # making path for each file
        for key, dir_path in self.file_map.items():
            if key in del_files:
                file_path = Path(dir_path) / key
                if file_path.exists() and file_path.is_file():
                    try:
                        file_path.unlink()
                        logger.debug(f"[✘] Deleted file from path: {file_path}")
                    except Exception as e:
                        logger.error(f"[ERROR] Error deleting {file_path}: {e}")
                else:
                    logger.error(f"[!] Skipping: File does not exist or is not a file → {file_path}")

def config_loader(path: str):
        """
        Load config from a JSON file using pathlib after validating:
        - Path exists
        - File is a .json
        - File is not empty
        - File contains valid JSON
        - JSON content is a dictionary
        """

        global ENV
        config_path = Path(path)

        print(f"[INFO] Loading config from: {config_path}")

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        if not config_path.is_file():
            raise ValueError(f"Path is not a file: {config_path}")

        if config_path.suffix != '.json':
            raise ValueError(f"Invalid file extension (expected .json): {config_path}")

        if config_path.stat().st_size == 0:
            raise ValueError(f"Config file is empty: {config_path}")

        try:
            with config_path.open('r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {config_path}: {e}")

        if not isinstance(data, dict):
            raise ValueError(f"JSON content must be an object (dict), got {type(data)}")

        ENV = data
        return True

def utf8_check(file_path: Path) -> bool:
    """
    Checks if a file is valid UTF-8 encoded.
    :param file_path: Path object pointing to the file.
    :return: True if valid UTF-8, False otherwise.
    """
    if not file_path.exists() or not file_path.is_file():
        logger.error(f"[ERROR] File not found or invalid: {file_path}")
        return False

    try:
        with file_path.open('rb') as f:
            # Attempt to decode the entire file as UTF-8
            f.read().decode('utf-8')
        logger.debug(f"[INFO] UTF-8 Check Passed for {file_path}")
        return True
    except UnicodeDecodeError as e:
        logger.error(f"[ERROR] UTF-8 Check Failed for {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"[ERROR] Unexpected error during UTF-8 check: {e}")
        return False

def main():
    logfile_name = f"filewatcher.log.{datetime.now().strftime('%Y.%m.%d')}"
    setup_logging(logfile_name)
    project_root = "/home/jay/work/scripts/AUP"

#--- Replicate server dir structure for local. [remove this block in dev/prod ] ---
    server_home = "/home/jay/work/scripts/AUP/home/ubuntu/"
    # class object
    manager = FileMapManager(server_home)

    env_file = "./env/fwDevEnv.json"
    if config_loader(env_file):
        if len(ENV) == 0:
            exit("conf loaded... but not populated")
    else:
        logger.error("Something went wrong in loading config ")
    company_names = [ name["cmp_name"] for name in ENV.get("all_companies")]
    # ["company_1", "company_2"]all_companies
    print(company_names)
    company_ids = [ids["cmp_id"] for ids in ENV.get("all_companies", [])]

    src_upload_dir_lst = [f'/home/jay/work/scripts/AUP/home/{company}/UPLOAD/' for company in company_names]
    # ["/home/jay/work/scripts/AUP/home/company_1/UPLOAD/","/home/jay/work/scripts/AUP/home/company_2/UPLOAD/"]

    _cmp_filenames_lst = [f"{f}_complete" for f in company_names]
    # ["company_1_complete", "company_2_complete"]

    # adding all these file to file map {filename,abs_path}
    for i, name in enumerate(company_names):
        manager.add_file(_cmp_filenames_lst[i], src_upload_dir_lst[i])

    # creating AUPChannelUploader.py will need later
    manager.add_file("AUPChannelUploader.py", f"{server_home}/allegoAdmin/scripts/channels/")
    # creating files
    manager.create_files()

    # clean files
    # manager.clean_up(['log.txt','log1.txt', 'log2.txt' ])

# --- END ---

# --- From this point script is starting ---
    logger.info(f"running filewatcher {datetime.now().strftime('%Y.%m.%d')}")

# --- args ---
    # Check for env_file argument
    if len(sys.argv) > 1:
        env_file = sys.argv[1]
        logger.debug(f"Using env file: {env_file}...")

# --- threshold ---
    # Default threshold if not set to 101 in order to ignore threshold functions
    # getting threshold value form.
    threshold = ENV.get('threshold') or 101
    logger.debug(f"Threshold is set to: {threshold}")

# --- while loop ---
    i = 0
    while i < ENV.get("number_of_company"):
        logger.info(f"checking {i}, {datetime.now()}")

        company_name = company_names[i]
        company_id = company_ids[i]
        logger.info(f"company= {company_name}")
        logger.info(f"companyID= {company_id}")

        # number of company and company in list are same?
        logger.warning("value of 'number_of_company' attribute and number of company resent in list are not same ") if ENV.get("number_of_company") != len(company_names) else None

    # --- for loop ---
        upload_dir = Path(src_upload_dir_lst[i])
        for idx, _cmp_file in enumerate(upload_dir.glob("*_complete")):
            file_name = _cmp_file.name
            prefix = file_name[:-9]  # Removes last 9 characters
            users_csv = upload_dir / f"{prefix}_users.csv"

            # --- utf8 ---
            users_csv = Path(users_csv)
            match company_id:
                case 218 | 120:
                    logger.debug("[INFO] Checking UTF-8 format...")
                    if not utf8_check(users_csv):
                        logger.error("[FATAL] Exiting due to invalid UTF-8 characters.")
                        exit(1)
                case _:
                    logger.info(f"[INFO] Skipping UTF-8 check for company ID: {company_id}")

        # --- FileWatcherExpressEnhancement Step 1 ---
            target_parent_dir = ENV.get("target_parent_dir", ".")
            Path(target_parent_dir)
            channel_id = ENV.get("channel_id")

            # Define Paths for Previous Files
            # --- assuming we have prev files in dev---
            # creating for local
            manager.add_file("users.csv",f"{target_parent_dir}/{company_name}")
            manager.add_file("manual_users.csv",f"{target_parent_dir}/{company_name}")
            manager.create_files()

            previous_check = Path(target_parent_dir) /company_name/"users.csv"
            previous_manual_check = Path(target_parent_dir)/company_name/"manual_users.csv"

            if len(sys.argv) > 2 and sys.argv[2].lower() == "legacy":
                logger.debug("Running Legacy Version with full file")
                # Legacy runs as manual; override Threshold
                threshold = 101
                previous_check = Path(target_parent_dir) / company_name / "users.csv"
                previous_manual_check = Path(target_parent_dir) /company_name/"manual_users.csv"
                previous_check.touch()
                previous_manual_check.touch()
            else:
                if previous_check.exists():
                    logger.debug("A previous Users.csv run as been detected")
                else:
                    previous_check.touch()
                    logger.debug("Created blank Users.csv previous file for first run")

                if previous_manual_check.exists():
                    logger.debug("Created blank manual_Users.csv previous file for first run")
                else:
                    previous_manual_check.touch()
                    logger.debug("Created blank manual_Users.csv previous file for first run")

            # Copy previous users.csv (or blank one you just touched, or blank one you forced in there), as previous.csv
            # Copy previous manual_users.csv (or blank one you just touched, or blank one you forced in there), as manual_previous.csv
            previous_file = Path(target_parent_dir) / company_name / "previous.csv"
            previous_manual_file = Path(target_parent_dir) / company_name / "manual_previous.csv"

            # --- assuming it is present ---
            # but creating previous file for local
            # previous_file.touch() if not previous_file.exists() else logger.log(f"Previous file Exist... at {previous_file}")
            # previous_manual_file.touch() if not previous_manual_file.exists() else logger.log(f"Previous manual file Exist... at {previous_manual_file}")

            shutil.copy2(previous_check, previous_file)
            shutil.copy2(previous_manual_check, previous_manual_file)

            # Upload file to channel in AUP Company
            python_exe = "/usr/bin/python3"
            script_path = "/home/ubuntu/allegoAdmin/scripts/channels/AUPChannelUploader.py"
            users_csv = Path("/UPLOAD/client-218/users_complete")

            # Run command
            result = subprocess.run(
                [python_exe, script_path, str(channel_id), str(users_csv)],
                capture_output=True,
                text=True,
            )

            # Check result
            if result.returncode == 0:
                logger.debug("Script executed successfully:")
                # print(result.stdout)
            else:
                logger.debug("Script failed:")
                # print(result.stderr)

            # Check estimated differences first CASE is based on exit codes. Skip if threshold = 101
            if threshold < 101:
                # precent = diff_checker(previous_file, users_csv, threshold, ENV.get("threshold", 1), company_id, company_name)
                precent =  0
                if precent == 1 :
                    logger.debug("Diff Checker has stopped AUP...")
                    # Remove complete file and archive Users file when AUP fails

                    # 1. Remove *_complete files
                    for file in upload_dir.glob("*_complete"):
                        try:
                            file.unlink()
                        except Exception as e:
                            logger.error(f"Failed to delete {file}: {e}")

                    # 2. Move users_csv to failure archive with prefix
                    aup_failure_archive_path = target_parent_dir / "aupFailureArchive" / f"{prefix}_{company_name}"
                    try:
                        shutil.move(str(users_csv), str(aup_failure_archive_path))
                    except Exception as e:
                        logger.error(f"Failed to move file: {e}")
                    exit(1)
                else:
                    logger.debug("Diff Checker has passed...")

        # --- End FileWatcherExpressEnhancement Step 1 ---



        i += 1
    manager.clean_up(_cmp_filenames_lst)


if __name__ == "__main__":
    main()