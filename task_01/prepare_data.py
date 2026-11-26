import pandas as pd
from pathlib import Path

SRC = Path(r'H:\Repos\elevvo-internship-data-analytics\untitled-project\datasets\superstore.csv')
OUT = Path(r'H:\Repos\elevvo-internship-data-analytics\untitled-project\task_01\data')
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(SRC, encoding='latin1')

df['Order Date'] = pd.to_datetime(df['Order Date'], format='mixed', dayfirst=False)
df['Ship Date'] = pd.to_datetime(df['Ship Date'], format='mixed', dayfirst=False)
df.drop_duplicates(inplace=True)
df['Sales'] = df['Sales'].round(2)
df['Profit'] = df['Profit'].round(2)
df['Postal Code'] = df['Postal Code'].astype('string').str.zfill(5)

df['Order Year'] = df['Order Date'].dt.year
df['Order Month'] = df['Order Date'].dt.month
df['Month Name'] = df['Order Date'].dt.strftime('%b')
df['YearMonth'] = df['Order Date'].dt.strftime('%Y-%m')
df['Quarter'] = df['Order Date'].dt.quarter.map({1:'Q1',2:'Q2',3:'Q3',4:'Q4'})
df['Ship Days'] = (df['Ship Date'] - df['Order Date']).dt.days
df['Profit Margin'] = (df['Profit'] / df['Sales']).round(4)

dest = OUT / 'superstore_clean.csv'
df.to_csv(dest, index=False, date_format='%Y-%m-%d')
print('rows:', len(df))
print('cols:', list(df.columns))
print('range:', df['Order Date'].min().date(), '->', df['Order Date'].max().date())
print('totals: revenue=%.2f units=%d profit=%.2f' % (df['Sales'].sum(), df['Quantity'].sum(), df['Profit'].sum()))
print(dest)
