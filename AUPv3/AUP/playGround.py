# from pathlib import Path
# import  time
#
# class FileMapManager:
#     def __init__(self, home_path: str):
#         self.home_path = Path(home_path).expanduser().resolve()
#         self.file_map = {} # {"filename":"path of file till dir"}
#
#     def add_file(self, filename: str , absolute_path: str):
#         """
#             Add a file-to-directory mapping.
#             Validates that filename has no slashes and path is not absolute.
#         """
#
#         if '/' in filename:
#             raise ValueError("Filename must not contain slash, check your filename.")
#         if not Path(absolute_path).is_absolute():
#             raise ValueError("Expected absolute file path")
#
#         self.file_map[filename] = Path(absolute_path)
#         print(f"[+] Mapped '{filename}' → '{absolute_path}'")
#
#     def create_files(self):
#         """
#             Creates each file in the map under home_path/relative_dir.
#             Skips if the file already exists.
#         """
#         # creating Home
#         self.home_path.mkdir(parents=True, exist_ok=True) if not self.home_path.exists() else print(f"[*] Existing home path -> {self.home_path}")
#
#         for file , dir_path in self.file_map.items():
#             file_path = dir_path / file
#
#             print(f"[DEBUG] dir_path -> {dir_path}")
#             print(f"[DEBUG] fullpath -> {file_path}")
#             dir_path.mkdir(parents=True, exist_ok=True)
#
#             if file_path.exists():
#                 print(f"[*] Existing file: {file_path}")
#                 continue
#             file_path.touch()
#
#     def clean_up(self, del_files: list[str]):
#         """
#             This function clean files created bt this class.
#         """
#
#         # making path for each file
#         for key, dir_path in self.file_map.items():
#             if key in del_files:
#                 file_path = Path(dir_path) / key
#                 if file_path.exists() and file_path.is_file():
#                     try:
#                         file_path.unlink()
#                         print(f"[✘] Deleted: {file_path}")
#                     except Exception as e:
#                         print(f"[ERROR] Error deleting {file_path}: {e}")
#                 else:
#                     print(f"[!] Skipping: File does not exist or is not a file → {file_path}")
#
# if __name__ == "__main__":
#     manager = FileMapManager("./home/ubuntu")
#
#     # Add mappings
#     manager.add_file("log.txt", "/home/jay/work/scripts/AUP/home/ubuntu")
#     manager.add_file("log1.txt", "/home/jay/work/scripts/AUP/home/ubuntu")
#     manager.add_file("log2.txt", "/home/jay/work/scripts/AUP/home/ubuntu")
#
#     # Create files on disk
#     manager.create_files()
#     time.sleep(5)
#     manager.clean_up(['log.txt','log1.txt', 'log2.txt' ])
#
import logging
import  os
import json
from datetime import datetime
from logging.config import dictConfig
from operator import index
from time import sleep

from cloudinit.log.log_util import logexc


# def setup_logging(path: str, filename: str):
#     # load file
#     with open(path, 'r') as logfile:
#         log_conf = json.load(logfile)
#
#     for handler in log_conf.get("handlers", {}).values():
#         if handler.get("filename") == "__LOGFILE__":
#             print(f"changing log to : {filename}")
#             handler["filename"] = filename
#     print(f"[INFO] log file set to : {filename}")
#     log_conf["disable_existing_loggers"] = False
#     dictConfig(log_conf)

from pathlib import Path
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
        print(f"[+] Mapped '{filename}' → '{absolute_path}'")

    def create_files(self):
        """
            Creates each file in the map under home_path/relative_dir.
            Skips if the file already exists.
        """
        # creating Home
        self.home_path.mkdir(parents=True, exist_ok=True) if not self.home_path.exists() else print(f"[*] Existing home path -> {self.home_path}")

        for file , dir_path in self.file_map.items():
            file_path = dir_path / file

            print(f"[DEBUG] dir_path -> {dir_path}")
            print(f"[DEBUG] fullpath -> {file_path}")
            dir_path.mkdir(parents=True, exist_ok=True)

            if file_path.exists():
                print(f"[*] Existing file: {file_path}")
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
                        print(f"[✘] Deleted: {file_path}")
                    except Exception as e:
                        print(f"[ERROR] Error deleting {file_path}: {e}")
                else:
                    print(f"[!] Skipping: File does not exist or is not a file → {file_path}")



def main():

    # f"/home/jay/work/scripts/AUP/home/{company}/UPLOAD/{company}_complete"
    server_home = "/home/jay/work/scripts/AUP/home/ubuntu"
    manager = FileMapManager(server_home)
    env = { "all_companies" : [
        {
            "cmp_name": "solarcity",
            "cmp_id": 14
        },
        {
            "cmp_name": "fintech",
            "cmp_id": 13
        },
        {
            "cmp_name": "yagacell",
            "cmp_id": 12
        }
    ]
    }
    # list_file = [file['cmp_name'] for file in env.get("all_companies",[])]
    # print(list_file[0].get("cmp_name"))

    # all_company_names = [name["cmp_name"] for name in env.get("all_companies", [])]
    # all_company_src_paths = [f'/home/jay/work/scripts/AUP/home/{company}/UPLOAD/{company}_complete' for company in all_company_names]
    # print(all_company_src_paths)
    # _complete_files_paths = [f"/home/jay/work/scripts/AUP/home/{company}/UPLOAD/{company}_complete" for company in ENV.get("all_companies",{}).values()]

    # all_company_names = [name["cmp_name"] for name in env.get("all_companies", [])]
    # src_cmp_upload_dir = [f'/home/jay/work/scripts/AUP/home/{company}/UPLOAD/' for company in all_company_names]
    # _cmp_filenames_lst = [f"{f}_complete" for f in all_company_names]
    # for i in range(len(all_company_names)):
    #     manager.add_file(_cmp_filenames_lst[i], src_cmp_upload_dir[i])
    #
    # manager.create_files()
    # sleep(5)
    # manager.clean_up(_cmp_filenames_lst)
    i = 0
    while i < 5:
        print(i)
    i +=1
main()