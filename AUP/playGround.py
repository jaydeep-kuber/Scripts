# import csv
# import os
# def sort_csv_by_column(prevFilePath, currentFilePath, column_name=None):
#     # sorting prev file
#
#     with open(prevFilePath, mode='r', newline='', encoding='utf-8') as infile:
#         reader = csv.DictReader(infile)
#         prevFileData = list(reader)
#
#     if not prevFileData:
#         raise ValueError("CSV file is empty")
#
#         # Use provided column or default to the first column
#     sort_key = column_name if column_name else reader.fieldnames[0] # type: ignore
#     if sort_key not in reader.fieldnames: # type: ignore
#         raise ValueError(f"Column '{sort_key}' not found in CSV headers")
#
#     sortedPrevFile = sorted(prevFileData, key=lambda x: x[sort_key])
#     # print(sortedPrevFile)
#
#     output_file_path = "sorted_prev.csv"
#     with open(output_file_path, mode='w', newline='', encoding='utf-8') as outfile:
#         writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames) # type: ignore
#         writer.writeheader()
#         writer.writerows(sortedPrevFile)
#
#     print("########################################################################")
#     # sorting current file
#     with open(currentFilePath, mode='r', newline='', encoding='utf-8') as infile:
#         reader = csv.DictReader(infile)
#         currentFileData = list(reader)
#
#     if not currentFileData:
#         raise ValueError("CSV file is empty")
#
#     # Use provided column or default to the first column
#     sort_key = column_name if column_name else reader.fieldnames[0] # type: ignore
#     if sort_key not in reader.fieldnames: # type: ignore
#         raise ValueError(f"Column '{sort_key}' not found in CSV headers")
#
#     sortedCurrentFile = sorted(currentFileData, key= lambda x : x[sort_key])
#     # print(sortedCurrentFile)
#
#     output_file_path = "sorted_currnt.csv"
#     with open(output_file_path, mode='w', newline='', encoding='utf-8') as outfile:
#         writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames) # type: ignore
#         writer.writeheader()
#         writer.writerows(sortedCurrentFile)
#
#     print("########################################################################")
#
#     # creating addUpdate and disable csv files.
#
#
# sort_csv_by_column("../py/home/ubuntu/allegoAdmin/workdir/solarcity/previous.csv", "../py/home/ubuntu/allegoAdmin/workdir/solarcity/users.csv", "id")
# # /home/jay/work/scripts/AUP/data/csv/orgData.csv
#
#
# def generate_add_discard_files(current_csv, previous_csv, add_csv, discard_csv):
#     def read_rows(filepath):
#         with open(filepath, newline='', encoding='utf-8') as f:
#             reader = csv.reader(f)
#             header = next(reader)
#             rows = [tuple(row) for row in reader]
#         return header, rows
#
#     # Read both CSVs
#     current_header, current_rows = read_rows(current_csv)
#     previous_header, previous_rows = read_rows(previous_csv)
#
#     # Optional: Check if headers match
#     if current_header != previous_header:
#         raise ValueError("Headers do not match between current and previous CSV files")
#
#     # Convert to sets for comparison
#     current_set = set(current_rows)
#     previous_set = set(previous_rows)
#
#     add_rows = current_set - previous_set  # new rows
#     discard_rows = current_set & previous_set  # existing rows
#
#     # Write add.csv
#     with open(add_csv, mode='w', newline='', encoding='utf-8') as f:
#         writer = csv.writer(f)
#         writer.writerow(current_header)
#         writer.writerows(add_rows)
#
#     # Write discard.csv
#     with open(discard_csv, mode='w', newline='', encoding='utf-8') as f:
#         writer = csv.writer(f)
#         writer.writerow(current_header)
#         writer.writerows(discard_rows)
#
# generate_add_discard_files("./sorted_currnt.csv","./sorted_prev.csv","./sortedFiles/add.csv","./sortedFiles/discar.csv")

from pathlib import Path
import os

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
        for file , dir_path in self.file_map.items():
            dir_path = self.home_path / dir_path
            file_path = dir_path / file

            print(f"[DEBUG] fullpath -> {file_path}")
            dir_path.mkdir(parents=True, exist_ok=True)

            if file_path.exists():
                print(f"[*] Existing file: {file_path}")
                continue
            file_path.touch()


if __name__ == "__main__":
    manager = FileMapManager("./home/ubuntu")

    # Add mappings
    manager.add_file("log.txt", "/home/jay/work/scripts/AUP")
    manager.add_file("run.py", "/home/jay/work/scripts/AUP")
    manager.add_file("notes.md", "/home/jay/work/scripts/AUP")

    # Create files on disk
    manager.create_files()

