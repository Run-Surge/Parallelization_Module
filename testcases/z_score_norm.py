##########################################################################################################
#! User defined variables
import csv
FILE_NAME = 'test.csv'  # Name of the file to read data from

##########################################################################################################







##########################################################################################################
#! User Code is written below this line (Note: code is written in the form of functions and entry point is a function named 'main')
#! all functions must have a return statement
#! the returned value is not assumed to be by reference, but a copy of it
#! no nested user defined functions are allowed
#! functions return value must be 1 value and a variable or a slice of it not an operation (ex: return x / return x[0] not return x + 1)
#! available aggregates are c --> concatenate, a --> average, s --> sum, m --> max, n --> min, l --> length, i --> multiply, empty string for means don't parallelize
#! format aggregation = "type:list"

def preprocess_data(data):
    numeric_data = []
    for row in data[1:]:  # Skip header
        numeric_row = []
        for x in row:
            # convert to float
            numeric_row.append(float(x))
        numeric_data.append(numeric_row)
    aggregation = "c:numeric_data"
    return numeric_data

def compute_column_means(numeric_data):
    num_columns = len(numeric_data[0])
    num_rows = len(numeric_data)
    means = []
    for col_idx in range(num_columns):
        total = 0.0
        for row_idx in range(num_rows):
            total += numeric_data[row_idx][col_idx]
        mean = total / num_rows
        means.append(mean)
    aggregation = "a:means"
    return means

def compute_column_stds(numeric_data, means):
    num_columns = len(numeric_data[0])
    num_rows = len(numeric_data)
    stds = []
    for col_idx in range(num_columns):
        var_sum = 0.0
        mean_i = means[col_idx]
        for row_idx in range(num_rows):
            diff = numeric_data[row_idx][col_idx] - mean_i
            var_sum += diff * diff
        # population variance: divide by num_rows
        std = (var_sum / num_rows) ** 0.5
        stds.append(std)
    aggregation = "a:stds"
    return stds

def normalize_data(numeric_data, means, stds):
    num_columns = len(numeric_data[0])
    num_rows = len(numeric_data)
    normalized_data = []
    for row_idx in range(num_rows):
        norm_row = []
        for col_idx in range(num_columns):
            val = numeric_data[row_idx][col_idx]
            std_i = stds[col_idx]
            if std_i == 0:
                norm_val = 0.0
            else:
                norm_val = (val - means[col_idx]) / std_i
            norm_row.append(norm_val)
        normalized_data.append(norm_row)
    aggregation = "c:normalized_data"
    return normalized_data

##########################################################################################################


##########################################################################################################
#---------------------------------------------------------------------------------------------------------
#! This block handles data loading please don't edit it (Note:The data is loaded into a list of name data)
if __name__ == '__main__':
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
        print("File not found. Please ensure 'test.csv' exists in the current directory.")
#---------------------------------------------------------------------------------------------------------

#! User main function is defined here
#! Note: each function call is independent; if modifying lists in-place, return a copy to avoid conflicts in parallel use
    numeric_data = preprocess_data(data)
    means = compute_column_means(numeric_data)
    stds = compute_column_stds(numeric_data, means)
    output = normalize_data(numeric_data, means, stds)

#---------------------------------------------------------------------------------------------------------
#! Saving the output to a file please don't edit this block
#! output name should be a list named output
    with open('output.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        for row in output:
            writer.writerow(row)
#---------------------------------------------------------------------------------------------------------
