import csv
import random

def infer_column_type(file_path, column_name):
    with open(file_path, newline='') as csvfile:
        reader = list(csv.DictReader(csvfile))

        if column_name not in reader[0].keys():
            print("Columnn is not Exist")
            return

    if len(reader) < 10:
        sample_rows = reader  # use all rows if < 10
    else:
        sample_rows = random.sample(reader, 10)

    type_counts = {"int": 0, "float": 0, "string": 0}
    missing_count = 0

    for row in sample_rows:
        value = row.get(column_name, "").strip()

        if value == "" or value.lower() in ("na", "null", "none"):
            missing_count += 1
            continue

        try:
            int(value)
            type_counts["int"] += 1
        except ValueError:
            try:
                float(value)
                type_counts["float"] += 1
            except ValueError:
                type_counts["string"] += 1

    # Choose the most frequent type
    if all(count == 0 for count in type_counts.values()):
        final_type = "unknown"
    else:
        final_type = max(type_counts, key=type_counts.get) # type: ignore

    return {
        "column": column_name,
        "sample_size": len(sample_rows),
        "inferred_type": final_type,
        "missing_values": missing_count,
        "type_breakdown": type_counts
    }


result = infer_column_type("../data/csv/1000row.csv", "Age")
print(result)
