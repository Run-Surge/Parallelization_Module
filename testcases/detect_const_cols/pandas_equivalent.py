import pandas as pd

FILE_NAME = 'test.csv'

def detect_constant_columns_pandas(df):
    is_constant = [1 if df[col].nunique(dropna=False) == 1 else 0 for col in df.columns]
    result = [list(df.columns), is_constant]
    return result

if __name__ == '__main__':
    df = pd.read_csv(FILE_NAME)
    output = detect_constant_columns_pandas(df)
    with open('original.csv', 'w', newline='') as f:
        for row in output:
            f.write(','.join(map(str, row)) + '\n')
