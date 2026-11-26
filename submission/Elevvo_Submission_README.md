# Elevvo Data Analytics Internship — Task Submission

**Intern:** Mostakim Hossain
**Program:** Elevvo Internship — Pro Plan (Data Analytics track)
**Tasks completed:** all 10 (the brief requires 3 for the 2-week and 4 for the 1-month internship)
**Contents of this package:** one folder per task, numbered in the same order as `Data Analytics Tasks.pdf`

> **How to read this package.** One folder per task, plus `00_Start_Here/` holding this README. The package also exists as two zips — `..._Part1_Tasks_1-6.zip` and `..._Part2_Tasks_7-10.zip` — split only because the Task 9 star-schema database is 31 MB on its own and email attachments cap at 25 MB; each part contains this README and together they hold all ten tasks. If you received this as a shared Drive or GitHub link, ignore the split and read the single folder tree.

| # | Level | Task | Main deliverable | Key result |
|---|-------|------|------------------|------------|
| 1 | 1 | Sales Performance Dashboard (Excel) | `Task_01_Excel_Dashboard/Task1_Sales_Performance_Dashboard.xlsx` (+ PDF preview) | $2,297,200.65 revenue · 37,873 units · $286,396.54 profit · 12.47% margin · YoY +20.4% |
| 2 | 1 | EDA on Titanic | `Task_02_Titanic_EDA/Titanic_EDA.ipynb` (executed) + 3 figures | 74% female vs 19% male survival; 1st class 63% vs 3rd 24%; 1st-class women 97% |
| 3 | 2 | RFM Customer Segmentation | `Task_03_RFM_Segmentation/RFM_Segmentation.ipynb` + 3 figures | Champions/Loyal = minority of customers but majority of revenue; top monetary quintile ≈ 50× the bottom |
| 4 | 2 | Survey Data Cleaning & Insights | `Task_04_Survey_Cleaning_Insights/Survey_Cleaning_Insights.ipynb` + 2 figures | 4,456 duplicate rows removed; Python dominant and growing; response volume rising every year |
| 5 | 2 | SQL Product Sales Analysis (Chinook) | `Task_05_SQL_Analysis/queries.sql`, `results.md`, `insights.md` | 10 queries with JOINs + 4 window functions; Europe €1,114 vs Americas $1,101 revenue |
| 6 | 3 | Web Scraping & Job Posting Analysis | `Task_06_Job_Postings/Job_Postings_Analysis.ipynb` + `jobs_clean.csv` + 4 figures | Python/JS dominant; AWS+Docker+K8s table stakes; senior roles far outnumber junior |
| 7 | 3 | Walmart Retail Time Series | `Task_07_Walmart_Time_Series/Walmart_Time_Series.ipynb`, `insights.md` + 7 figures | $6.74B analysed; December index 1.40, January 0.81; Holt-Winters MAPE 14.4% |
| 8 | 3 | Power BI Retail Dashboard | `Task_08_PowerBI/Task8_PowerBI_Dashboard.pbix` (+ PDF, screenshot, build guide) | 3 report pages, 6 KPI cards, 5 slicers, 24 DAX measures; matches Task 1 to the cent |
| 9 | Industry | Olist Cohort Analysis & Executive Report | `Task_09_Olist_Executive_Report/` notebook + `EXECUTIVE_REPORT.md` + `olist_star.sqlite` | Of 42,131 customers acquired in 2017, only 643 (1.5%) bought again in 2018; delivery↔review r = −0.56 |
| 10 | Industry | Marketing A/B Test | `Task_10_AB_Test/Marketing_AB_Test.ipynb` + 4 figures | Control 1.785% vs test 2.555%; +0.769 pp (+43.1% relative), z = 7.37, p = 1.7e-13 |

---

## How to open the deliverables

**Excel (Task 1).** Open `Task1_Sales_Performance_Dashboard.xlsx` in Excel. Sheets: `Dashboard` (KPI cards, charts, 5 slicers), `Pivot` (pivot tables), `Data`. If a slicer does not respond immediately, click any character in the dashboard first so Excel recalculates. The `.pdf` is an export of the same dashboard for reviewers without Excel.

**Notebooks (Tasks 2, 3, 4, 6, 7, 9, 10).** All are **already executed** — every table, chart and printed metric is stored in the file, so they can be read on GitHub or in any viewer without running anything. To re-run: `jupyter notebook <file>.ipynb` from the package root; data paths are relative to `datasets/` (see *Datasets* below), so keep the folder next to the `datasets` directory or edit the one `DATA_DIR` line at the top of a notebook.

**Power BI (Task 8).** Open `Task8_PowerBI_Dashboard.pbix` in Power BI Desktop (free). The data is cached in the file, so it renders immediately without a refresh. `BUILD_GUIDE.md` explains the model, every page/visual, and how the file was generated; `pbip/` contains the editable Power BI Project source (TMDL model + PBIR report).

**SQL (Task 5).** `queries.sql` holds the 10 commented queries (SQLite dialect) and `results.md` holds their real output tables, so the results can be reviewed without a database. The database used is `datasets/Chinook.sqlite`; run with `sqlite3 datasets/Chinook.sqlite < queries.sql`.

**Task 9 database.** `olist_star.sqlite` is the star schema (`fact_order_items`, `dim_customers`, `dim_orders`, `dim_products`, `dim_date`) built from the raw Olist CSVs before any visualisation — the industry constraint in the brief.

---

## Datasets

The raw datasets are public and are **not** included in this package (they total ~215 MB). They were downloaded to a local `datasets/` folder:

| Task | Dataset |
|---|---|
| 1, 8 | Superstore Sales (`superstore.csv`) |
| 2 | Titanic: Machine Learning from Disaster (`titanic.csv`) |
| 3 | Online Retail II, UCI (`online_retail.xlsx`) |
| 4 | Kaggle Data Science Survey 2017–2021 (`kaggle_survey_2017_2021.csv`) |
| 5 | Chinook (`Chinook.sqlite`) |
| 6 | WeWorkRemotely public RSS feeds (scraped live; raw snapshot included as `jobs_raw.json`) |
| 7 | Walmart Store Sales Forecasting (`walmart_train.csv`, `walmart_stores.csv`, `walmart_features.csv`) |
| 9 | Brazilian E-Commerce Public Dataset by Olist (9 CSVs) |
| 10 | Marketing A/B Testing (`marketing_AB.csv`) |

## Reproducibility

Every task folder keeps the script that generated it (`build_excel.py`, `build_model.py`, `build_pbix_project.py`, `scrape.py`, `build_notebook.py`), so each result can be rebuilt from the source data. Python 3.12 (Anaconda) with pandas, numpy, matplotlib, seaborn, scipy, statsmodels, openpyxl and pywin32. No private credentials or paid services are used.

## Notes and honest limitations

- **Task 1:** `Sales` and `Profit` in the source file are the standard Superstore row values; the pivot totals reproduce `metrics.json` exactly.
- **Task 5:** Chinook is a demo database with near-uniform $0.99/$1.99 pricing, so "top-selling" lists are effectively ties broken alphabetically — a property of the data, not the query.
- **Task 7:** Walmart's file has no state or city, so store *type/size* is used as the regional cut (documented in `insights.md`).
- **Task 8:** The model's Power Query source steps point at the CSV folder on the build machine (`H:\Repos\...\task_08\model\`). Refreshing on another machine only needs that Source path changed — see `BUILD_GUIDE.md`. Publishing to the Power BI Service (the optional bonus) was not done because it requires an organisational account.
- **Task 9:** Month-1 retention is genuinely ~0.5–1.9% in this dataset; the heatmap shows returning-customer counts as well as rates because rates at that level are hard to read.
- **Task 6:** a live RSS snapshot, not a historical census; counts are directional.
- **GitHub mirror:** the 31 MB `olist_star.sqlite` ships in the zip/Drive package but is not committed to the GitHub repo — its binary contains a byte sequence that GitHub's push protection flags as a Twilio key (a false positive). Running the Task 9 notebook rebuilds it in one pass.
