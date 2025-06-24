import pandas as pd
import numpy as np

FILE_NAME = 'test.csv'

if __name__ == '__main__':
    # Load CSV
    df = pd.read_csv(FILE_NAME)

    # Convert all data to float (non-numeric to NaN)
    df = df.apply(pd.to_numeric, errors='coerce')

    # Drop rows with any NaN (optional, to mimic your assumption of clean input)
    df = df.dropna()

    # Compute column-wise population mean and std (ddof=0)
    means = df.mean()
    stds = df.std(ddof=0)

    # Replace zero stds with 1 to avoid division by zero during normalization
    safe_stds = stds.replace(0, np.nan)  # temporarily use NaN to avoid division
    normalized_df = (df - means) / safe_stds

    # Replace resulting NaNs (from 0 std) with 0.0 (like your code does)
    normalized_df = normalized_df.fillna(0.0)

    # Save to CSV without index or header (matches your manual output)
    normalized_df.to_csv('original.csv', index=False, header=False)
