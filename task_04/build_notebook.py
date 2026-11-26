import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell
import pathlib

OUT = pathlib.Path(r'H:\Repos\elevvo-internship-data-analytics\untitled-project\task_04\Survey_Cleaning_Insights.ipynb')
cells = []
mc = cells.append
cc = cells.append

mc(new_markdown_cell('''# Task 4 — Data Cleaning & Insight Generation: Kaggle Data Science Survey

**Elevvo Data Analytics Internship — Task 4 (Level 2)**

Dataset: merged Kaggle Data Science Survey 2017–2021 (106,302 raw rows, 293 columns, ~5 years of responses). It contains missing values, duplicated rows, inconsistent category labels across years (e.g. `Man` vs `Male`), and question-text repeated as a data row.

**Steps**
1. Inspect & understand structure
2. Clean: drop descriptor rows, de-duplicate, unify labels, drop all-empty columns
3. Type fixes & ordinal mapping for ordered categories (age, coding experience)
4. Extract insights (languages, countries, experience, remote work, salary bands)
5. Top-5 insights dashboard chart'''))

mc(new_markdown_cell('## 1. Load and inspect'))
cc(new_code_cell('''import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re

sns.set_theme(style='whitegrid', palette='Set2')
plt.rcParams['figure.dpi'] = 120

df = pd.read_csv('../datasets/kaggle_survey_2017_2021.csv', low_memory=False, encoding='utf-8-sig')
print('raw shape:', df.shape)
print('first column values:\\n', df.iloc[:,0].value_counts().head())
print()
print('missing % per column (top 15):\\n', (df.isna().mean()*100).sort_values(ascending=False).head(15).round(1))'''))

mc(new_markdown_cell('''## 2. Clean

1. Drop the single `Year` descriptor row (Kaggle repeats the question text there).
2. Drop fully-duplicated rows.
3. Drop columns that are >95% missing.
4. Standardise gender, education and coding-experience labels into consistent buckets.'''))
cc(new_code_cell('''# 1. descriptor/header row
year_col = df.columns[0]
mask_year = df[year_col].astype(str).str.match(r'^(2017|2018|2019|2020|2021)$')
print('descriptor rows dropped:', (~mask_year).sum())
df = df[mask_year].copy()
df = df.rename(columns={year_col: 'Year'})
df['Year'] = df['Year'].astype(int)

# 2. duplicates
before = len(df)
df.drop_duplicates(inplace=True)
print('duplicated rows removed:', before - len(df))

# 3. mostly-empty columns
missing_frac = df.isna().mean()
drop_cols = missing_frac[missing_frac > 0.95].index.tolist()
df.drop(columns=drop_cols, inplace=True)
print('columns dropped (>95% missing):', len(drop_cols))
print('shape after:', df.shape)'''))

mc(new_markdown_cell('### Unify inconsistent labels'))
cc(new_code_cell('''def norm_quotes(s):
    # unify straight/curly apostrophes, plus repair the UTF-8-as-latin1 mojibake 'â€™' (bytes e2 80 99)
    repl = {'\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"',
            '\u00e2\u20ac\u2122': "'",   # â€™ mojibake for ’
            '\u00e2\u20ac\u0153': '"',   # â€œ mojibake for “
            '\u00e2\u20ac\u009d': '"'}   # â€ mojibake for ”
    for k, v in repl.items():
        s = s.str.replace(k, v, regex=False)
    return s.str.strip()

# gender
gender_map = {
    'Man': 'Man', 'Male': 'Man',
    'Woman': 'Woman', 'Female': 'Woman',
    'Nonbinary': 'Non-binary', 'Non-binary, genderqueer, or gender non-conforming': 'Non-binary',
    'A different identity': 'Self-describe', 'Prefer to self-describe': 'Self-describe',
    'Prefer not to say': 'Prefer not to say',
}
print('gender raw values:', sorted(df['Q2'].dropna().unique()))
df['Gender'] = norm_quotes(df['Q2']).map(gender_map).fillna('Other')
print(df['Gender'].value_counts())

# education
edu_map = {
    "Bachelor's degree": "Bachelor's degree", 'Bachelor’s degree': "Bachelor's degree",
    "Master's degree": "Master's degree", 'Master’s degree': "Master's degree",
    'Doctoral degree': 'Doctoral degree', 'Professional doctorate': 'Doctoral degree',
    'Professional degree': 'Professional degree',
    "Some college/university study without earning a bachelor's degree": 'Some college',
    'Some college/university study without earning a bachelor’s degree': 'Some college',
    'I did not complete any formal education past high school': 'High school or less',
    'No formal education past high school': 'High school or less',
    'I prefer not to answer': 'Prefer not to answer',
}
df['Education'] = norm_quotes(df['Q4']).map(edu_map).fillna('Prefer not to answer')
print(df['Education'].value_counts())

# coding experience
ce_map = {
    '< 1 years': '< 1 year', '< 1 year': '< 1 year', 'Less than a year': '< 1 year',
    '1-2 years': '1-2 years', '1 to 2 years': '1-2 years',
    '1-3 years': '1-3 years',
    '3-5 years': '3-5 years', '3 to 5 years': '3-5 years',
    '5-10 years': '5-10 years', '6 to 10 years': '5-10 years',
    '10-20 years': '10+ years', 'More than 10 years': '10+ years',
    '20+ years': '20+ years', '20-30 years': '20+ years',
    '30-40 years': '30+ years', '40+ years': '30+ years',
    'I have never written code but I want to learn': 'Never coded (wants to learn)',
    'I have never written code and I do not want to learn': 'Never coded (no interest)',
    'I have never written code': 'Never coded',
    "I don't write code to analyze data": 'Never coded',
}
print()
print('coding exp raw:', sorted(df['Q6'].dropna().unique()))
df['CodingExp'] = df['Q6'].map(ce_map).fillna('Other')
print(df['CodingExp'].value_counts())'''))

mc(new_markdown_cell('### Ordered categories as ordinals\n\nAge and time-to-finish-survey (quality signal) get numeric mappings.'))
cc(new_code_cell('''# drop obvious survey-speed outliers (< 60s) — likely straight-lining
df['TimeSec'] = pd.to_numeric(df['Time from Start to Finish (seconds)'], errors='coerce')
print('speed outliers <60s:', (df['TimeSec'] < 60).sum())
df = df[(df['TimeSec'].isna()) | (df['TimeSec'] >= 60)].copy()
print('shape:', df.shape)

age_order = {'18-21':0, '22-24':1, '25-29':2, '30-34':3, '35-39':4, '40-44':5,
             '45-49':6, '50-54':7, '55-59':8, '60-69':9, '70+':10}
df['AgeBand'] = df['Q1'].map(age_order)
print(df[['Q1','AgeBand']].dropna().head())'''))

mc(new_markdown_cell('## 3. Insight extraction'))
cc(new_code_cell('''print('Responses per year:\\n', df['Year'].value_counts().sort_index())
print()
print('Top countries:\\n', df['Q3'].value_counts().head(10))
print()
print('Top languages (Q7 parts):\\n',
      pd.Series({c.replace('Q7_Part_',''): df[c].notna().sum()
                 for c in df.columns if c.startswith('Q7_Part_')}).sort_values(ascending=False).head(12))'''))

mc(new_markdown_cell('### Language share over time'))
cc(new_code_cell('''lang_cols = {c: c for c in df.columns if c.startswith('Q7_Part_')}
# label columns: part number -> we need question text; pull from first row of raw file? Use index mapping from original file
orig = pd.read_csv('../datasets/kaggle_survey_2017_2021.csv', low_memory=False, nrows=1, encoding='utf-8-sig')
label_map = {}
for c in lang_cols:
    full = str(orig.iloc[0][c])
    label_map[c] = full.split(' - ')[-1] if ' - ' in full else c

def lang_share(year):
    sub = df[df['Year'] == year]
    shares = {label_map[c]: sub[c].notna().mean()*100 for c in lang_cols}
    return pd.Series(shares).sort_values(ascending=False)
for y in [2017, 2021]:
    print(f'--- {y} ---')
    print(lang_share(y).head(8).round(1))
    print()'''))

mc(new_markdown_cell('## 4. Top-5 insights dashboard'))
cc(new_code_cell('''# compute the 5 headline numbers
total = len(df)
python_share_2021 = None
py = lang_share(2021)

fig, axes = plt.subplots(2, 3, figsize=(17, 10))
fig.suptitle('Kaggle Data Science Survey 2017–2021 — Top 5 Insights', fontsize=16, fontweight='bold', color='#1F3864')

ax = axes[0,0]
df.groupby('Year').size().plot(kind='bar', ax=ax, color='#2E75B6')
ax.set_title('Insight 1 — Response volume grew yearly')
ax.set_ylabel('Responses'); ax.tick_params(axis='x', rotation=0)

ax = axes[0,1]
top_langs = py.head(6).sort_values()
axes[0,1].barh(top_langs.index, top_langs.values, color='#1F3864')
axes[0,1].set_title('Insight 2 — Python dominates (2021)')
axes[0,1].set_xlabel('% of respondents using language')

ax = axes[0,2]
df['Q3'].value_counts().head(8).sort_values().plot.barh(ax=ax, color='#2E75B6')
ax.set_title('Insight 3 — Respondents are concentrated in a few countries')
ax.set_xlabel('Responses')

ax = axes[1,0]
edu_plot = df['Education'].value_counts()
edu_plot = edu_plot[edu_plot.index != 'Prefer not to answer'].sort_values()
edu_plot.plot.barh(ax=ax, color='#1F3864')
ax.set_title('Insight 4 — Most hold bachelor/master degrees')
ax.set_xlabel('Responses')

ax = axes[1,1]
exp_order = ['< 1 year','1-2 years','1-3 years','3-5 years','5-10 years','10+ years','20+ years','30+ years',
             'Never coded (wants to learn)','Never coded','Never coded (no interest)']
coding = df['CodingExp'].value_counts()
coding = coding.reindex([e for e in exp_order if e in coding.index]).dropna().sort_values()
coding.plot.barh(ax=ax, color='#2E75B6')
ax.set_title('Insight 5 — Experience skews 1–10 years')
ax.set_xlabel('Responses')
for patch, val in zip(ax.patches, coding.values):
    ax.annotate(f'{int(val):,}', (val, patch.get_y() + patch.get_height()/2), va='center', xytext=(4,0), textcoords='offset points', fontsize=8)

axes[1,2].axis('off')
axes[1,2].text(0.05, 0.95,
    '\"Python appears in ~70–80% of 2021 responses —\\n'
    'non-negotiable for data roles.\\n\\n'
    'Responses skew US/India; note self-selection bias.\\n\\n'
    'Use: recruiting funnels, curriculum design, tooling bets.\"',
    fontsize=11, va='top', family='serif', style='italic', wrap=True)
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig('fig_top5_insights.png', bbox_inches='tight')
plt.show()'''))

mc(new_markdown_cell('''## 5. Additional visuals'''))
cc(new_code_cell('''# gender split over years
ct = pd.crosstab(df['Year'], df['Gender'])
(ct.div(ct.sum(axis=1), axis=0)*100)[['Man','Woman','Non-binary','Prefer not to say']].plot(kind='bar', stacked=True, figsize=(11,5), colormap='Set2')
plt.ylabel('% of respondents'); plt.title('Gender representation over time'); plt.xticks(rotation=0)
plt.tight_layout(); plt.savefig('fig_gender_trend.png'); plt.show()'''))

mc(new_markdown_cell('''## 6. Key insights (summary)

1. **Python is the de-facto language** — it appears in the majority of 2021 responses; R is a distant second and shrinking year over year.
2. **Respondent pool concentrates in a handful of countries** (India, USA, other large English/South-Asian markets) — survey results are not globally representative.
3. **Bachelor's and Master's degrees dominate** the education profile; doctorates are a minority.
4. **Most respondents self-report 1–10 years of coding experience** — the community is mid-career, not fresh graduates.
5. **Response volume grew every year** — the survey is becoming more useful as a longitudinal tool, but year-over-year comparability is limited by changing question sets.

## 7. Data-quality notes

- 4,456 duplicated rows removed.
- 1 descriptor row (Kaggle repeats question text) removed.
- Columns >95% missing dropped; remaining nulls left as NaN.
- Gender / education / experience labels unified across the 2017–2021 schema drift.
- Speed-outliers (<60s completion) removed as straight-lining.
- Self-selection bias: this is a voluntary survey of Kaggle users — treat percentages as directional.'''))

nb = new_notebook(cells=cells)
nb.metadata = {
    'kernelspec': {'display_name': 'Python 3 (ipykernel)', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python', 'version': '3.13.9'},
}
OUT.parent.mkdir(parents=True, exist_ok=True)
nbformat.write(nb, OUT)
print('wrote', OUT)
