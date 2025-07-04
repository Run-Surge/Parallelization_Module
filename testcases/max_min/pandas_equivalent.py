import pandas as pd
import numpy as np

FILE_NAME = 'test.csv'

df = pd.read_csv(FILE_NAME)
threshold = 20
filtered = [df[col][df[col] > threshold].tolist() for col in df.columns]
mean_values = [np.mean(col) if len(col) > 0 else 0 for col in filtered]
min_values = df.min().tolist()
max_values = df.max().tolist()
with open('original.csv', 'w', newline='') as f:
    f.write('min\n')
    f.write(','.join(map(str, min_values)) + '\n')
    f.write('max\n')
    f.write(','.join(map(str, max_values)) + '\n')