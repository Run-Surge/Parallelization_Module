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
#! each function must have an aggregation variable just before the return statement

def calculate_mean(data):
    numeric_data = []
    for row in data[1:]:  # Skip header
        numeric_row = []
        for x in row:
            numeric_row.append(float(x))
        numeric_data.append(numeric_row)

    num_columns = len(numeric_data[0])
    num_rows = len(numeric_data)
    mean_values = []
    for col_idx in range(num_columns):
        total = 0
        for row_idx in range(num_rows):
            total += numeric_data[row_idx][col_idx]
        mean = total / num_rows
        mean_values.append(mean)
    aggregation = "a:mean_values"
    return mean_values    

def calculate_std(data, mean_values):
    numeric_data = []
    for row in data[1:]:  # Skip header
        numeric_row = []
        for x in row:
            numeric_row.append(float(x))
        numeric_data.append(numeric_row)

    num_columns = len(numeric_data[0])
    num_rows = len(numeric_data)
    std_values = []
    for col_idx in range(num_columns):
        variance = 0
        for row_idx in range(num_rows):
            diff = numeric_data[row_idx][col_idx] - mean_values[col_idx]
            variance += diff ** 2
        std = (variance / num_rows) ** 0.5
        std_values.append(std)
    result = []
    result.append(data[0])  # Include header
    result.append(std_values)  # Append std values
    aggregation = "a:result"
    return result
##########################################################################################################


##########################################################################################################
if __name__ == '__main__':
#---------------------------------------------------------------------------------------------------------
#! This block handles data loading please don't edit it (Note:The data is loaded into a list of name data)
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
#! Note for boosting performance if list is modified inside the function (each function call is independent) then return pass a 
#! copy of the list instead of the same list for performing different operations in parallel
    mean_values = calculate_mean(data)
    std_data = calculate_std(data, mean_values)
    output = std_data
#---------------------------------------------------------------------------------------------------------
#! Saving the output to a file please don't edit this block
#! output name should be a list named output
    with open('output.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        for row in output:
            writer.writerow(row)
#---------------------------------------------------------------------------------------------------------


##########################################################################################################
