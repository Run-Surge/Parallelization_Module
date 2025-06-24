##########################################################################################################
#! User defined variables
import csv
FILE_NAME = 'pixels.csv'  # Name of the file to read data from
CSV_OUTPUT = 'edges.csv'
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

def apply_sobel_all(images_2d):
    sobel_results = []
    Gx = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
    Gy = [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]
    for image_2d in images_2d:
        result = []
        for i in range(32):
            result_row = []
            for j in range(32):
                if i == 0 or j == 0 or i == 32 - 1 or j == 32 - 1:
                    result_row.append(0)
                else:
                    gx = 0
                    gy = 0
                    for ki in range(3):
                        for kj in range(3):
                            ni = i + ki - 1
                            nj = j + kj - 1
                            px = image_2d[ni][nj]
                            gx += Gx[ki][kj] * px
                            gy += Gy[ki][kj] * px
                    magnitude = (gx ** 2 + gy ** 2) ** 0.5
                    result_row.append(round(min(magnitude, 255)))
            result.append(result_row)
        sobel_results.append(result)
    aggregation = "c:sobel_results"
    return sobel_results

def flatten_all(sobel_images):
    flat_images = []
    for image_2d in sobel_images:
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
    sobel_outputs = apply_sobel_all(reshaped_data)
    output = flatten_all(sobel_outputs)
#---------------------------------------------------------------------------------------------------------
    with open(CSV_OUTPUT, 'w', newline='') as file:
        writer = csv.writer(file)
        header = ['p' + str(i + 1) for i in range(32 * 32)]
        writer.writerow(header)
        for row in output:
            writer.writerow(row)
#---------------------------------------------------------------------------------------------------------
