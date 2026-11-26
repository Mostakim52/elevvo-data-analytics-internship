# Elevvo Data Analytics Internship — Tasks 1–10

Ten analytics tasks built on public datasets, each in its own folder with the deliverable, its
figures, and the script that produced it.

Completed as part of the Elevvo Data Analytics internship track. The brief asks for 4 tasks on
the 1-month format (3 on the 2-week); all ten are included here.

| # | Level | Task | Deliverable | Key result |
|---|-------|------|-------------|------------|
| 1 | 1 | Sales performance dashboard | `task_01/Task1_Sales_Performance_Dashboard.xlsx` | $2.30M revenue · 37,873 units · 12.47% margin · YoY +20.4% |
| 2 | 1 | Titanic EDA | `task_02/Titanic_EDA.ipynb` | 74% female vs 19% male survival; 63% 1st class vs 24% 3rd |
| 3 | 2 | RFM segmentation | `task_03/RFM_Segmentation.ipynb` | Top monetary quintile spends ~50× the bottom |
| 4 | 2 | Survey cleaning & insights | `task_04/Survey_Cleaning_Insights.ipynb` | 4,456 duplicates removed; 5-year schema drift reconciled |
| 5 | 2 | SQL product sales (Chinook) | `task_05/queries.sql`, `results.md` | 10 queries with JOINs + 4 window functions |
| 6 | 3 | Job postings scrape & analysis | `task_06/Job_Postings_Analysis.ipynb` | robots.txt checked; 209 postings; Python/JS dominant |
| 7 | 3 | Walmart time series | `task_07/Walmart_Time_Series.ipynb` | $6.74B analysed; Dec index 1.40 vs Jan 0.81; MAPE 14.4% |
| 8 | 3 | Power BI retail dashboard | `task_08/Task8_PowerBI_Dashboard.pbix` | 3 pages, 24 DAX measures, 5 slicers; reconciles with Task 1 |
| 9 | Industry | Olist cohort analysis & executive report | `task_09/Olist_Cohort_Analysis.ipynb`, `EXECUTIVE_REPORT.md` | 643 of 42,131 2017 customers (1.5%) returned in 2018 |
| 10 | Industry | Marketing A/B test | `task_10/Marketing_AB_Test.ipynb` | +0.769 pp (+43.1% rel.), z = 7.37, p = 1.7e-13 |

**Full index:** [`submission/Elevvo_Submission_README.md`](submission/Elevvo_Submission_README.md)
— how to open each file type, the dataset used per task, reproducibility notes and limitations.

## Opening the work

- **Notebooks** are saved with their outputs executed, so they read on GitHub without running anything.
- **Excel** (`task_01`): sheets `Dashboard`, `Pivot`, `Data`; click any character in a chart first so slicers activate.
- **Power BI** (`task_08`): open the `.pbix` in Power BI Desktop; data is cached in the file. `BUILD_GUIDE.md` documents the model and pages.
- **SQL** (`task_05`): `queries.sql` plus `results.md` with the real output tables, readable without a database.

## Datasets

Not included — they total ~215 MB and all are public: Superstore, Titanic, Online Retail II
(UCI), Kaggle Data Science Survey 2017–2021, Chinook, WeWorkRemotely RSS, Walmart store sales,
the Olist Brazilian e-commerce dataset and the Marketing A/B testing dataset. Each notebook
expects them in a `datasets/` folder beside the task folders; the per-task dataset names are in
the full index.

## Notes

- `task_09/olist_star.sqlite` (the 31 MB star schema) is not committed — GitHub's push
  protection flags a byte sequence in that binary as a key (a false positive). The notebook
  rebuilds it.
- `task_08` Power Query source steps contain the absolute path of the machine that built the
  model; refreshing elsewhere needs only that Source path changed, as `BUILD_GUIDE.md` explains.
