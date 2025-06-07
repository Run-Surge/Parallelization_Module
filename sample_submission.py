##########################################################################################################
#! User defined variables

FILE_NAME = 'test.csv'  # Name of the file to read data from

##########################################################################################################







##########################################################################################################
#! User Code is written below this line (Note: code is written in the form of fucntions and entry point is a function named 'main')
#! all functions must have a return statement
#! the returned value is not assumed to be by reference, but a copy of it
#! no nested user defined functions are allowed
def add1(data):
    header = data[0]
    rows = data[1:]
    new_data = [header]
    new_data.extend(rows)  # Copy existing rows to new_data
    new_data.append(['New Row', 'Value1', 'Value2'])  # Add a new row with custom values
    return new_data[0]
def hello(z):
    z = z + 1
    return z
def hello2():
    return 4 + 3
def hello3(x,y):
    x = x+1
    return x + y
def calc(x,y,z,a,b,c,d):
    return [['Output', str(x), str(y), str(z), str(a), str(b), str(c), str(d)]]  # Example output format
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
    z = add1(data)
    x = hello2()
    y = x.copy()
    z = hello(z)
    a = hello(z)
    b = hello3(x,y)
    c = hello(z)
    d = hello3(x)
    output = calc(x,y,z,a,b,c,d)
    
    
#---------------------------------------------------------------------------------------------------------
#! Saving the output to a file please don't edit this block
#! output name should be a list named output
    with open('output.csv', 'w') as file:
        for row in output:
            file.write(','.join(row) + '\n')
#---------------------------------------------------------------------------------------------------------




##########################################################################################################






