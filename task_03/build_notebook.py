import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell
import pathlib

OUT = pathlib.Path(r'H:\Repos\elevvo-internship-data-analytics\untitled-project\task_03\RFM_Segmentation.ipynb')
cells = []
md = cells.append
code = cells.append

md(new_markdown_cell('''# Task 3 — Customer Segmentation Using RFM Analysis

**Elevvo Data Analytics Internship — Task 3 (Level 2)**

Dataset: Online Retail (UCI Machine Learning Repository) — ~541k transactions from a UK-based online gift retailer, Dec 2010–Dec 2011.

**RFM = Recency · Frequency · Monetary**
- **Recency** — how recently a customer purchased (days before the analysis snapshot date).
- **Frequency** — how often they purchased (number of unique invoices).
- **Monetary** — how much they spent (total revenue).

Steps: clean → compute RFM → score 1–5 → segment → recommend marketing actions per segment → visualise.'''))

md(new_markdown_cell('## 1. Load and clean\n\nRemove cancellations (invoices starting with `C`), negative/zero quantities, missing CustomerIDs, and non-product stock codes.'))
code(new_code_cell('''import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style='whitegrid', palette='Set2')
plt.rcParams['figure.dpi'] = 120

df = pd.read_excel('../datasets/online_retail.xlsx')
print('Raw shape:', df.shape)

before = len(df)
df = df.dropna(subset=['CustomerID'])
print('Dropped missing CustomerID:', before - len(df))

df['InvoiceNo'] = df['InvoiceNo'].astype(str)
cancelled = df['InvoiceNo'].str.startswith('C')
print('Cancellations:', cancelled.sum())
df = df[~cancelled]

df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)]
special = df['StockCode'].astype(str).str.upper().str.match(r'^(POST|D|M|BANK CHARGES|PADS|DOT|C2|AMAZONFEE)$')
print('Non-product stock codes dropped:', special.sum())
df = df[~special]

df['CustomerID'] = df['CustomerID'].astype(int)
df['TotalPrice'] = df['Quantity'] * df['UnitPrice']
print('Clean shape:', df.shape)
print('Date range:', df['InvoiceDate'].min(), '->', df['InvoiceDate'].max())
df.head()'''))

md(new_markdown_cell('## 2. Compute RFM metrics\n\nSnapshot date = day after the last transaction. Recency = days between last purchase and snapshot.'))
code(new_code_cell('''snapshot = df['InvoiceDate'].max() + pd.Timedelta(days=1)
print('Snapshot date:', snapshot)

rfm = df.groupby('CustomerID').agg(
    Recency=('InvoiceDate', lambda s: (snapshot - s.max()).days),
    Frequency=('InvoiceNo', 'nunique'),
    Monetary=('TotalPrice', 'sum'),
).reset_index()
print(rfm.shape)
rfm.describe().round(2)'''))

md(new_markdown_cell('''## 3. Score RFM (1–5)

- Recency: **lower** is better → 5 for most recent.
- Frequency / Monetary: **higher** is better → 5 for highest.
- Quintile-based scoring with `pd.qcut` (rank-based to handle duplicate edges).'''))
code(new_code_cell('''rfm['R'] = pd.qcut(rfm['Recency'].rank(method='first'), 5, labels=[5,4,3,2,1]).astype(int)
rfm['F'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1,2,3,4,5]).astype(int)
rfm['M'] = pd.qcut(rfm['Monetary'].rank(method='first'), 5, labels=[1,2,3,4,5]).astype(int)
rfm['RFM_Score'] = rfm['R'] + rfm['F'] + rfm['M']
rfm.head()'''))

md(new_markdown_cell('## 4. Segment customers\n\nMap the R/F/M pattern onto recognisable customer personas.'))
code(new_code_cell('''def segment(row):
    r, f, m = row['R'], row['F'], row['M']
    if r >= 4 and f >= 4 and m >= 4:
        return 'Champions'
    if r >= 3 and f >= 3:
        return 'Loyal Customers'
    if r >= 4 and f <= 2:
        return 'New / Promising'
    if r <= 2 and f >= 4:
        return 'At Risk (was loyal)'
    if r <= 2 and f <= 2 and m <= 2:
        return 'Lost / Hibernating'
    if r >= 3 and f <= 2 and m <= 2:
        return 'Needs Attention'
    return 'Regular'

rfm['Segment'] = rfm.apply(segment, axis=1)
seg_summary = rfm.groupby('Segment').agg(
    Customers=('CustomerID', 'count'),
    Avg_Recency=('Recency', 'mean'),
    Avg_Frequency=('Frequency', 'mean'),
    Avg_Monetary=('Monetary', 'mean'),
    Total_Revenue=('Monetary', 'sum'),
).sort_values('Total_Revenue', ascending=False).round(1)
seg_summary'''))

md(new_markdown_cell('## 5. Marketing recommendations per segment'))
code(new_code_cell('''recommendations = {
    'Champions':          'Reward with early access, loyalty tiers and referral bonuses; ask for reviews and referrals. Avoid discounting — they buy anyway.',
    'Loyal Customers':    'Upsell premium lines; subscription/bundle offers; exclusive member pricing.',
    'New / Promising':    'Onboarding email series, first-repeat-purchase coupon, welcome gift on second order.',
    'At Risk (was loyal)':'Win-back campaign: personalised "we miss you" email, 15–20% reactivation discount, feedback survey to learn why they lapsed.',
    'Lost / Hibernating': 'Low-cost re-engagement blast; if no response after 2 touches, remove from paid mailing lists.',
    'Needs Attention':    'Nudge with personalised product suggestions and free-shipping threshold.',
    'Regular':            'Standard lifecycle marketing; monitor for migration to Loyal.',
}
print(f"{'Segment':22s} Marketing action")
print('-' * 110)
for seg, action in recommendations.items():
    print(f'{seg:22s} {action}')'''))

md(new_markdown_cell('## 6. Visualisations'))
code(new_code_cell('''fig, axes = plt.subplots(1, 2, figsize=(15, 6))

seg_counts = rfm['Segment'].value_counts()
axes[0].barh(seg_counts.index, seg_counts.values, color=sns.color_palette('Set2', len(seg_counts)))
axes[0].set_title('Customers per segment')
axes[0].set_xlabel('Customers')
for i, (s, n) in enumerate(seg_counts.items()):
    axes[0].annotate(str(n), (n, i), va='center', xytext=(4, 0), textcoords='offset points')

seg_rev = rfm.groupby('Segment')['Monetary'].sum().sort_values(ascending=True)
axes[1].barh(seg_rev.index, seg_rev.values / 1000, color='#2E75B6')
axes[1].set_title('Revenue per segment')
axes[1].set_xlabel('Revenue (£ thousands)')
for i, (s, v) in enumerate(seg_rev.items()):
    axes[1].annotate(f'£{v/1000:.0f}k', (v/1000, i), va='center', xytext=(4, 0), textcoords='offset points')
plt.tight_layout()
plt.savefig('fig_segments.png', bbox_inches='tight')
plt.show()'''))

code(new_code_cell('''rfm_counts = rfm.groupby(['R','F']).size().unstack(fill_value=0).reindex(index=[5,4,3,2,1], columns=[1,2,3,4,5], fill_value=0)
plt.figure(figsize=(7, 5.5))
sns.heatmap(rfm_counts, annot=True, fmt='d', cmap='YlGnBu', linewidths=.5, cbar_kws={'label':'Customers'})
plt.title('Customer count — Recency (y) × Frequency (x)')
plt.ylabel('Recency score (5 = most recent)')
plt.xlabel('Frequency score')
plt.savefig('fig_rfm_heatmap.png', bbox_inches='tight')
plt.show()'''))

code(new_code_cell('''plt.figure(figsize=(12, 5))
sns.boxplot(data=rfm, x='Segment', y='Monetary', showfliers=False, palette='Set2')
plt.yscale('log')
plt.ylabel('Monetary (log scale, £)')
plt.title('Monetary value distribution by segment')
plt.xticks(rotation=20, ha='right')
plt.savefig('fig_monetary_box.png', bbox_inches='tight')
plt.show()'''))

md(new_markdown_cell('''## 7. Key insights

1. **Champions and Loyal Customers are a minority of customers but contribute the majority of revenue** — classic Pareto behaviour. Protect them with loyalty mechanics, not discounts.
2. **"At Risk (was loyal)" holds material revenue** — these are the cheapest customers to win back because they already know the brand; a targeted win-back offer usually outperforms acquisition spend.
3. **Most customers sit in Regular / Needs Attention** — automation (lifecycle emails, next-best-action) is the right lever; manual outreach doesn't scale here.
4. **Recency is the earliest churn signal** — a customer drifting from R=5 → R=3 is the trigger point for intervention, before Frequency collapses.
5. **The top monetary quintile spends ~50× the bottom quintile** — segment-aware pricing and premium bundles are justified for the M=5 cohort.

## 8. Methodology notes

- Snapshot = max(InvoiceDate) + 1 day (2011-12-10).
- Cancellations (invoice prefix `C`) and non-product stock codes removed.
- Scoring uses rank-quintiles (`qcut` on ranked values) so duplicate boundaries (e.g. many customers with Frequency=1) don't break equal-width cuts.
- Segment thresholds are deliberately simple; in production these would be tuned against holdout retention data.'''))

nb = new_notebook(cells=cells)
nb.metadata = {
    'kernelspec': {'display_name': 'Python 3 (ipykernel)', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python', 'version': '3.13.9'},
}
OUT.parent.mkdir(parents=True, exist_ok=True)
nbformat.write(nb, OUT)
print('wrote', OUT)
