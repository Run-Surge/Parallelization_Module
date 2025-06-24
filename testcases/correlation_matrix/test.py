import pandas as pd
import numpy as np

FILE_NAME = 'test.csv'

if __name__ == '__main__':
    # Read CSV and convert everything to float
    df = pd.read_csv(FILE_NAME)
    df = df.apply(pd.to_numeric, errors='coerce')

    # Drop rows with any NaNs
    df = df.dropna(axis=0, how='any')

    # Convert to NumPy array
    data = df.values
    means = np.mean(data, axis=0)
    num_columns = data.shape[1]
    num_rows = data.shape[0]

    # Initialize empty correlation matrix
    corr_matrix = np.zeros((num_columns, num_columns))

    # Manually compute correlation (with 0 if any std is 0)
    for i in range(num_columns):
        for j in range(num_columns):
            xi = data[:, i] - means[i]
            xj = data[:, j] - means[j]
            denom = np.sqrt(np.sum(xi ** 2)) * np.sqrt(np.sum(xj ** 2))
            if denom == 0:
                corr = 0
            else:
                corr = np.sum(xi * xj) / denom
            corr_matrix[i, j] = corr

    # Save the result to CSV
    np.savetxt("original.csv", corr_matrix, delimiter=",")
