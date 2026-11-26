"""Task 1 - Sales Performance Dashboard (Superstore).

Builds the workbook natively in Excel through COM automation:
  Data      cleaned table with formatting, number formats, frozen header
  Pivots    4 native pivot tables (monthly trend, category, region x segment, top products)
  Dashboard KPI formulas, YoY / MoM growth, 4 charts, 2 slicers, insight notes
Exports the dashboard to PDF.

NOTE: Range.Resize() is unreliable through this COM binding (it returns a
single mis-placed cell), so every range is built with explicit A1 addresses.
"""
import datetime as dt
import string
import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
from win32com.client import gencache

BASE = Path(r"H:\Repos\elevvo-internship-data-analytics\untitled-project\task_01")
CSV = BASE / "data" / "superstore_clean.csv"
XLSX = BASE / "Task1_Sales_Performance_Dashboard.xlsx"
PDF = BASE / "Task1_Sales_Performance_Dashboard.pdf"

xlSrcRange = 1
xlYes = 1
xlRowField = 1
xlColumnField = 2
xlSum = -4157
xlDatabase = 1
xlDescending = 2
xlLine = 4
xlColumnClustered = 51
xlBarClustered = 57
xlTypePDF = 0
xlFileFormatXlsx = 51
xlLandscape = 2


def log(msg):
    print(msg, flush=True)


def col_letter(idx):
    """1 -> A, 28 -> AB."""
    s = ""
    while idx:
        idx, rem = divmod(idx - 1, 26)
        s = string.ascii_uppercase[rem] + s
    return s


def main():
    df = pd.read_csv(CSV, encoding="utf-8-sig", parse_dates=["Order Date", "Ship Date"])
    # helper flag: marks the 10 highest-revenue products so the top-products
    # pivot can filter on it without hiding ~1,850 individual pivot items
    top10_products = set(df.groupby("Product Name")["Sales"].sum().nlargest(10).index)
    df["Top Product"] = np.where(df["Product Name"].isin(top10_products), "Yes", "No")
    n, ncols = df.shape
    last = n + 1
    last_col = col_letter(ncols)
    header = list(df.columns)
    log(f"loaded {n} rows x {ncols} cols")

    def cell(v):
        if isinstance(v, (pd.Timestamp, dt.datetime, dt.date)):
            return dt.datetime(v.year, v.month, v.day)
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        if isinstance(v, np.integer):
            return int(v)
        if isinstance(v, np.floating):
            return float(v)
        return v

    values = [[cell(v) for v in row] for row in df.itertuples(index=False, name=None)]

    years = sorted(df["Order Year"].unique().tolist())
    cur_year, prev_year = years[-1], years[-2]
    months = sorted(df["YearMonth"].unique().tolist())
    cur_month, prev_month = months[-1], months[-2]

    excel = gencache.EnsureDispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    excel.ScreenUpdating = False
    log("excel started")

    wb = excel.Workbooks.Add()
    try:
        excel.Calculation = -4105  # xlCalculationAutomatic
    except Exception as exc:  # noqa: BLE001
        log(f"calculation setting skipped: {exc}")
    ws = wb.Worksheets(1)
    ws.Name = "Data"

    # ---------------- Data sheet ------------------------------------------
    ws.Range(f"A1:{last_col}1").Value = [header]
    ws.Range(f"A2:{last_col}{last}").Value = values
    log(f"data written ({n} x {ncols})")
    assert ws.Range(f"A2:{last_col}{last}").Rows.Count == n, "bulk write did not land"

    data_rng = ws.Range(f"A1:{last_col}{last}")

    hdr = ws.Range(f"A1:{last_col}1")
    hdr.Interior.Color = 0x64311F          # dark navy (BGR)
    hdr.Font.Color = 0xFFFFFF
    hdr.Font.Bold = True
    hdr.Font.Size = 10
    hdr.VerticalAlignment = -4108
    hdr.WrapText = True
    hdr.RowHeight = 30

    tbl = ws.ListObjects.Add(xlSrcRange, data_rng, None, xlYes)
    tbl.Name = "tblSales"
    tbl.TableStyle = "TableStyleMedium2"
    log("table created")

    widths = {
        "Row ID": 7, "Order ID": 18, "Order Date": 12, "Ship Date": 12, "Ship Mode": 13,
        "Customer ID": 13, "Customer Name": 18, "Segment": 11, "Country": 13, "City": 12,
        "State": 13, "Postal Code": 9, "Region": 8, "Product ID": 18, "Category": 14,
        "Sub-Category": 15, "Product Name": 42, "Sales": 11, "Quantity": 9, "Discount": 9,
        "Profit": 11, "Order Year": 9, "Order Month": 9, "Month Name": 8, "YearMonth": 10,
        "Quarter": 8, "Ship Days": 8, "Profit Margin": 10, "Top Product": 11,
    }
    col_index = {name: i + 1 for i, name in enumerate(header)}
    for name, w in widths.items():
        ws.Columns(col_index[name]).ColumnWidth = w

    def col_range(name):
        ci = col_index[name]
        L = col_letter(ci)
        return ws.Range(f"{L}2:{L}{last}")

    for c in ("Sales", "Profit"):
        col_range(c).NumberFormat = "#,##0.00"
    col_range("Discount").NumberFormat = "0%"
    col_range("Profit Margin").NumberFormat = "0.0%"
    for c in ("Order Date", "Ship Date"):
        col_range(c).NumberFormat = "yyyy-mm-dd"
    col_range("Postal Code").NumberFormat = "@"

    ws.Activate()
    excel.ActiveWindow.SplitRow = 1
    excel.ActiveWindow.FreezePanes = True
    ws.Range("A1").Select()
    log("data formatted")

    # ---------------- Pivots sheet ----------------------------------------
    pv = wb.Worksheets.Add(After=wb.Worksheets(wb.Worksheets.Count))
    pv.Name = "Pivots"
    pv.Range("A1").Value = "Pivot summary tables (source: tblSales on the Data sheet)"
    pv.Range("A1").Font.Bold = True
    pv.Range("A1").Font.Size = 12

    cache = wb.PivotCaches().Create(SourceType=xlDatabase, SourceData=data_rng)
    log(f"pivot cache created (records={cache.RecordCount})")

    def make_pivot(dest_addr, name, rows, data_fields, cols=None, title=None,
                   title_addr=None, page_fields=None):
        dest = pv.Range(dest_addr)
        cache.CreatePivotTable(TableDestination=dest, TableName=name)
        pt = pv.PivotTables(name)
        for i, r in enumerate(rows, start=1):
            pf = pt.PivotFields(r)
            pf.Orientation = xlRowField
            pf.Position = i
        for field, value in (page_fields or []):
            pf = pt.PivotFields(field)
            pf.Orientation = 3  # xlPageField
            pf.CurrentPage = value
        if cols:
            for i, c in enumerate(cols, start=1):
                pf = pt.PivotFields(c)
                pf.Orientation = xlColumnField
                pf.Position = i
        for field_name, caption in data_fields:
            pt.AddDataField(pt.PivotFields(field_name), caption, xlSum)
        try:
            pt.RowAxisLayout(1)  # tabular layout; needs at least one row field
        except Exception:  # noqa: BLE001
            pass
        if title and title_addr:
            tcell = pv.Range(title_addr)
            tcell.Value = title
            tcell.Font.Bold = True
            tcell.Font.Size = 11
        pt.Update()
        log(f"  {name}: {pt.TableRange1.Address} rows={pt.RowFields.Count} cols={pt.ColumnFields.Count}")
        return pt

    pt_month = make_pivot("B3", "PT_Monthly",
                          rows=["YearMonth"],
                          data_fields=[("Sales", "Sum of Sales"), ("Profit", "Sum of Profit")],
                          title="1. Monthly revenue & profit trend", title_addr="B1")

    pt_cat = make_pivot("I3", "PT_Category",
                        rows=["Sub-Category"],
                        data_fields=[("Sales", "Sum of Sales")],
                        title="2. Revenue by sub-category", title_addr="I1")

    # headline measures as a pivot with no row field (revenue, units, profit)
    pt_summary = make_pivot("P24", "PT_Summary",
                            rows=[],
                            data_fields=[("Sales", "Sum of Sales"),
                                         ("Quantity", "Units Sold"),
                                         ("Profit", "Sum of Profit")],
                            title="5. Headline measures", title_addr="P22")
    try:  # rank sub-categories so the bar chart reads top-down
        pt_cat.PivotFields("Sub-Category").AutoSort(xlDescending, "Sum of Sales")
        pt_cat.Update()
    except Exception as exc:  # noqa: BLE001
        log(f"  sub-category sort skipped: {exc}")

    pt_region = make_pivot("P3", "PT_Region",
                           rows=["Region"],
                           cols=["Segment"],
                           data_fields=[("Sales", "Sum of Sales")],
                           title="3. Revenue by region and customer segment", title_addr="P1")

    pt_top = make_pivot("B56", "PT_TopProducts",
                        rows=["Product Name"],
                        data_fields=[("Sales", "Sum of Sales")],
                        title="4. Top 10 products by revenue", title_addr="B54",
                        page_fields=[("Top Product", "Yes")])
    try:
        pf = pt_top.PivotFields("Product Name")
        pf.AutoSort(xlDescending, "Sum of Sales")
        pt_top.Update()
        log(f"  PT_TopProducts rows={pt_top.TableRange1.Address} "
            f"items={pf.PivotItems().Count}")
    except Exception as exc:  # noqa: BLE001
        log(f"  top-products sort skipped: {exc}")

    pv.Columns("A:Z").ColumnWidth = 14

    # ---------------- Dashboard ------------------------------------------
    dash = wb.Worksheets.Add(Before=wb.Worksheets(1))
    dash.Name = "Dashboard"
    dash.Cells.Font.Name = "Calibri"
    dash.Cells.Font.Size = 11

    title = dash.Range("A1:D2")
    title.Merge()
    title.Value = "SUPERSTORE SALES PERFORMANCE DASHBOARD"
    title.Font.Size = 20
    title.Font.Bold = True
    title.Font.Color = 0xFFFFFF
    title.Interior.Color = 0x64311F
    title.VerticalAlignment = -4108
    title.HorizontalAlignment = -4131

    sub = dash.Range("A3:D3")
    sub.Merge()
    sub.Value = (f"{df['Order Date'].min():%b %Y} – {df['Order Date'].max():%b %Y}"
                 f"   |   {n:,} order lines   |   {df['Order ID'].nunique():,} orders")
    sub.Font.Size = 10
    sub.Font.Italic = True
    sub.Font.Color = 0x606060
    sub.HorizontalAlignment = -4131

    # set column widths before placing shapes: resizing afterwards rescales charts
    dash.Columns("A").ColumnWidth = 40
    for ci in range(2, 22):
        dash.Columns(ci).ColumnWidth = 12

    S = f"Data!$R$2:$R${last}"
    Q = f"Data!$S$2:$S${last}"
    P = f"Data!$U$2:$U${last}"
    YR = f"Data!$V$2:$V${last}"
    YM = f"Data!$Y$2:$Y${last}"

    def card(label_cell, label, value_cell, formula, fmt, colour, size=15):
        dash.Range(label_cell).Value = label
        dash.Range(label_cell).Font.Size = 9
        dash.Range(label_cell).Font.Bold = True
        dash.Range(label_cell).Font.Color = 0x707070
        dash.Range(value_cell).Formula = formula
        dash.Range(value_cell).NumberFormat = fmt
        dash.Range(value_cell).Font.Size = size
        dash.Range(value_cell).Font.Bold = True
        dash.Range(value_cell).Font.Color = colour

    dash.Range("A5:D10").Interior.Color = 0xF4F4F4
    card("A5", "TOTAL REVENUE", "A6", f"=SUM({S})", '#,##0', 0x1F3864)
    card("C5", "UNITS SOLD", "C6", f"=SUM({Q})", '#,##0', 0x1F3864)
    card("A8", "TOTAL PROFIT", "A9", f"=SUM({P})", '#,##0', 0x2E7D32)
    card("C8", "PROFIT MARGIN", "C9", "=IF(A6=0,0,A9/A6)", '0.0%', 0x2E7D32)

    dash.Range("A12").Value = "GROWTH — BONUS (YoY / MoM)"
    dash.Range("A12").Font.Bold = True
    dash.Range("A12").Font.Size = 10
    dash.Range("A12").Font.Color = 0x64311F

    growth = [
        (13, f"Revenue {cur_year}", f"=SUMIFS({S},{YR},{cur_year})", '#,##0'),
        (14, f"Revenue {prev_year}", f"=SUMIFS({S},{YR},{prev_year})", '#,##0'),
        (15, f"YoY growth ({prev_year} → {cur_year})", "=IF(B14=0,0,(B13-B14)/B14)", '0.0%'),
        (16, f"Revenue {cur_month}", f'=SUMIFS({S},{YM},"{cur_month}")', '#,##0'),
        (17, f"Revenue {prev_month}", f'=SUMIFS({S},{YM},"{prev_month}")', '#,##0'),
        (18, f"MoM growth ({prev_month} → {cur_month})", "=IF(B17=0,0,(B16-B17)/B17)", '0.0%'),
    ]
    for r, label, formula, fmt in growth:
        dash.Cells(r, 1).Value = label
        dash.Cells(r, 1).Font.Size = 9
        dash.Cells(r, 1).Font.Color = 0x505050
        dash.Cells(r, 2).Formula = formula
        dash.Cells(r, 2).NumberFormat = fmt
        dash.Cells(r, 2).Font.Size = 10
        dash.Cells(r, 2).Font.Bold = True

    # ---- charts ---------------------------------------------------------
    def add_chart(chart_type, source, left, top, width, height, title_text, legend=None):
        shape = dash.Shapes.AddChart2(-1, chart_type, left, top, width, height)
        chart = shape.Chart
        chart.SetSourceData(Source=source)
        chart.HasTitle = True
        chart.ChartTitle.Text = title_text
        chart.ChartTitle.Font.Size = 11
        chart.ChartTitle.Font.Bold = True
        chart.HasLegend = (chart_type != xlLine) if legend is None else legend
        for attr in ("ShowAllFieldButtons", "ShowValueFieldButtons", "ShowAxisFieldButtons",
                     "ShowLegendFieldButtons", "ShowReportFilterFieldButtons"):
            try:
                setattr(chart, attr, False)
            except Exception:  # noqa: BLE001
                pass
        return chart

    # four charts stacked in one column so everything fits a single printed page
    c1 = add_chart(xlLine, pt_month.TableRange1, 430, 5, 380, 128, "Monthly revenue & profit")
    c2 = add_chart(xlBarClustered, pt_cat.TableRange1, 430, 138, 380, 212,
                   "Revenue by sub-category", legend=False)
    c3 = add_chart(xlColumnClustered, pt_region.TableRange1, 430, 355, 380, 96,
                   "Revenue by region and segment")
    c4 = add_chart(xlBarClustered, pt_top.TableRange1, 430, 456, 380, 144,
                   "Top 10 products by revenue", legend=False)
    for chart in (c1, c2, c3, c4):
        try:
            chart.Axes(1).TickLabels.Font.Size = 7
            chart.Axes(2).TickLabels.Font.Size = 6
            chart.Axes(2).TickLabels.NumberFormat = '#,##0,"k"'
        except Exception:  # noqa: BLE001
            pass
    log(f"charts added: {dash.ChartObjects().Count}")

    # ---- slicers (shared cache across all four pivots) -------------------
    slicers = []
    for i, (field, caption) in enumerate([("Region", "Region"), ("Category", "Category")]):
        try:
            sc = wb.SlicerCaches.Add2(pt_month, field, f"{caption}Cache")
            # named arguments are required here: positional args fail on this build
            sc.Slicers.Add(SlicerDestination=dash, Name=f"{caption}Slicer", Caption=caption,
                           Top=390, Left=20 + i * 190, Width=170, Height=170)
            for other in (pt_cat, pt_region, pt_top, pt_summary):
                try:
                    sc.PivotTables.AddPivotTable(other)
                except Exception as exc:  # noqa: BLE001
                    log(f"  connect {other.Name} to {caption}: {exc}")
            slicers.append(f"{caption}: {sc.Slicers.Count} slicer, {sc.PivotTables.Count} pivots")
        except Exception as exc:  # noqa: BLE001
            log(f"slicer {caption} failed: {exc}")
    log(f"slicers: {slicers}")

    # ---- insight notes (computed from the data, not typed by hand) -------
    rev_total = df["Sales"].sum()
    by_cat = df.groupby("Category")["Sales"].sum()
    by_sub = df.groupby("Sub-Category")["Sales"].sum()
    by_region = df.groupby("Region")["Sales"].sum()
    loss_subs = df.groupby("Sub-Category")["Profit"].sum()
    loss_subs = loss_subs[loss_subs < 0].sort_values().index.tolist()
    top10_share = df.groupby("Product Name")["Sales"].sum().nlargest(10).sum() / rev_total

    notes = [
        "KEY INSIGHTS",
        f"• {by_cat.idxmax()} leads category revenue at {by_cat.max()/rev_total:.1%}; "
        f"{by_sub.idxmax()} is the top sub-category.",
        f"• {by_region.idxmax()} is the strongest region "
        f"({by_region.max()/rev_total:.1%} of sales); {by_region.idxmin()} is the weakest.",
        f"• Top 10 products generate {top10_share:.1%} of total revenue.",
        f"• Discounting hurts: {', '.join(loss_subs)} have negative total profit.",
        "• Region and Category slicers filter every pivot table on the Pivots sheet.",
    ]
    for i, text in enumerate(notes):
        c = dash.Cells(20 + i, 1)
        c.Value = text
        c.Font.Size = 9 if i else 10
        c.Font.Bold = i == 0
        if i == 0:
            c.Font.Color = 0x64311F

    # ---- print setup + save ---------------------------------------------
    dash.Activate()
    excel.ActiveWindow.DisplayGridlines = False
    dash.PageSetup.Orientation = xlLandscape
    dash.PageSetup.Zoom = False
    dash.PageSetup.FitToPagesWide = 1
    dash.PageSetup.FitToPagesTall = 1
    dash.PageSetup.PrintArea = "A1:J40"
    dash.PageSetup.LeftMargin = 18
    dash.PageSetup.RightMargin = 18
    dash.PageSetup.TopMargin = 18
    dash.PageSetup.BottomMargin = 18
    dash.Range("A1").Select()

    pv.Activate()
    excel.ActiveWindow.DisplayGridlines = False
    ws.Activate()
    excel.ActiveWindow.DisplayGridlines = True
    ws.Range("A1").Select()
    dash.Activate()

    if XLSX.exists():
        XLSX.unlink()
    wb.SaveAs(str(XLSX), FileFormat=xlFileFormatXlsx)
    log(f"saved {XLSX.name}")

    if PDF.exists():
        PDF.unlink()
    dash.ExportAsFixedFormat(xlTypePDF, str(PDF))
    log(f"exported {PDF.name} ({PDF.stat().st_size/1024:.0f} KB)")

    wb.Close(SaveChanges=False)
    excel.Quit()
    log("done")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        try:
            gencache.EnsureDispatch("Excel.Application").Quit()
        except Exception:  # noqa: BLE001
            pass
        sys.exit(1)
