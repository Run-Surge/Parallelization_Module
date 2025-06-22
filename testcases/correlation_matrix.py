##########################################################################################################
#! User defined variables
import csv
FILE_NAME = 'test.csv'  # Name of the file to read data from

##########################################################################################################







##########################################################################################################
#! User Code is written below this line (Note: code is written in the form of fucntions and entry point is a function named 'main')
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

def compute_column_means(numeric_data):
    num_columns = len(numeric_data[0])
    num_rows = len(numeric_data)
    means = []
    for col_idx in range(num_columns):
        total = 0
        for row_idx in range(num_rows):
            total += numeric_data[row_idx][col_idx]
        mean = total / num_rows
        means.append(mean)
    aggregation = "a:means"
    return means

def compute_correlation_matrix(numeric_data, means):
    num_columns = len(numeric_data[0])
    num_rows = len(numeric_data)
    matrix = []
    for i in range(num_columns):
        row = []
        for j in range(num_columns):
            num = 0
            denom1 = 0
            denom2 = 0
            for k in range(num_rows):
                xi = numeric_data[k][i] - means[i]
                xj = numeric_data[k][j] - means[j]
                num += xi * xj
                denom1 += xi * xi
                denom2 += xj * xj
            if denom1 == 0 or denom2 == 0:
                corr = 0
            else:
                corr = num / ((denom1 ** 0.5) * (denom2 ** 0.5))
            row.append(corr)
        matrix.append(row)
    aggregation = "c:matrix"
    return matrix

##########################################################################################################


##########################################################################################################
if __name__ == '__main__':
    def infer_type(value):
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value.strip()
#---------------------------------------------------------------------------------------------------------
#! This block handles data loading please don't edit it (Note:The data is loaded into a list of name data)
    try:
        with open(FILE_NAME, 'r') as file:
            lines = file.readlines()
            data = [[infer_type(cell) for cell in line.strip().split(',')] for line in lines]
    except FileNotFoundError:
        print("File not found. Please ensure 'test.csv' exists in the current directory.")
#---------------------------------------------------------------------------------------------------------

#! User main function is defined here
#! Note for boosting performance if list is modified inside the function (each function call is independent) then return pass a 
#! copy of the list instead of the same list for performing different operations in parallel
    numeric_data = preprocess_data(data)
    means = compute_column_means(numeric_data)
    output = compute_correlation_matrix(numeric_data, means)

#---------------------------------------------------------------------------------------------------------
#! Saving the output to a file please don't edit this block
#! output name should be a list named output
    with open('output.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        for row in output:
            writer.writerow(row)
#---------------------------------------------------------------------------------------------------------


##########################################################################################################
