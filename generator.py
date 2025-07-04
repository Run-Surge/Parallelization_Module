import os
import csv
import numpy as np

def generate_sales_csv_numpy(file_name, rows=10000000, columns=20, batch_size=1_000_000):
    file_path = file_name

    with open(file_path, mode='w', newline='', buffering=1024*1024) as f:
        writer = csv.writer(f)
        column_names = [f"Product_{i+1}" for i in range(columns)]
        writer.writerow(column_names)

        for i in range(0, rows, batch_size):
            current_batch = min(batch_size, rows - i)
            data = np.random.randint(1000, 10000, size=(current_batch, columns))
            writer.writerows(data.tolist())

    print(f"[INFO] Generated CSV file '{file_name}' with {rows} rows and {columns} columns.")
generate_sales_csv_numpy('sales_data2.csv')