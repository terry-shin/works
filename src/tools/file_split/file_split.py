import csv
import sys
import gzip

if len(sys.argv) > 1:
    file_name = sys.argv[1]
else:
    print("invalid parameter")
    print("parameter input is required")
    print("please input'file_split.py [file_name]'")
    sys.exit()


input_file = f"input/{file_name}"
header = ""
target_date = ""
output_rows = []

with open(input_file, 'r') as in_f:
    reader = csv.reader(in_f)
    for index, line in enumerate(reader):
        if index == 0:
            header = line
        else:
            if target_date == '':
                target_date = line[2]
                print(f'現在の処理日付:{target_date}')
                output_rows.append(header)
            elif target_date == line[2]:
                output_rows.append(line)
            else:
                with gzip.open(f'output/{target_date}_{file_name}.gz', 'wt') as out_f:
                    out_writer = csv.writer(out_f)
                    out_writer.writerows(output_rows)
                target_date = line[2]
                print(f'現在の処理日付:{target_date}')
                output_rows = []
                output_rows.append(header)
    # 最終日付処理
    with gzip.open(f'output/{target_date}_{file_name}.gz', 'wt') as out_f:
        out_writer = csv.writer(out_f)
        out_writer.writerows(output_rows)
    target_date = line[2]


