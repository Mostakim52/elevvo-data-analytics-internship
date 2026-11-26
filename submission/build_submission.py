"""Stage the task deliverables into one submission folder and zip it."""
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # untitled-project/
SUB = ROOT / "submission"
STAGE = SUB / "Elevvo_Data_Analytics_Submission_Mostakim_Hossain"
# The Olist database alone is ~16 MB compressed, so the package is split in two
# email-sized parts (Gmail rejects attachments over 25 MB).
PARTS = {
    "Part1_Tasks_1-6": ["00_Start_Here", "Task_01_Excel_Dashboard", "Task_02_Titanic_EDA",
                        "Task_03_RFM_Segmentation", "Task_04_Survey_Cleaning_Insights",
                        "Task_05_SQL_Analysis", "Task_06_Job_Postings"],
    "Part2_Tasks_7-10": ["00_Start_Here", "Task_07_Walmart_Time_Series", "Task_08_PowerBI",
                         "Task_09_Olist_Executive_Report", "Task_10_AB_Test"],
}

# folder -> files (relative to untitled-project/)
MANIFEST = {
    "00_Start_Here": ["submission/Elevvo_Submission_README.md"],
    "Task_01_Excel_Dashboard": [
        "task_01/Task1_Sales_Performance_Dashboard.xlsx",
        "task_01/Task1_Sales_Performance_Dashboard.pdf",
        "task_01/dashboard_preview.png",
        "task_01/build_excel.py",
        "task_01/prepare_data.py",
        "task_01/verify_task1.py",
    ],
    "Task_02_Titanic_EDA": [
        "task_02/Titanic_EDA.ipynb",
        "task_02/fig_overview.png",
        "task_02/fig_heatmap_sex_class.png",
        "task_02/fig_correlation.png",
        "task_02/build_notebook.py",
    ],
    "Task_03_RFM_Segmentation": [
        "task_03/RFM_Segmentation.ipynb",
        "task_03/fig_segments.png",
        "task_03/fig_rfm_heatmap.png",
        "task_03/fig_monetary_box.png",
        "task_03/build_notebook.py",
    ],
    "Task_04_Survey_Cleaning_Insights": [
        "task_04/Survey_Cleaning_Insights.ipynb",
        "task_04/fig_top5_insights.png",
        "task_04/fig_gender_trend.png",
        "task_04/build_notebook.py",
    ],
    "Task_05_SQL_Analysis": [
        "task_05/queries.sql",
        "task_05/results.md",
        "task_05/insights.md",
    ],
    "Task_06_Job_Postings": [
        "task_06/Job_Postings_Analysis.ipynb",
        "task_06/jobs_clean.csv",
        "task_06/jobs_raw.json",
        "task_06/fig_roles.png",
        "task_06/fig_skills.png",
        "task_06/fig_skills_by_region.png",
        "task_06/fig_trend.png",
        "task_06/scrape.py",
        "task_06/build_notebook.py",
    ],
    "Task_07_Walmart_Time_Series": [
        "task_07/Walmart_Time_Series.ipynb",
        "task_07/insights.md",
        "task_07/fig_trend.png",
        "task_07/fig_yoy.png",
        "task_07/fig_seasonality.png",
        "task_07/fig_holidays.png",
        "task_07/fig_dept_trend.png",
        "task_07/fig_type.png",
        "task_07/fig_forecast.png",
        "task_07/build_notebook.py",
    ],
    "Task_08_PowerBI": [
        "task_08/Task8_PowerBI_Dashboard.pbix",
        "task_08/Task8_PowerBI_Dashboard.pdf",
        "task_08/dashboard_screenshot.png",
        "task_08/BUILD_GUIDE.md",
        "task_08/measures.dax",
        "task_08/metrics.json",
        "task_08/build_pbix_project.py",
        "task_08/build_model.py",
    ],
    "Task_09_Olist_Executive_Report": [
        "task_09/Olist_Cohort_Analysis.ipynb",
        "task_09/EXECUTIVE_REPORT.md",
        "task_09/olist_star.sqlite",
        "task_09/fig_cohort_heatmap.png",
        "task_09/fig_revenue.png",
        "task_09/fig_clv.png",
        "task_09/fig_delivery_review.png",
        "task_09/build_notebook.py",
    ],
    "Task_10_AB_Test": [
        "task_10/Marketing_AB_Test.ipynb",
        "task_10/fig_conv_rates.png",
        "task_10/fig_lift_ci.png",
        "task_10/fig_rollout.png",
        "task_10/fig_exposure.png",
        "task_10/build_notebook.py",
    ],
}

# whole directories to copy in
DIRS = {
    "Task_08_PowerBI/model": "task_08/model",
    "Task_08_PowerBI/pbip": "task_08/pbip",
}

SKIP_DIR_NAMES = {"__pycache__", ".pbi"}


def main():
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)

    missing = []
    staged = 0
    for folder, files in MANIFEST.items():
        dest = STAGE / folder
        dest.mkdir(parents=True, exist_ok=True)
        for rel in files:
            src = ROOT / rel
            if not src.is_file():
                missing.append(rel)
                continue
            shutil.copy2(src, dest / src.name)
            staged += 1

    for dest_rel, src_rel in DIRS.items():
        src = ROOT / src_rel
        dest = STAGE / dest_rel
        for path in sorted(src.rglob("*")):
            if not path.is_file():
                continue
            if SKIP_DIR_NAMES & set(path.parts):
                continue
            target = dest / path.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            staged += 1

    for old in SUB.glob(STAGE.name + "*.zip"):
        old.unlink()

    print(f"staged files : {staged}")
    print(f"missing      : {missing if missing else 'none'}")
    print(f"folder size  : {sum(p.stat().st_size for p in STAGE.rglob('*') if p.is_file())/1024/1024:.1f} MB")

    for part, folders in PARTS.items():
        zip_path = SUB / f"{STAGE.name}_{part}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for folder in folders:
                for path in sorted((STAGE / folder).rglob("*")):
                    if path.is_file():
                        arc = path.relative_to(STAGE).as_posix()
                        zf.write(path, f"{STAGE.name}/{arc}")
        with zipfile.ZipFile(zip_path) as zf:
            bad = zf.testzip()
            n = len(zf.namelist())
        print(f"{zip_path.name:58s} {zip_path.stat().st_size/1024/1024:5.1f} MB  "
              f"{n:3d} files  {'OK' if bad is None else 'CORRUPT: ' + bad}")


if __name__ == "__main__":
    main()
