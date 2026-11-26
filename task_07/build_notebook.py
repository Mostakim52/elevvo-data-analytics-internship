"""Build Task 7 notebook: time-series breakdown of Walmart retail sales."""
import pathlib

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

OUT = pathlib.Path(r"H:\Repos\elevvo-internship-data-analytics\untitled-project\task_07\Walmart_Time_Series.ipynb")
cells = []

cells.append(new_markdown_cell("""# Task 7 — Time Series Breakdown of Retail Sales

**Elevvo Data Analytics Internship — Task 7 (Level 3)**

**Dataset:** Walmart Sales Forecasting (Kaggle) — `train.csv` (421,570 weekly store-department records, Feb 2010 – Oct 2012), `stores.csv` (store type and size), `features.csv` (temperature, fuel price, CPI, unemployment, markdowns).

**What this notebook does**

1. Combine weekly sales with store and economic attributes.
2. Build the monthly revenue series and read the trend with a 12-month moving average.
3. Quantify seasonality (month-of-year index, year × month heatmap) and the holiday effect.
4. Break revenue down by *product* (department) and by store format, which is the closest thing this dataset offers to a region.
5. Bonus: forecast with exponential smoothing and benchmark it against a rolling-mean baseline.

**Note on "region":** the Walmart dataset contains no state or city field — only `Store`, `Type` (A/B/C) and `Size`. Store format is therefore used as the regional proxy and is labelled as such throughout.
"""))

cells.append(new_markdown_cell("""## 1. Load and combine the three files"""))
cells.append(new_code_cell("""import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings('ignore')
sns.set_theme(style='whitegrid', palette='deep')
plt.rcParams['figure.dpi'] = 110
plt.rcParams['axes.titlesize'] = 11

DATA = Path('../datasets')
OUT = Path('.')

train = pd.read_csv(DATA / 'walmart_train.csv', parse_dates=['Date'])
stores = pd.read_csv(DATA / 'walmart_stores.csv', lineterminator='\\r')
feat = pd.read_csv(DATA / 'walmart_features.csv', parse_dates=['Date'])

print('train   ', train.shape)
print('stores  ', stores.shape)
print('features', feat.shape)
print('date range:', train.Date.min().date(), '->', train.Date.max().date())
print('stores:', train.Store.nunique(), '| departments:', train.Dept.nunique())
"""))

cells.append(new_code_cell("""df = (train
      .merge(stores, on='Store', how='left')
      .merge(feat[['Store', 'Date', 'Temperature', 'Fuel_Price', 'CPI', 'Unemployment']],
             on=['Store', 'Date'], how='left'))

df['Year'] = df.Date.dt.year
df['Month'] = df.Date.dt.month
df['SizeBand'] = pd.cut(df.Size, [0, 50_000, 100_000, 150_000, 250_000],
                        labels=['<50k sqft', '50-100k', '100-150k', '150k+'])

print('joined:', df.shape, '| negative or zero sales rows:', (df.Weekly_Sales <= 0).sum())
print('missing CPI:', df.CPI.isna().sum(), '| missing store type:', df.Type.isna().sum())
df.head()
"""))

cells.append(new_markdown_cell("""## 2. Monthly revenue trend

Weekly figures are summed into calendar months (each week is assigned to the month of its Friday end-date). The 12-month moving average removes the seasonal saw-tooth and exposes the underlying direction.
"""))
cells.append(new_code_cell("""monthly = (df.groupby(pd.Grouper(key='Date', freq='MS'))['Weekly_Sales']
             .sum().to_frame('Sales'))
monthly['Rolling12'] = monthly.Sales.rolling(12, min_periods=6).mean()
monthly['MoM_%'] = monthly.Sales.pct_change() * 100
monthly['YoY_%'] = monthly.Sales.pct_change(12) * 100

fig, ax = plt.subplots(figsize=(11, 4.2))
ax.plot(monthly.index, monthly.Sales / 1e6, marker='o', ms=3, lw=1.4, label='Monthly sales')
ax.plot(monthly.index, monthly.Rolling12 / 1e6, lw=2.6, color='crimson', label='12-month moving average')
ax.set_title('Walmart US weekly sales, aggregated to months')
ax.set_ylabel('Sales ($ millions)')
ax.legend()
plt.tight_layout()
plt.savefig(OUT / 'fig_trend.png', bbox_inches='tight')
plt.show()

print(f"total sales      ${df.Weekly_Sales.sum()/1e9:.2f}B")
print(f"average month    ${monthly.Sales.mean()/1e6:.1f}M")
print(f"best month       {monthly.Sales.idxmax():%b %Y} at ${monthly.Sales.max()/1e6:.1f}M")
print(f"weakest month    {monthly.Sales.idxmin():%b %Y} at ${monthly.Sales.min()/1e6:.1f}M")
print(f"last 12m vs prior 12m: {monthly.Sales[-12:].sum()/monthly.Sales[-24:-12].sum()-1:+.1%}")
"""))

cells.append(new_markdown_cell("""## 3. Year-over-year view

Overlaying whole years on a shared month axis makes the year-on-year direction and the shape of the seasonal curve comparable at a glance.
"""))
cells.append(new_code_cell("""fig, axes = plt.subplots(1, 2, figsize=(12, 4))

years = [2010, 2011, 2012]
palette = {2010: '#8ab4f8', 2011: '#f6a623', 2012: '#1f3864'}
for y in years:
    s = monthly[monthly.index.year == y]
    axes[0].plot(s.index.month, s.Sales / 1e6, marker='o', ms=4, label=str(y), color=palette[y])
axes[0].set_xticks(range(1, 13))
axes[0].set_xlabel('Month')
axes[0].set_ylabel('Sales ($ millions)')
axes[0].set_title('Monthly sales by year')
axes[0].legend(title='Year')

yearly = df.groupby('Year').Weekly_Sales.sum() / 1e9
axes[1].bar(yearly.index.astype(str), yearly.values, color=['#8ab4f8', '#f6a623', '#1f3864'])
axes[1].set_title('Total sales by year (2012 is partial)')
axes[1].set_ylabel('Sales ($ billions)')
for i, v in enumerate(yearly.values):
    axes[1].text(i, v + 0.15, f'${v:.2f}B', ha='center', fontsize=9)

plt.tight_layout()
plt.savefig(OUT / 'fig_yoy.png', bbox_inches='tight')
plt.show()

print('2012 covers Feb–Oct only, so its total is not comparable to full years.')
print(df[df.Year == 2012].Date.max().date())
"""))

cells.append(new_markdown_cell("""## 4. Seasonality

The seasonality index is each calendar month's average sales divided by the average month, so 1.00 is a "normal" month and 1.20 means 20% above average.
"""))
cells.append(new_code_cell("""seasonal = (monthly.assign(Month=monthly.index.month)
                     .groupby('Month').Sales.mean())
index = seasonal / seasonal.mean()

fig, axes = plt.subplots(1, 2, figsize=(12, 4))

cols = ['#c0392b' if v == index.max() else '#2c7fb8' for v in index.values]
axes[0].bar(index.index, index.values, color=cols)
axes[0].axhline(1, color='grey', ls='--', lw=1)
axes[0].set_xticks(range(1, 13))
axes[0].set_title('Seasonality index by calendar month')
axes[0].set_xlabel('Month')
axes[0].set_ylabel('Index (1.00 = average month)')
for m, v in index.items():
    axes[0].text(m, v + 0.01, f'{v:.2f}', ha='center', fontsize=7)

heat = monthly.assign(Year=monthly.index.year, Month=monthly.index.month).pivot_table(
    index='Year', columns='Month', values='Sales') / 1e6
sns.heatmap(heat, annot=True, fmt='.0f', cmap='YlGnBu', cbar_kws={'label': '$m'},
            ax=axes[1], linewidths=.5)
axes[1].set_title('Monthly sales heatmap ($ millions)')
axes[1].set_xlabel('Month')
axes[1].set_ylabel('Year')

plt.tight_layout()
plt.savefig(OUT / 'fig_seasonality.png', bbox_inches='tight')
plt.show()

print('strongest months:', ', '.join(f'{m}' for m in index.nlargest(3).index))
print(index.sort_values(ascending=False).head(3).round(3).to_string())
"""))

cells.append(new_markdown_cell("""## 5. Holiday effect

`IsHoliday` flags four weeks: Super Bowl, Labour Day, Thanksgiving and Christmas. Comparing holiday weeks with ordinary weeks isolates the promotional spike.
"""))
cells.append(new_code_cell("""weekly = df.groupby(['Date', 'IsHoliday']).Weekly_Sales.sum().reset_index()
hol = weekly.groupby('IsHoliday').Weekly_Sales.mean()
lift = hol[True] / hol[False] - 1
print(f"average holiday week: ${hol[True]/1e6:.1f}M")
print(f"average ordinary week: ${hol[False]/1e6:.1f}M")
print(f"holiday lift: {lift:+.1%}")

# the four flagged weeks per year, in date order
flagged = weekly[weekly.IsHoliday].sort_values('Date')
flagged['Year'] = flagged.Date.dt.year
fig, ax = plt.subplots(figsize=(9, 3.4))
for y in [2010, 2011]:
    s = flagged[flagged.Year == y]
    ax.plot(range(len(s)), s.Weekly_Sales / 1e6, marker='o', label=str(y))
ax.set_xticks(range(4))
ax.set_xticklabels(['Super Bowl (Feb)', 'Labour Day (Sep)', 'Thanksgiving (Nov)', 'Christmas (Dec)'])
ax.set_ylabel('Sales in holiday week ($ millions)')
ax.set_title('Sales in the four flagged holiday weeks')
ax.legend(title='Year')
plt.tight_layout()
plt.savefig(OUT / 'fig_holidays.png', bbox_inches='tight')
plt.show()

print(flagged[flagged.Year == 2011][['Date', 'Weekly_Sales']].to_string(index=False))
"""))

cells.append(new_markdown_cell("""## 6. Breakdown by product — department over time

`Dept` is the product dimension. The ten largest departments are tracked month by month, and each one's change from 2010 to comparable months in 2012 shows which parts of the assortment are growing.
"""))
cells.append(new_code_cell("""top_depts = df.groupby('Dept').Weekly_Sales.sum().nlargest(10).index
dept_month = (df[df.Dept.isin(top_depts)]
              .groupby([pd.Grouper(key='Date', freq='MS'), 'Dept']).Weekly_Sales.sum()
              .unstack())

fig, ax = plt.subplots(figsize=(11, 4.4))
dept_month.plot(ax=ax, lw=1.5, colormap='tab10')
ax.set_title('Monthly sales of the ten largest departments')
ax.set_ylabel('Sales ($ millions)')
ax.yaxis.set_major_formatter(lambda v, _: f'{v/1e6:.0f}M')
ax.legend(title='Dept', ncol=2, fontsize=8)
plt.tight_layout()
plt.savefig(OUT / 'fig_dept_trend.png', bbox_inches='tight')
plt.show()

share = df.groupby('Dept').Weekly_Sales.sum().nlargest(10)
print('top departments by revenue:')
print((share / df.Weekly_Sales.sum() * 100).round(1).to_string())
print(f"top 10 departments = {share.sum()/df.Weekly_Sales.sum():.1%} of all sales")
"""))

cells.append(new_code_cell("""# like-for-like: 2012 only reaches October, so compare Feb-Oct 2010 with Feb-Oct 2012
def dept_feb_oct(dept, year):
    s = df[(df.Dept == dept) & (df.Year == year) & (df.Month.between(2, 10))]
    return s.Weekly_Sales.sum()

rows = []
for d in top_depts:
    a, b = dept_feb_oct(d, 2010), dept_feb_oct(d, 2012)
    rows.append({'Dept': d, 'Feb-Oct 2010': a, 'Feb-Oct 2012': b, 'change_%': (b / a - 1) * 100})
growth = pd.DataFrame(rows).sort_values('change_%', ascending=False)

print('Department growth, like-for-like (Feb-Oct 2010 vs Feb-Oct 2012):')
print(growth.assign(**{'Feb-Oct 2010': growth['Feb-Oct 2010'] / 1e6,
                       'Feb-Oct 2012': growth['Feb-Oct 2012'] / 1e6})
        .rename(columns={'Feb-Oct 2010': '2010_$m', 'Feb-Oct 2012': '2012_$m'})
        .round(1).to_string(index=False))
print(f"growing: {(growth['change_%'] > 0).sum()} of {len(growth)} top departments")
"""))

cells.append(new_markdown_cell("""## 7. Breakdown by store format (regional proxy)

The dataset has no geography, so store format and size band are the available regional cuts: type A stores are the largest, C the smallest.
"""))
cells.append(new_code_cell("""type_month = (df.groupby([pd.Grouper(key='Date', freq='MS'), 'Type']).Weekly_Sales.sum()
                .unstack())
type_share = df.groupby('Type').Weekly_Sales.sum()
type_share = type_share / type_share.sum()

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
type_month.plot(ax=axes[0], lw=1.6, color=['#1f3864', '#2c7fb8', '#8ab4f8'])
axes[0].set_title('Monthly sales by store type')
axes[0].set_ylabel('Sales ($ millions)')
axes[0].yaxis.set_major_formatter(lambda v, _: f'{v/1e6:.0f}M')

axes[1].bar(type_share.index, type_share.values * 100, color=['#1f3864', '#2c7fb8', '#8ab4f8'])
axes[1].set_title('Share of total revenue by store type')
axes[1].set_ylabel('% of revenue')
for i, v in enumerate(type_share.values * 100):
    axes[1].text(i, v + 0.6, f'{v:.1f}%', ha='center', fontsize=9)

plt.tight_layout()
plt.savefig(OUT / 'fig_type.png', bbox_inches='tight')
plt.show()

print(pd.DataFrame({'stores': df.groupby('Type').Store.nunique(),
                    'revenue_share_%': (type_share * 100).round(1),
                    'avg_weekly_sales_$': df.groupby('Type').Weekly_Sales.mean().round(0)}).to_string())
"""))

cells.append(new_markdown_cell("""## 8. Bonus — forecasting with exponential smoothing

Holt-Winters (additive trend and seasonality, 12-month period) is fitted on the first 24 months and asked to predict the remaining 9 — statsmodels needs two full seasonal cycles to initialise the seasonal component. It is benchmarked against two naive baselines: last value repeated, and a 3-month rolling mean.
"""))
cells.append(new_code_cell("""from statsmodels.tsa.holtwinters import ExponentialSmoothing

y = monthly.Sales.asfreq('MS')
HOLDOUT = 9
train_y, test_y = y[:-HOLDOUT], y[-HOLDOUT:]

fit = ExponentialSmoothing(train_y, trend='add', seasonal='add', seasonal_periods=12).fit()
fc = fit.forecast(HOLDOUT)

def mape(actual, pred):
    return float(np.mean(np.abs((actual - pred) / actual)) * 100)

naive = pd.Series(train_y.iloc[-1], index=test_y.index)
roll = pd.Series(train_y.iloc[-3:].mean(), index=test_y.index)

print(f'Holt-Winters MAPE : {mape(test_y, fc):.1f}%')
print(f'last-value MAPE   : {mape(test_y, naive):.1f}%')
print(f'3-month mean MAPE : {mape(test_y, roll):.1f}%')

full_fit = ExponentialSmoothing(y, trend='add', seasonal='add', seasonal_periods=12).fit()
future = full_fit.forecast(6)

fig, ax = plt.subplots(figsize=(11, 4.2))
ax.plot(y.index, y / 1e6, label='Actual', color='#1f3864', lw=1.6)
ax.plot(fc.index, fc / 1e6, label='Holt-Winters 9-month holdout forecast', color='darkorange', lw=2)
ax.plot(future.index, future / 1e6, label='Next 6 months', color='seagreen', ls='--', lw=2)
ax.axvline(test_y.index[0], color='grey', ls=':', lw=1)
ax.set_title('Monthly sales with exponential-smoothing forecast')
ax.set_ylabel('Sales ($ millions)')
ax.legend()
plt.tight_layout()
plt.savefig(OUT / 'fig_forecast.png', bbox_inches='tight')
plt.show()

print('\\nnext 6 months ($ millions):')
print((future / 1e6).round(1).to_string())
"""))

cells.append(new_markdown_cell("""## 9. Key findings"""))
cells.append(new_code_cell("""peak = index.idxmax()
trough = index.idxmin()
peak_name = pd.Timestamp(2020, peak, 1).strftime('%B')
trough_name = pd.Timestamp(2020, trough, 1).strftime('%B')
full_years = df[df.Year < 2012].groupby('Year').Weekly_Sales.sum()
growth_1011 = full_years[2011] / full_years[2010] - 1

print('KEY FINDINGS')
print(f"1. Sales grew {growth_1011:+.1%} from 2010 to 2011, and the 12-month moving average")
print(f"   ends {monthly.Rolling12.iloc[-1]/monthly.Rolling12.iloc[11]-1:+.1%} above where it started.")
print(f"2. {peak_name} is the strongest month (index {index.max():.2f}); {trough_name} the weakest ({index.min():.2f}).")
print(f"3. Holiday weeks sell {lift:+.1%} more than ordinary weeks on average;")
print(f"   Thanksgiving week is the single largest week of the year.")
print(f"4. The ten biggest departments are {share.sum()/df.Weekly_Sales.sum():.1%} of revenue;")
print(f"   like-for-like, dept {growth.iloc[0].Dept:.0f} grew {growth.iloc[0]['change_%']:+.1f}% and")
print(f"   dept {growth.iloc[-1].Dept:.0f} fell {growth.iloc[-1]['change_%']:+.1f}% (Feb-Oct 2012 vs Feb-Oct 2010).")
print(f"5. Type A stores are {df[df.Type=='A'].Store.nunique()} stores but {type_share['A']:.1%} of revenue.")
print(f"6. Holt-Winters beats the naive baselines ({mape(test_y, fc):.1f}% MAPE), so the monthly shape")
print(f"   is predictable from history alone; the next quarter is forecast around ${future.mean()/1e6:.0f}M/month.")
"""))

nb = new_notebook(cells=cells, metadata={
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
})
nbformat.write(nb, OUT)
print('written', OUT)
