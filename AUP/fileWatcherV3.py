import json
import logging
import shlex
import sys
import stat
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

from py.FwLibrary import diff_checker

ENV = {}

# Global logger

# --- Global Logger Setup ---
# This setup is done once when the script starts.
logger = logging.getLogger("FileWatcher")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    fmt="[%(asctime)s] | %(levelname)s | %(name)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
# Ensures we don't add handlers multiple times if this module were imported elsewhere.
if not logger.handlers:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# This will hold the current file handler so we can change it per company.
current_file_handler = None

def setup_logging(log_path: str):
    """Sets up or switches the file handler for logging."""
    Path(log_path)
    global current_file_handler
    if current_file_handler:
        logger.removeHandler(current_file_handler)
        current_file_handler.close()

    # Use a rotating file handler for robustness in production.
    file_handler = RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=3, mode='a')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    current_file_handler = file_handler

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

def skip_header(src_path, dest_path):
    with open(src_path, 'r', encoding='utf-8') as src_file:
        lines = src_file.readlines()[1:]  # skip the first line
    with open(dest_path, 'w', encoding='utf-8') as dest_file:
        dest_file.writelines(lines)

def dos2unix(path):
    with open(path, 'rb') as file:
        content = file.read()
    content = content.replace(b'\r\n', b'\n')
    with open(path, 'wb') as file:
        file.write(content)

def generate_add_update_csv(previous_file, current_file, output_file):
    """
    Generate addUpdate.csv: lines that are in current_file but not in previous_file.
    """
    # Convert paths to Path objects
    previous_file = Path(previous_file)
    current_file = Path(current_file)
    output_file = Path(output_file)

    try:
        # Read and sort both files (strip newlines and spaces)
        with previous_file.open('r', encoding='utf-8') as f:
            previous_lines = sorted(set(line.strip() for line in f if line.strip()))

        with current_file.open('r', encoding='utf-8') as f:
            current_lines = sorted(set(line.strip() for line in f if line.strip()))

        # Find lines that are in current but not in previous
        add_update_lines = sorted(set(current_lines) - set(previous_lines))

        # Write result
        with output_file.open('w', encoding='utf-8') as f:
            for line in add_update_lines:
                f.write(line + '\n')

        logger.info(f"[+] addUpdate written to: {output_file}")

    except Exception as e:
        logger.error(f"[!] Error generating addUpdate file: {e}")

def generate_disable_file(previous_file, current_file, output_file):
    """
    Generate disable.csv: lines that were in previous_file but not in current_file.
    """
    previous_file = Path(previous_file)
    current_file = Path(current_file)
    output_file = Path(output_file)

    try:
        with previous_file.open('r', encoding='utf-8') as f:
            previous_lines = sorted(set(line.strip() for line in f if line.strip()))

        with current_file.open('r', encoding='utf-8') as f:
            current_lines = sorted(set(line.strip() for line in f if line.strip()))

        # Find lines that were removed (present in previous but not in current)
        disabled_lines = sorted(set(previous_lines) - set(current_lines))

        with output_file.open('w', encoding='utf-8') as f:
            for line in disabled_lines:
                f.write(line + '\n')

        logger.info(f"[+] disable.csv written to: {output_file}")

    except Exception as e:
        logger.info(f"[!] Error generating disable file: {e}")

def generate_manual_update_csv(previous_file, current_file, output_file):
    """
    Generate manual_update.csv containing lines present in current manual file but not in previous.
    Then, remove the *_complete file after processing.
    """
    previous_file = Path(previous_file)
    current_file = Path(current_file)
    output_file = Path(output_file)

    try:
        # Read and sort unique lines from each file
        with previous_file.open('r', encoding='utf-8') as f:
            previous_lines = sorted(set(line.strip() for line in f if line.strip()))

        with current_file.open('r', encoding='utf-8') as f:
            current_lines = sorted(set(line.strip() for line in f if line.strip()))

        # Get lines that are only in current file (new/updated)
        new_lines = sorted(set(current_lines) - set(previous_lines))

        # Write to output
        with output_file.open('w', encoding='utf-8') as f:
            for line in new_lines:
                f.write(line + '\n')

        logger.info(f"[+] manual_update.csv written to: {output_file}")

    except Exception as e:
        print(f"[!] Error during manual update generation: {e}")

def make_sql_executable(sql_path: str) -> bool:
    """
    Ensure the .sql file exists, has a shebang, and is executable.
    Returns True if ready to execute.
    """
    sql_file = Path(sql_path)
    logger.info(f"Making: {sql_file} executable in 'make_sql_executable' func")
    if not sql_file.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")
    if not sql_file.is_file():
        raise ValueError(f"Not a valid file: {sql_path}")

    # Read first line to check for shebang
    with sql_file.open("r") as f:
        first_line = f.readline().strip()

    if not first_line.startswith("#!"):
        raise ValueError(f"Missing shebang in {sql_path}. Got: {first_line}")

    # Add executable permission if missing
    st = os.stat(sql_path)
    if not bool(st.st_mode & stat.S_IXUSR):
        os.chmod(sql_path, st.st_mode | stat.S_IXUSR)

    return True

def run_sql_script(script_path: str, argument: str) -> str:
    """
    Run the SQL script with given argument using subprocess.
    Returns stdout output.
    Raises CalledProcessError if it fails.
    """
    script = Path(script_path)

    # Add executable permission if missing
    st = os.stat(script_path)
    if not bool(st.st_mode & stat.S_IXUSR):
        os.chmod(script_path, st.st_mode | stat.S_IXUSR)

    if not script.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    if not os.access(script_path, os.X_OK):
        raise PermissionError(f"Script is not executable: {script_path}")

    # MYSQL_CMD = "mysql CoreDB -u <user> -p <password> -h <DB-URL>"
    result = subprocess.run(
        [str(script), argument],
        capture_output=True,
        text=True,
        check=True  # raises CalledProcessError on failure
    )
    return result.stdout.strip()

def run_shell_script(script_path: str, argument: str) -> str:
    """
    Run the shell script with given argument using subprocess.
    Returns stdout output.
    Raises CalledProcessError if it fails.
    """
    script = Path(script_path)

    if not script.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    if not os.access(script_path, os.X_OK):
        raise PermissionError(f"Script is not executable: {script_path}")

    result = subprocess.run(
        [str(script), argument],
        capture_output=True,
        text=True,
        check=True  # raises CalledProcessError on failure
    )
    return result.stdout.strip()

def main():
    env_file = "./env/fwDevEnv.json"
    # loading config to access global ENV
    if config_loader(env_file):
        if len(ENV) == 0:
            exit("conf loaded... but not populated")
    else:
        logger.error("Something went wrong in loading config ")

    logfile_root = Path("/home/jay/work/scripts/AUP/home/ubuntu/logs")
    logfile_root.mkdir(parents=True, exist_ok=True)
    date_time = datetime.now().strftime('%Y.%m.%d')
    logfile_name = f"{logfile_root}/filewatcher.log.{date_time}"
    setup_logging(logfile_name)

    # static declaration
    # project_root = "/home/jay/work/scripts/AUP/"
    server_home = "/home/jay/work/scripts/AUP/home/ubuntu/"

    # class object
    manager = FileMapManager(server_home)


    # static from env file
    source_root = Path(ENV["source_parent_dir"])
    target_root = Path(ENV["target_parent_dir"])
    allego_home = Path(ENV["allego_home"])

    company_names = [ name["name"] for name in ENV.get("all_companies")]
    # ["company_1", "company_2"]all_companies
    # company_ids = [ids["cmp_id"] for ids in ENV.get("all_companies", [])]

    src_upload_directory_lst = [f'/home/jay/work/scripts/AUP/home/{company}/UPLOAD/' for company in company_names]
    # ["/home/jay/work/scripts/AUP/home/company_1/UPLOAD/","/home/jay/work/scripts/AUP/home/company_2/UPLOAD/"]

    _cmp_filenames_lst = [f"{f}_complete" for f in company_names]
    # ["company_1_complete", "company_2_complete"]

    # adding all these file to file map {filename,abs_path}
    for i, name in enumerate(company_names):
        manager.add_file(_cmp_filenames_lst[i], src_upload_directory_lst[i])

    # adding AUPChannelUploader.py will need later
    manager.add_file("AUPChannelUploader.py", f"{server_home}/allegoAdmin/scripts/channels/")
    # creating files
    manager.create_files()
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
    
    # --- replaced while with for loop ---
    all_companies = ENV["all_companies"]
    for company in all_companies:
        company_name = company['name']
        company_id = company['name']

        # --- Logging per company ---
        logfile_company = f"{logfile_root}/filewatcher.log.{company_name}.{date_time}"
        setup_logging(logfile_company)

        logger.info(f"checking {company}, {datetime.now()}")

        upload_directory = source_root / company_name / "UPLOAD"
        work_directory = Path(f"{target_root}/{company_name}")

        logger.info(f"company= {company_name}")
        logger.info(f"companyID= {company_id}")
        for idx, _cmp_file in enumerate(upload_directory.glob("*_complete")):
            file_name = _cmp_file.name
            prefix = file_name[:-9]  # Removes last 9 characters

            # static in loop
            channel_id = ENV.get("channel_id")
            python_exe = ENV.get("python_exe")
            script_path = ENV.get("channels_script_path")

            users_csv = upload_directory / f"{prefix}_users.csv"
            groups_csv = upload_directory / f"{prefix}_groups.csv"
            user_group_membership_csv = upload_directory / f"{prefix}_user_group_membership.csv"
            fbt_users_csv = upload_directory / f"{prefix}_fbt_users.csv"  # sunovion Legacy implementation
            manual_users_csv = upload_directory / f"{prefix}_manual_users.csv"  # Manual File Support

            aup_failure_archive_path = target_root / "aupFailureArchive" / f"{prefix}_{company_name}"

            manager.add_file("add_update.csv", f"{work_directory}")
            manager.add_file("disable.csv", f"{work_directory}")
            manager.add_file("users.csv", f"{work_directory}")
            manager.add_file("manual_users.csv", f"{work_directory}")
            manager.add_file(f"{prefix}_groups.csv", str(upload_directory))
            manager.add_file(f"{prefix}_user_group_membership.csv", str(upload_directory))
            manager.add_file(f"{prefix}_fbt_users.csv", str(upload_directory))
            manager.add_file(f"{prefix}_manual_users.csv", str(upload_directory))
            manager.add_file(f"{prefix}_users.csv", str(upload_directory))
            manager.create_files()

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
            previous_check = Path(work_directory) /"users.csv"
            previous_manual_check = Path(work_directory) /"manual_users.csv"

            if len(sys.argv) > 2 and sys.argv[2].lower() == "legacy":
                logger.debug("Running Legacy Version with full file")
                # Legacy runs as manual; override Threshold
                threshold = 101
                previous_check = Path(work_directory) / "users.csv"
                previous_manual_check = Path(work_directory) /"manual_users.csv"
                previous_check.touch()
                previous_manual_check.touch()
            else:
                if previous_check.exists():
                    logger.debug("A previous users.csv run as been detected")
                else:
                    previous_check.touch()
                    logger.debug("Created blank Users.csv previous file for first run")

                if previous_manual_check.exists():
                    logger.debug("A previous manual_users.csv run as been detected")
                else:
                    previous_manual_check.touch()
                    logger.debug("Created blank manual_Users.csv previous file for first run")

            # Copy previous users.csv (or blank one you just touched, or blank one you forced in there), as previous.csv
            # Copy previous manual_users.csv (or blank one you just touched, or blank one you forced in there), as manual_previous.csv
            previous_file = Path(work_directory) / "previous.csv"
            previous_manual_file = Path(work_directory) / "manual_previous.csv"

            shutil.copy2(previous_check, previous_file)
            shutil.copy2(previous_manual_check, previous_manual_file)

            script_file = f"{script_path}/AUPChannelUploader.py"
            # Run command
            result = subprocess.run(
                [python_exe, script_file, str(channel_id), str(users_csv)],
                capture_output=True,
                text=True,
            )

            # Check result
            if result.returncode == 0:
                logger.debug("Script executed successfully:")
            else:
                logger.debug("Script failed:")

            # Check estimated differences first CASE is based on exit codes. Skip if threshold = 101
            location = ENV.get("location")
            if threshold < 101:
                # precent =  0 # skipping log watcher, testing purpose.
                precent = diff_checker(previous_file, users_csv, threshold, location, company_id, company_name, logger_obj=logger)
                if precent == 1 :
                    logger.debug("Diff Checker has stopped AUP...")
                    # Remove complete file and archive Users file when AUP fails

                    # 1. Remove *_complete files
                    for file in upload_directory.glob("*_complete"):
                        try:
                            file.unlink()
                        except Exception as e:
                            logger.error(f"Failed to delete {file}: {e}")

                    # 2. Move users_csv to failure archive with prefix
                    try:
                        shutil.move(str(users_csv), str(aup_failure_archive_path))
                    except Exception as e:
                        logger.error(f"Failed to move file: {e}")
                    exit(1)
                else:
                    logger.debug("Diff Checker has passed...")

            # --- End FileWatcherExpressEnhancement Step 1 ---

            # --- This is not in script but to keep in safe side, I did here ---
            backup_dir = work_directory / "backup"
            backup_dir.mkdir(parents=True ,exist_ok=True)
            logger.info("Backup dir created in server home")

            bck_user_csv = backup_dir / f"users.csv.{prefix}"
            bck_add_update = backup_dir / f"add_update.csv.{prefix}"
            bck_disable = backup_dir / f"disable.csv.{prefix}"
            bck_grp_csv = backup_dir / f"groups.csv_{prefix}"
            bck_group_membership_csv = backup_dir / f"group_membership.csv_{prefix}"
            bck_fbt_user_csv = backup_dir / f"fbt_users.csv.{prefix}"
            bck_manual_users_csv = backup_dir / f"fbt_users.csv.{prefix}"

            if users_csv.exists():
                bck_user_csv.touch()
                shutil.copy2(str(users_csv), str(bck_user_csv))
                logger.info("user csv copied to backup folder.")

                skip_header(str(bck_user_csv), f"{work_directory}/users.csv" )
                dos2unix(f"{work_directory}/users.csv")

            # --- FileWatcherExpressEnhancement Step 2 ---
            add_update_csv = work_directory / "add_update.csv"
            disable_csv = work_directory / "disable.csv"

            if add_update_csv.exists():
                shutil.copy2(add_update_csv, bck_add_update)
                logger.info("add_update csv copied to backup")
            if disable_csv.exists():
                shutil.copy2(disable_csv, bck_disable)
                logger.info("disable csv copied to backup")

            generate_add_update_csv(str(previous_file), f"{work_directory}/users.csv",str(add_update_csv))
            generate_disable_file(str(previous_file),f"{work_directory}/users.csv", str(disable_csv) )
            # --- End FileWatcherExpressEnhancement Step 2 ---

            # Older implementation of groups.csb and userGroupMemberShip.csv
            if groups_csv.exists():
                bck_grp_csv.touch()
                shutil.copy2(str(groups_csv), str(bck_grp_csv))
                skip_header(str(bck_grp_csv),str(groups_csv))

            if user_group_membership_csv.exists():
                bck_group_membership_csv.touch()
                shutil.copy2(str(user_group_membership_csv), str(bck_group_membership_csv))
                skip_header(str(bck_group_membership_csv),str(user_group_membership_csv))

            if fbt_users_csv.exists():
                bck_fbt_user_csv.touch()
                shutil.copy2(str(fbt_users_csv), str(bck_fbt_user_csv))
                skip_header(str(bck_fbt_user_csv), str(fbt_users_csv))

            if manual_users_csv.exists():
                bck_manual_users_csv.touch()
                shutil.copy2(str(manual_users_csv), str(bck_manual_users_csv))
                skip_header(str(bck_manual_users_csv), str(manual_users_csv))

            # FileWatcherExpressEnhancement Step 3 - Manual Files
            manual_update_csv = Path(work_directory) / "manual_update.csv"
            manager.add_file("manual_update.csv", f"{work_directory}")
            manager.create_files()

            if manual_update_csv.exists():
                bck_manual_users_csv.touch()
                shutil.copy2(str(manual_update_csv), str(bck_manual_users_csv))

            generate_add_update_csv(str(previous_manual_file), str(previous_manual_check), str(manual_update_csv))

            # Remove *_complete file
            complete_file_to_remove = upload_directory / company_name
            if complete_file_to_remove.exists():
                complete_file_to_remove.unlink()
                logger.info(f"[+] Removed complete file: {complete_file_to_remove}")
            else:
                logger.debug(f"[!] Complete file not found: {complete_file_to_remove}")

            #
            # now run the script to load the data into staging tables in the db
            #

            # HERE  WE NEED .SQL FILE BUT FOR TEMPORARY I USED A .PY FILE
            mysql_cmd = ENV.get("mysql_cmd")
            mysql_args = shlex.split(mysql_cmd)
            manager.add_file(f"setup_{company_name}.py", f"{allego_home}/conf/import/customer/{company_name}")
            manager.add_file("import.sh",f"{allego_home}/scripts")
            manager.create_files()

            #  I CAN NOT TEST THIS .SQL IN LOCAL.
            stage_script = Path(ENV.get("customer_stg_script")) / company_name / f"setup_{company_name}.sql"

            try:
                # make sql executable.
                if make_sql_executable(sql_path=stage_script):
                    logger.info("SQL script is ready to execute.")
                else:
                    logger.warning("Problem in making .sql executable...")
                # execute
                try:
                    # 1. Read all queries from the .sql file into a single string
                    with open(stage_script, 'r') as f:
                        sql_commands = f.read()

                    # 2. Execute the mysql command, piping the file's content to it
                    #    The `input` parameter is the key here.
                    subprocess.run(
                        mysql_args,
                        input=sql_commands,
                        text=True,  # Treat input as text
                        check=True  # Raise an error if the command fails
                    )
                    logger.info(f"✅ Successfully executed {stage_script}")

                except FileNotFoundError:
                    print(f"❌ Error: The file was not found at {stage_script}")
                except subprocess.CalledProcessError as e:
                    print(f"❌ Error during MySQL execution: {e}")
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")
                #     output = run_sql_script(stage_script, f"{work_directory}")
                # if output:
                #     logger.info("Script executed successfully...")
                # else:
                #     logger.error("execution not return output")
            except Exception as e:
                logger.error(f"Error in sql execution... {e}")

            #
            # now run the script to load from staging into production - run this one asynchronously
            #
            load_script = Path(ENV.get("allegoadmin_script_path")) / "import.sh"
            try:
                output = run_shell_script(str(load_script), f"{company_id}")
                if output:
                    logger.info("import script executed successfully...")
                else:
                    logger.error("import sh execution not return output")
            except Exception as e:
                logger.error(f"Error in import.sh execution... {e}")
        logger.info(f"checked for {company}, {datetime.now()}")

if __name__ == "__main__":
    main()