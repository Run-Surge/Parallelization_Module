import pandas as pd
import numpy as np

FILE_NAME = 'test.csv'

df = pd.read_csv(FILE_NAME)
threshold = 20
filtered = [df[col][df[col] > threshold].tolist() for col in df.columns]
mean_values = [np.mean(col) if len(col) > 0 else 0 for col in filtered]
pd.DataFrame([mean_values]).to_csv('original.csv', index=False, header=False)