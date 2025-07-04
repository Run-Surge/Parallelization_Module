##########################################################################################################
#! User defined variables
import csv
FILE_NAME = 'pixels.csv'  # Name of the file to read data from
CSV_OUTPUT = 'filtered.csv'
##########################################################################################################

##########################################################################################################
#! User Code is written below this line
#! all functions must have a return statement
#! the returned value is not assumed to be by reference, but a copy of it
#! no nested user defined functions are allowed
#! functions return value must be 1 value and a variable or a slice of it not an operation (ex: return x / return x[0] not return x + 1)
#! available aggregates are c --> concatenate, a --> average, s --> sum, m --> max, n --> min, l --> length, i --> multiply, empty string for means don't parallelize
#! format aggregation = "type:list"

def preprocess_data(data):
    numeric_data = []
    for row in data[1:]:
        numeric_row = []
        for x in row:
            numeric_row.append(float(x))
        numeric_data.append(numeric_row)
    aggregation = "c:numeric_data"
    return numeric_data

def reshape_rows(numeric_data):
    reshaped_data = []
    for row in numeric_data:
        if len(row) != 32 * 32:
            continue
        image_2d = []
        for i in range(32):
            image_row = []
            for j in range(32):
                index = i * 32 + j
                image_row.append(row[index])
            image_2d.append(image_row)
        reshaped_data.append(image_2d)
    aggregation = "c:reshaped_data"
    return reshaped_data

def apply_mean_filter_all(images_2d):
    filtered_results = []
    for image_2d in images_2d:
        result = []
        for i in range(32):
            result_row = []
            for j in range(32):
                if i == 0 or j == 0 or i == 31 or j == 31:
                    result_row.append(image_2d[i][j])
                else:
                    total = 0.0
                    for ki in range(-1, 2):
                        for kj in range(-1, 2):
                            ni = i + ki
                            nj = j + kj
                            total += image_2d[ni][nj]
                    avg = total / 9.0
                    result_row.append(round(avg))
            result.append(result_row)
        filtered_results.append(result)
    aggregation = "c:filtered_results"
    return filtered_results

def flatten_all(filtered_images):
    flat_images = []
    for image_2d in filtered_images:
        flat = []
        for row in image_2d:
            for val in row:
                flat.append(val)
        flat_images.append(flat)
    aggregation = "c:flat_images"
    return flat_images
##########################################################################################################

##########################################################################################################
if __name__ == '__main__':
#---------------------------------------------------------------------------------------------------------
    def infer_type(value):
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value.strip()
    try:
        with open(FILE_NAME, 'r') as file:
            lines = file.readlines()
            data = [[infer_type(cell) for cell in line.strip().split(',')] for line in lines]
    except FileNotFoundError:
        print("File not found. Please ensure 'pixels.csv' exists in the current directory.")
#---------------------------------------------------------------------------------------------------------
    numeric_data = preprocess_data(data)
    reshaped_data = reshape_rows(numeric_data)
    filtered_outputs = apply_mean_filter_all(reshaped_data)
    output = flatten_all(filtered_outputs)
#---------------------------------------------------------------------------------------------------------
    with open(CSV_OUTPUT, 'w', newline='') as file:
        writer = csv.writer(file)
        header = ['p' + str(i + 1) for i in range(32 * 32)]
        writer.writerow(header)
        for row in output:
            writer.writerow(row)
#---------------------------------------------------------------------------------------------------------
