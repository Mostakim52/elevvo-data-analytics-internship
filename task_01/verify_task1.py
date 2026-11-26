"""Verify the Task 1 workbook against the source data."""
import traceback
from pathlib import Path

import pandas as pd
from win32com.client import gencache

BASE = Path(r"H:\Repos\elevvo-internship-data-analytics\untitled-project\task_01")
XLSX = BASE / "Task1_Sales_Performance_Dashboard.xlsx"
PDF = BASE / "Task1_Sales_Performance_Dashboard.pdf"
df = pd.read_csv(BASE / "data" / "superstore_clean.csv", encoding="utf-8-sig")

print(f"source: rows={len(df):,} revenue={df['Sales'].sum():,.2f} "
      f"units={df['Quantity'].sum():,} profit={df['Profit'].sum():,.2f} "
      f"margin={(df['Profit'].sum()/df['Sales'].sum()):.4f}")
print(f"pdf exists: {PDF.exists()} ({PDF.stat().st_size/1024:.0f} KB)")

excel = None
try:
    excel = gencache.EnsureDispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    wb = excel.Workbooks.Open(str(XLSX), ReadOnly=True)
    print("sheets:", [wb.Worksheets(i).Name for i in range(1, wb.Worksheets.Count + 1)])

    data = wb.Worksheets("Data")
    print("data used range:", data.UsedRange.Address,
          "| tables:", [data.ListObjects(i).Name for i in range(1, data.ListObjects.Count + 1)])

    dash = wb.Worksheets("Dashboard")
    print("\nKPI cards:")
    for cell, label in [("A6", "revenue"), ("C6", "units"), ("A9", "profit"), ("C9", "margin")]:
        print(f"  {label:8s} {dash.Range(cell).Value}")
    print("growth block:")
    for r in range(13, 19):
        print(f"  {dash.Cells(r, 1).Value} = {dash.Cells(r, 2).Value}")
    print("charts on dashboard:", dash.ChartObjects().Count,
          "| shapes:", dash.Shapes.Count)
    print("notes:")
    for r in range(25, 30):
        v = dash.Cells(r, 1).Value
        if v:
            print("  ", v[:110])

    pv = wb.Worksheets("Pivots")
    print("\npivot tables:")
    for i in range(1, pv.PivotTables().Count + 1):
        pt = pv.PivotTables(i)
        vals = pt.TableRange1.Value
        total = None
        for row in reversed(vals):
            if row and isinstance(row[-1], float):
                total = row[-1]
                break
        print(f"  {pt.Name:16s} {pt.TableRange1.Address:14s} rows={len(vals):3d} "
              f"total={total}")

    print("\nslicer caches:")
    for i in range(1, wb.SlicerCaches.Count + 1):
        sc = wb.SlicerCaches(i)
        print(f"  {sc.Name}: slicers={sc.Slicers.Count} "
              f"pivots={[sc.PivotTables(j).Name for j in range(1, sc.PivotTables.Count + 1)]}")
    wb.Close(SaveChanges=False)
except Exception:
    traceback.print_exc()
finally:
    try:
        excel.Quit()
    except Exception:
        pass
