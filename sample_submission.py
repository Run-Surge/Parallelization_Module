##########################################################################################################
#! User defined variables

FILE_NAME = 'test.csv'  # Name of the file to read data from

##########################################################################################################







##########################################################################################################
#! User Code is written below this line (Note: code is written in the form of fucntions and entry point is a function named 'main')
def add1(data):
    header = data[0]
    rows = data[1:]
    new_data = [header]
    new_data.extend(rows)  # Copy existing rows to new_data
    new_data.append(['New Row', 'Value1', 'Value2'])  # Add a new row with custom values
def hello(z):
    z = z + 1
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
    add1(data)
    hello(5)
    
    
#---------------------------------------------------------------------------------------------------------
#! Saving the output to a file please don't edit this block
    with open('output.csv', 'w') as file:
        for row in data:
            file.write(','.join(row) + '\n')
#---------------------------------------------------------------------------------------------------------




##########################################################################################################






