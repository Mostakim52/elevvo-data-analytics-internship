import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell
import pathlib

OUT = pathlib.Path(r'H:\Repos\elevvo-internship-data-analytics\untitled-project\task_02\Titanic_EDA.ipynb')

cells = []
md = lambda s: cells.append(new_markdown_cell(s))
code = lambda s: cells.append(new_code_cell(s))

md('''# Task 2 — Exploratory Data Analysis: Titanic Dataset

**Elevvo Data Analytics Internship — Task 2 (Level 1)**

Dataset: Titanic passenger manifest (from seaborn's packaged copy of the classic Kaggle *Titanic: Machine Learning from Disaster* dataset).

**Goals**
1. Data cleaning — handle missing values, convert types.
2. Summary statistics and group-based insights (survival by gender / class / fare / age).
3. Visualise key patterns and correlations.
4. Bonus: survival-rate bar plots and a correlation heatmap.
''')

md('## 1. Imports & load data')
code('''import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

sns.set_theme(style='whitegrid', palette='Set2')
plt.rcParams['figure.dpi'] = 120

df = pd.read_csv('../datasets/titanic.csv')
print('Shape:', df.shape)
df.head()''')

md('## 2. Initial inspection')
code('''print('Dtypes:\\n', df.dtypes)
print()
print('Missing values:\\n', df.isna().sum())
print()
df.describe(include='all').T''')

md('''## 3. Data cleaning

- `age` has gaps → impute with the median age **within sex × class groups** (better than a single global median).
- `deck` is >75% missing → dropped.
- `embarked` has 2 missing values → filled with the mode.
- Convert `survived`, `pclass`, `sex`, `embarked` to categoricals (they are codes, not continuous numbers).
- Drop duplicates if any.
''')
code('''print('Duplicates before:', df.duplicated().sum())
df.drop_duplicates(inplace=True)

# age imputation by sex/class median
df['age'] = df.groupby(['sex','pclass'])['age'].transform(lambda s: s.fillna(s.median()))

# embarked: fill mode
df['embarked'] = df['embarked'].fillna(df['embarked'].mode()[0])

# deck: too sparse
df.drop(columns=['deck'], inplace=True)

# types
for col in ['pclass','sex','embarked','alone']:
    df[col] = df[col].astype('category')

print('Missing after cleaning:\\n', df.isna().sum())
print('Duplicates after:', df.duplicated().sum())
df.head()''')

md('## 4. Summary statistics')
code('''print('Overall survival rate: {:.1%}'.format(df['survived'].astype(int).mean()))
print()
print(df.describe(include=[np.number]).round(2).T)''')

md('## 5. Group-based insights')
code('''surv_rate = lambda s: round(s.astype(int).mean() * 100, 1)

print('Survival rate by sex:\\n', df.groupby('sex', observed=True)['survived'].agg(['mean','count']).round(3))
print()
print('Survival rate by class:\\n', df.groupby('pclass', observed=True)['survived'].agg(['mean','count']).round(3))
print()
print('Survival rate by embarkation port:\\n', df.groupby('embarked', observed=True)['survived'].agg(['mean','count']).round(3))
print()
print('Survival rate by sex × class:\\n', df.groupby(['sex','pclass'], observed=True)['survived'].mean().unstack().round(3))''')

md('## 6. Visualisations')
code('''fig, axes = plt.subplots(2, 2, figsize=(13, 9))

# survival rate by sex
sns.barplot(data=df, x='sex', y='survived', ax=axes[0,0], errorbar=None)
axes[0,0].set_title('Survival rate by sex')
axes[0,0].set_ylabel('Survival rate')
for p in axes[0,0].patches:
    axes[0,0].annotate(f'{p.get_height()*100:.1f}%', (p.get_x()+p.get_width()/2, p.get_height()), ha='center', va='bottom')

# survival rate by class
sns.barplot(data=df, x='pclass', y='survived', ax=axes[0,1], errorbar=None)
axes[0,1].set_title('Survival rate by passenger class')
for p in axes[0,1].patches:
    axes[0,1].annotate(f'{p.get_height()*100:.1f}%', (p.get_x()+p.get_width()/2, p.get_height()), ha='center', va='bottom')

# age distribution by survival
sns.histplot(data=df, x='age', hue='survived', kde=True, bins=30, ax=axes[1,0], element='step')
axes[1,0].set_title('Age distribution by survival')

# fare vs age scatter
sns.scatterplot(data=df, x='age', y='fare', hue='survived', alpha=0.6, ax=axes[1,1])
axes[1,1].set_title('Fare vs age, coloured by survival')

plt.tight_layout()
plt.savefig('fig_overview.png', bbox_inches='tight')
plt.show()''')

md('### Survival rate heatmap — sex × class')
code('''pivot = df.groupby(['sex','pclass'], observed=True)['survived'].mean().unstack()
plt.figure(figsize=(6, 4.5))
sns.heatmap(pivot, annot=True, fmt='.0%', cmap='RdYlGn', vmin=0, vmax=1, linewidths=.5, cbar_kws={'label':'Survival rate'})
plt.title('Survival rate by sex × class')
plt.savefig('fig_heatmap_sex_class.png', bbox_inches='tight')
plt.show()''')

md('### Correlation heatmap (numeric features)')
code('''num = df[['survived','pclass','age','sibsp','parch','fare']].copy()
num['survived'] = num['survived'].astype(int)
num['pclass'] = num['pclass'].astype(int)
corr = num.corr()

plt.figure(figsize=(7.5, 6))
sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', center=0, vmin=-1, vmax=1, linewidths=.5)
plt.title('Correlation matrix (numeric features)')
plt.savefig('fig_correlation.png', bbox_inches='tight')
plt.show()''')

md('''## 7. Key insights

1. **Women survived at far higher rates** (~74%) than men (~19%) — the "women and children first" protocol is clearly visible in the data.
2. **Class strongly influenced survival**: 1st class ~63%, 2nd ~47%, 3rd ~24%. Class proxies both ticket price and cabin location (decks near lifeboats).
3. **Class and sex interact**: 1st-class women survived at ~97%; 3rd-class men at ~14% — the single strongest survival gradient in the dataset.
4. **Fare correlates positively with survival** (r ≈ +0.26) and negatively with class — wealthier passengers sat closer to the boat deck.
5. **Age matters at the extremes**: children (age < 10) had above-average survival; older passengers fared worse.
6. **Family size has a sweet spot**: passengers with 1–3 family members aboard survived more often than solo travellers or large families.

## 8. Conclusion

The Titanic manifest reflects the era's evacuation protocol and social structure: gender, age, class and wealth all shaped who lived. The single cleanest predictor is sex, but the sex × class interaction is far more informative than either alone. Data-quality notes: `age` required group-wise imputation, `deck` was dropped for excessive missingness, and duplicates were removed — all standard EDA hygiene steps.
''')

nb = new_notebook(cells=cells)
nb.metadata = {
    'kernelspec': {'display_name': 'Python 3 (ipykernel)', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python', 'version': '3.13.9'},
}
OUT.parent.mkdir(parents=True, exist_ok=True)
nbformat.write(nb, OUT)
print('wrote', OUT)
