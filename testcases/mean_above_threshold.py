##########################################################################################################
#! User defined variables

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

def filter_above_threshold(data):
    threshold = 50
    numeric_data = []
    for row in data[1:]:  # Skip header
        numeric_row = []
        for x in row:
            numeric_row.append(x)
        numeric_data.append(numeric_row)

    num_columns = len(numeric_data[0])
    num_rows = len(numeric_data)
    filtered = []
    for col_idx in range(num_columns):
        col_filtered = []
        for row_idx in range(num_rows):
            value = numeric_data[row_idx][col_idx]
            if value > threshold:
                col_filtered.append(value)
        filtered.append(col_filtered)
    aggregation = "c:filtered"
    return filtered

def mean_filtered_columns(filtered):
    mean_values = []
    for column in filtered:
        x = len(column)
        if x > 0:
            total = 0
            for x in column:
                total += x
            mean = total / x
        else:
            mean = 0
        mean_values.append(mean)
    aggregation = "a:mean_values"
    return mean_values

##########################################################################################################


##########################################################################################################
if __name__ == '__main__':
#---------------------------------------------------------------------------------------------------------
#! This block handles data loading please don't edit it (Note:The data is loaded into a list of name data)
    try:
        with open(FILE_NAME, 'r') as file:
            lines = file.readlines()
            data = [line.strip().split(',') for line in lines]
    except FileNotFoundError:
        print("File not found. Please ensure 'test.csv' exists in the current directory.")
#---------------------------------------------------------------------------------------------------------

#! User main function is defined here
#! Note for boosting performance if list is modified inside the function (each function call is independent) then return pass a 
#! copy of the list instead of the same list for performing different operations in parallel
    filtered = filter_above_threshold(data)
    mean_values = mean_filtered_columns(filtered)
    output = [mean_values]

#---------------------------------------------------------------------------------------------------------
#! Saving the output to a file please don't edit this block
#! output name should be a list named output
    with open('output.csv', 'w') as file:
        for row in output:
            file.write(','.join(row) + '\n')
#---------------------------------------------------------------------------------------------------------


##########################################################################################################
