import pandas as pd

# Read the CSV file
df = pd.read_csv('test.csv')

# Compute column-wise sum
col_sum = df.sum(numeric_only=True)

# Save the sum as a single-row DataFrame to original.csv
col_sum.to_frame().T.to_csv('original.csv', index=False)

