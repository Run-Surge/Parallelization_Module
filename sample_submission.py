##########################################################################################################
#! User defined variables

FILE_NAME = 'test.csv'  # Name of the file to read data from



##########################################################################################################




##########################################################################################################
#! This block handles data loading please don't edit it (Note:The data is loaded into a list of name data)
try:
    with open(FILE_NAME, 'r') as file:
        lines = file.readlines()
        data = [line.strip().split(',') for line in lines]
except FileNotFoundError:
    print("File not found. Please ensure 'test.csv' exists in the current directory.")
##########################################################################################################



##########################################################################################################
#! User Code is written below this line (Note: code is written in the form of fucntions and entry point is a function named 'main')
def add1(data):
    header = data[0]
    rows = data[1:]

    new_data = [header]
    for row in rows:
        new_row = []
        for value in row:
            try:
                new_row.append(str(float(value) + 1))
            except ValueError:
                new_row.append(value)
        new_data.append(new_row)
##########################################################################################################
#! User main function is defined here
def main():
    add1(data)
##########################################################################################################









##########################################################################################################
#! Please don't edit this block

if __name__ == '__main__':
    main()



##########################################################################################################






##########################################################################################################
#! Saving the output to a file please don't edit this block

with open('output.csv', 'w') as file:
    for row in data:
        file.write(','.join(row) + '\n')
##########################################################################################################