csvData=["apple","banana","avacado",7,"graps","cherry" "lichi",1,4,5]

import csv

def sorting(data, colName):
    rows = []
    with open(data, 'r', newline='') as f:
        reader = csv.reader(f)
        headers = next(f)

        for r in reader:
            rows.append(r)

        rows.sort(key= lambda x : int(x[colName]))
    print(rows)


dataFile = "../data/csv/oldFile.csv"
sorting(dataFile, 0)