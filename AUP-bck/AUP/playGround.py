import csv
import os
def sort_csv_by_column(prevFilePath, currentFilePath, column_name=None):
    # sorting prev file

    with open(prevFilePath, mode='r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        prevFileData = list(reader)

    if not prevFileData:
        raise ValueError("CSV file is empty")

        # Use provided column or default to the first column
    sort_key = column_name if column_name else reader.fieldnames[0] # type: ignore
    if sort_key not in reader.fieldnames: # type: ignore
        raise ValueError(f"Column '{sort_key}' not found in CSV headers")
 
    sortedPrevFile = sorted(prevFileData, key=lambda x: x[sort_key])    
    # print(sortedPrevFile)

    output_file_path = "sorted_prev.csv"
    with open(output_file_path, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames) # type: ignore
        writer.writeheader()
        writer.writerows(sortedPrevFile)
    
    print("########################################################################")
    # sorting current file
    with open(currentFilePath, mode='r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        currentFileData = list(reader)

    if not currentFileData:
        raise ValueError("CSV file is empty")
    
    # Use provided column or default to the first column
    sort_key = column_name if column_name else reader.fieldnames[0] # type: ignore
    if sort_key not in reader.fieldnames: # type: ignore
        raise ValueError(f"Column '{sort_key}' not found in CSV headers")
    
    sortedCurrentFile = sorted(currentFileData, key= lambda x : x[sort_key])
    # print(sortedCurrentFile)
    
    output_file_path = "sorted_currnt.csv"
    with open(output_file_path, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames) # type: ignore
        writer.writeheader()
        writer.writerows(sortedCurrentFile)

    print("########################################################################")

    # creating addUpdate and disable csv files.


sort_csv_by_column("../py/home/ubuntu/allegoAdmin/workdir/solarcity/previous.csv", "../py/home/ubuntu/allegoAdmin/workdir/solarcity/users.csv", "id")
# /home/jay/work/scripts/AUP/data/csv/orgData.csv


def generate_add_discard_files(current_csv, previous_csv, add_csv, discard_csv):
    def read_rows(filepath):
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = [tuple(row) for row in reader]
        return header, rows

    # Read both CSVs
    current_header, current_rows = read_rows(current_csv)
    previous_header, previous_rows = read_rows(previous_csv)

    # Optional: Check if headers match
    if current_header != previous_header:
        raise ValueError("Headers do not match between current and previous CSV files")

    # Convert to sets for comparison
    current_set = set(current_rows)
    previous_set = set(previous_rows)

    add_rows = current_set - previous_set  # new rows
    discard_rows = current_set & previous_set  # existing rows

    # Write add.csv
    with open(add_csv, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(current_header)
        writer.writerows(add_rows)

    # Write discard.csv
    with open(discard_csv, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(current_header)
        writer.writerows(discard_rows)

generate_add_discard_files("./sorted_currnt.csv","./sorted_prev.csv","./sortedFiles/add.csv","./sortedFiles/discar.csv")