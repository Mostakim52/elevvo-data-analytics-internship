"""Task 8 - Power BI dashboard for retail insights.

Power BI Desktop is not installed on this machine, so the deliverable is the
complete model plus a faithful layout preview:

  model/*.csv        star schema ready for Power BI (fact + 4 dimensions)
  measures.dax       every measure the report needs
  BUILD_GUIDE.md     click-by-click build steps for Power BI Desktop
  dashboard.html     layout preview of the report pages
  Task8_PowerBI_Dashboard.pdf   rendered preview (via headless Edge)

The preview is generated from the same aggregates the DAX measures return,
so the numbers match what the PBIX will show.
"""
import datetime as dt
import json
from pathlib import Path

import pandas as pd

BASE = Path(r"H:\Repos\elevvo-internship-data-analytics\untitled-project")
SRC = BASE / "task_01" / "data" / "superstore_clean.csv"
OUT = BASE / "task_08"
MODEL = OUT / "model"
MODEL.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(SRC, encoding="utf-8-sig", parse_dates=["Order Date", "Ship Date"])
print(f"source rows: {len(df):,}")

# ---------------------------------------------------------------- star schema
dim_date = pd.DataFrame({"Date": pd.date_range(df["Order Date"].min(), df["Order Date"].max(), freq="D")})
dim_date["DateKey"] = dim_date.Date.dt.strftime("%Y%m%d").astype(int)
dim_date["Year"] = dim_date.Date.dt.year
dim_date["Quarter"] = "Q" + dim_date.Date.dt.quarter.astype(str)
dim_date["Month"] = dim_date.Date.dt.month
dim_date["MonthName"] = dim_date.Date.dt.strftime("%b")
dim_date["YearMonth"] = dim_date.Date.dt.strftime("%Y-%m")
dim_date["Weekday"] = dim_date.Date.dt.strftime("%a")
dim_date = dim_date[["DateKey", "Date", "Year", "Quarter", "Month", "MonthName", "YearMonth", "Weekday"]]

dim_product = (df[["Product ID", "Category", "Sub-Category", "Product Name"]]
               .drop_duplicates("Product ID")
               .rename(columns={"Product ID": "ProductKey", "Product Name": "ProductName",
                                "Sub-Category": "SubCategory"})
               .sort_values("ProductKey").reset_index(drop=True))

dim_customer = (df[["Customer ID", "Customer Name", "Segment"]]
                .drop_duplicates("Customer ID")
                .rename(columns={"Customer ID": "CustomerKey", "Customer Name": "CustomerName"})
                .sort_values("CustomerKey").reset_index(drop=True))

dim_geography = (df[["Country", "Region", "State", "City", "Postal Code"]]
                 .drop_duplicates(["City", "State"])
                 .rename(columns={"Postal Code": "PostalCode"})
                 .reset_index(drop=True))
dim_geography.insert(0, "GeoKey", range(1, len(dim_geography) + 1))

geo_lookup = dim_geography.set_index(["City", "State"]).GeoKey

fact = df.assign(
    DateKey=df["Order Date"].dt.strftime("%Y%m%d").astype(int),
    GeoKey=[geo_lookup.loc[(c, s)] for c, s in zip(df.City, df.State)],
).rename(columns={
    "Order ID": "OrderID", "Product ID": "ProductKey", "Customer ID": "CustomerKey",
    "Ship Mode": "ShipMode", "Ship Days": "ShipDays", "Discount": "Discount",
})
fact = fact[["OrderID", "DateKey", "ProductKey", "CustomerKey", "GeoKey", "ShipMode",
             "Sales", "Quantity", "Discount", "Profit", "ShipDays"]]

for name, frame in [("DimDate", dim_date), ("DimProduct", dim_product), ("DimCustomer", dim_customer),
                    ("DimGeography", dim_geography), ("FactSales", fact)]:
    path = MODEL / f"{name}.csv"
    frame.to_csv(path, index=False)
    print(f"  {name:14s} {len(frame):>6,} rows -> {path.name}")

# ---------------------------------------------------------------- aggregates
total_rev = df.Sales.sum()
total_profit = df.Profit.sum()
units = int(df.Quantity.sum())
orders = df["Order ID"].nunique()
margin = total_profit / total_rev
aov = total_rev / orders

monthly = (df.groupby(df["Order Date"].dt.to_period("M"))
             .Sales.sum().reset_index(name="Sales"))
monthly["label"] = monthly["Order Date"].dt.strftime("%b %y")

by_region = df.groupby("Region").Sales.sum().sort_values(ascending=False)
by_category = df.groupby("Category").Sales.sum().sort_values(ascending=False)
top_products = df.groupby("Product Name").Sales.sum().nlargest(10)
by_segment = df.groupby("Segment").agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
yoy = df.groupby("Order Year").Sales.sum()
last_two = yoy.index[-2:].tolist()

metrics = {
    "revenue": round(total_rev, 2), "profit": round(total_profit, 2), "units": units,
    "orders": orders, "margin": round(margin, 4), "aov": round(aov, 2),
    "yoy": round(yoy.loc[last_two[1]] / yoy.loc[last_two[0]] - 1, 4),
}
(OUT / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

# ---------------------------------------------------------------- SVG helpers
W, H, PAD = 760, 210, 34


def line_chart(values, labels):
    lo, hi = min(values), max(values)
    span = hi - lo or 1
    n = len(values)
    pts = []
    for i, v in enumerate(values):
        x = PAD + i * (W - 2 * PAD) / (n - 1)
        y = H - PAD - (v - lo) / span * (H - 2 * PAD)
        pts.append((x, y))
    path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts))
    area = path + f" L{pts[-1][0]:.1f},{H - PAD} L{pts[0][0]:.1f},{H - PAD} Z"
    grid = "".join(
        f'<line x1="{PAD}" y1="{H - PAD - t * (H - 2 * PAD) / 4:.0f}" '
        f'x2="{W - PAD}" y2="{H - PAD - t * (H - 2 * PAD) / 4:.0f}" stroke="#e8edf3"/>'
        f'<text x="4" y="{H - PAD - t * (H - 2 * PAD) / 4 + 4:.0f}" font-size="9" fill="#8a94a6">'
        f'{lo + t * span / 4:,.0f}</text>'
        for t in range(5)
    )
    ticks = "".join(
        f'<text x="{PAD + i * (W - 2 * PAD) / (n - 1):.0f}" y="{H - PAD + 14}" font-size="8.5" '
        f'fill="#8a94a6" text-anchor="middle">{lab}</text>'
        for i, lab in enumerate(labels) if i % 6 == 0
    )
    return (f'<svg viewBox="0 0 {W} {H}" class="chart">{grid}'
            f'<path d="{area}" fill="url(#grad)" opacity="0.55"/>'
            f'<path d="{path}" fill="none" stroke="#1f3864" stroke-width="2.2"/>'
            f'<defs><linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0%" stop-color="#2c7fb8" stop-opacity="0.45"/>'
            f'<stop offset="100%" stop-color="#2c7fb8" stop-opacity="0"/>'
            f'</linearGradient></defs>{ticks}</svg>')


def bar_rows(series, money=True, color="#2c7fb8"):
    top = series.max() or 1
    rows = []
    for label, value in series.items():
        width = value / top * 100
        shown = f"${value:,.0f}" if money else f"{value:,.0f}"
        rows.append(
            f'<div class="bar-row"><div class="bar-label" title="{label}">{label}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{width:.1f}%;'
            f'background:{color}"></div></div>'
            f'<div class="bar-value">{shown}</div></div>'
        )
    return "".join(rows)


kpi = lambda label, value, sub, accent: (
    f'<div class="kpi"><div class="kpi-label">{label}</div>'
    f'<div class="kpi-value" style="color:{accent}">{value}</div>'
    f'<div class="kpi-sub">{sub}</div></div>'
)

html = f"""<!doctype html>
<html><head><meta charset="utf-8">
<title>Superstore — Power BI report preview</title>
<style>
  @page {{ size: 1600px 900px; margin: 0; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font-family: 'Segoe UI', Arial, sans-serif; background:#eef1f5; color:#1b2430; width:1600px; }}
  .frame {{ width:1600px; padding:0 0 14px; }}
  header {{ background:#1f3864; color:#fff; padding:16px 26px 14px; display:flex; justify-content:space-between; align-items:flex-end; }}
  header h1 {{ margin:0; font-size:22px; letter-spacing:.4px; }}
  header .sub {{ font-size:11.5px; opacity:.8; margin-top:3px; }}
  .badge {{ font-size:10.5px; background:#2c7fb8; padding:5px 10px; border-radius:3px; letter-spacing:.3px; }}
  .slicers {{ display:flex; gap:8px; padding:10px 26px 0; }}
  .slicer {{ background:#fff; border:1px solid #d3dae4; border-radius:3px; padding:6px 10px; font-size:11px; min-width:150px; display:flex; justify-content:space-between; box-shadow:0 1px 2px rgba(16,24,40,.05); }}
  .slicer span.v {{ color:#2c7fb8; font-weight:600; }}
  .slicer small {{ display:block; color:#8a94a6; font-size:9px; text-transform:uppercase; letter-spacing:.5px; }}
  .kpis {{ display:grid; grid-template-columns:repeat(6,1fr); gap:10px; padding:12px 26px 0; }}
  .kpi {{ background:#fff; border:1px solid #e2e8f0; border-radius:4px; padding:10px 12px; }}
  .kpi-label {{ font-size:9.5px; text-transform:uppercase; letter-spacing:.6px; color:#8a94a6; }}
  .kpi-value {{ font-size:20px; font-weight:700; margin-top:3px; }}
  .kpi-sub {{ font-size:10px; color:#667085; margin-top:2px; }}
  .grid {{ display:grid; grid-template-columns: 760px 1fr; gap:10px; padding:10px 26px 0; }}
  .card {{ background:#fff; border:1px solid #e2e8f0; border-radius:4px; padding:12px 14px 10px; }}
  .card h3 {{ margin:0 0 8px; font-size:11px; text-transform:uppercase; letter-spacing:.6px; color:#475467; font-weight:600; }}
  .chart {{ width:100%; height:auto; display:block; }}
  .bar-row {{ display:grid; grid-template-columns:150px 1fr 72px; align-items:center; gap:8px; margin-bottom:5px; }}
  .bar-label {{ font-size:10.5px; color:#344054; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .bar-track {{ background:#f0f3f8; height:11px; border-radius:2px; overflow:hidden; }}
  .bar-fill {{ height:100%; border-radius:2px; }}
  .bar-value {{ font-size:10px; color:#475467; text-align:right; }}
  .stack {{ display:grid; gap:10px; }}
  .seg-table {{ width:100%; border-collapse:collapse; font-size:11px; }}
  .seg-table th {{ text-align:left; color:#8a94a6; font-weight:600; font-size:9.5px; text-transform:uppercase; letter-spacing:.5px; border-bottom:1px solid #e6ebf2; padding:4px 3px; }}
  .seg-table td {{ padding:5px 3px; border-bottom:1px solid #f1f4f8; }}
  .seg-table td.n {{ text-align:right; font-variant-numeric:tabular-nums; }}
  footer {{ padding:10px 26px 0; font-size:10px; color:#98a2b3; }}
</style></head>
<body><div class="frame">
  <header>
    <div>
      <h1>SUPERSTORE RETAIL INSIGHTS</h1>
      <div class="sub">Jan 2014 – Dec 2017 &nbsp;|&nbsp; {len(df):,} order lines &nbsp;|&nbsp; {orders:,} orders &nbsp;|&nbsp; 4 US regions</div>
    </div>
    <div class="badge">POWER BI REPORT — PAGE 1 OF 3 · LAYOUT PREVIEW</div>
  </header>

  <div class="slicers">
    <div class="slicer"><div><small>Region</small><span class="v">All</span></div><div>▾</div></div>
    <div class="slicer"><div><small>Category</small><span class="v">All</span></div><div>▾</div></div>
    <div class="slicer"><div><small>Segment</small><span class="v">All</span></div><div>▾</div></div>
    <div class="slicer"><div><small>Year</small><span class="v">2014 – 2017</span></div><div>▾</div></div>
    <div class="slicer"><div><small>Ship Mode</small><span class="v">All</span></div><div>▾</div></div>
  </div>

  <div class="kpis">
    {kpi("Total revenue", f"${total_rev/1e6:.2f}M", f"{orders:,} orders", "#1f3864")}
    {kpi("Total profit", f"${total_profit/1e3:,.0f}K", "net of discount", "#2e7d32")}
    {kpi("Profit margin", f"{margin:.1%}", "profit ÷ revenue", "#2e7d32")}
    {kpi("Units sold", f"{units:,}", "order lines", "#1f3864")}
    {kpi("Avg order value", f"${aov:,.0f}", "revenue ÷ orders", "#1f3864")}
    {kpi("YoY growth", f"{metrics['yoy']:+.1%}", f"{last_two[1]} vs {last_two[0]}", "#c0392b")}
  </div>

  <div class="grid">
    <div class="card">
      <h3>Monthly revenue trend</h3>
      {line_chart(list(monthly.Sales), list(monthly.label))}
    </div>
    <div class="stack">
      <div class="card">
        <h3>Revenue by region</h3>
        {bar_rows(by_region, color="#2c7fb8")}
      </div>
      <div class="card">
        <h3>Customer segment</h3>
        <table class="seg-table">
          <tr><th>Segment</th><th style="text-align:right">Revenue</th><th style="text-align:right">Profit</th><th style="text-align:right">Margin</th></tr>
          {''.join(f'<tr><td>{seg}</td><td class="n">${r.Sales:,.0f}</td><td class="n">${r.Profit:,.0f}</td><td class="n">{r.Profit/r.Sales:.1%}</td></tr>' for seg, r in by_segment.iterrows())}
        </table>
      </div>
    </div>
  </div>

  <div class="grid">
    <div class="card">
      <h3>Top 10 products by revenue</h3>
      {bar_rows(top_products, color="#1f3864")}
    </div>
    <div class="stack">
      <div class="card">
        <h3>Revenue by category</h3>
        {bar_rows(by_category, color="#2c7fb8")}
      </div>
      <div class="card">
        <h3>Notes for the Power BI build</h3>
        <div style="font-size:10.5px; color:#475467; line-height:1.55">
          Model: <b>FactSales</b> joined to <b>DimDate</b>, <b>DimProduct</b>, <b>DimCustomer</b> and
          <b>DimGeography</b> (star schema, one-to-many, single-direction filters).<br>
          Slicers above are driven by DimDate[Year], DimProduct[Category], DimCustomer[Segment],
          DimGeography[Region] and FactSales[ShipMode].<br>
          Page 2 = product drill-through, page 3 = geography map. All measures are in <b>measures.dax</b>.
        </div>
      </div>
    </div>
  </div>

  <footer>Preview rendered from the same aggregates as the DAX measures. Open <b>BUILD_GUIDE.md</b> to reproduce this report in Power BI Desktop and publish it to the web.</footer>
</div></body></html>
"""

(OUT / "dashboard.html").write_text(html, encoding="utf-8")
print(f"wrote {OUT/'dashboard.html'}")
print(f"metrics: {metrics}")
