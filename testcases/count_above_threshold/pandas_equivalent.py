import pandas as pd

# Read the CSV file
df = pd.read_csv('test.csv')

# Compute column-wise sum
col_sum = df.sum(numeric_only=True)

# Save the sum as a single-row DataFrame to original.csv
col_sum.to_frame().T.to_csv('original.csv', index=False)

# Count values above threshold (20) for each column and save to output.csv
threshold = 20
count_above = (df > threshold).sum()
result_df = pd.DataFrame([count_above.values], columns=df.columns)
# Write header and counts as two rows
result_df_with_header = pd.concat([pd.DataFrame([df.columns], columns=df.columns), result_df], ignore_index=True)
result_df_with_header.to_csv('original.csv', index=False, header=False)
