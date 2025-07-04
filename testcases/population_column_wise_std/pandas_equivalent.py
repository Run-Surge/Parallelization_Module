import pandas as pd

# Read the CSV file
df = pd.read_csv('test.csv')

# Compute column-wise standard deviation
col_std = df.std(numeric_only=True,ddof=0)

# Save the std as a single-row DataFrame to original.csv
col_std.to_frame().T.to_csv('original.csv', index=False)
