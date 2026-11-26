# Task 8 — Power BI dashboard

Built with **Power BI Desktop** (installed at `C:\Program Files\Microsoft Power BI Desktop`).

| File | What it is |
|---|---|
| `Task8_PowerBI_Dashboard.pbix` | **the deliverable** — opens in Power BI Desktop with data already loaded |
| `Task8_PowerBI_Dashboard.pdf` | screenshot of page 1 as rendered by Power BI Desktop |
| `dashboard_screenshot.png` | the same image as PNG |
| `pbip/` | the project source (TMDL model + PBIR report) the `.pbix` was generated from |
| `build_pbix_project.py` | generates `pbip/` — model, measures, all visuals, in code |
| `model/*.csv` | the star-schema tables the model imports |
| `measures.dax` | copy/paste-ready DAX library (documentation of the same measures) |
| `metrics.json` | the KPI values the report must show, for checking |

## The report

**Page 1 — Overview**: dynamic title, six KPI cards (revenue, profit, margin, units, AOV, YoY),
monthly revenue line, revenue by region, top-10 products, revenue by category donut,
customer-segment table, and five slicers (Region, Category, Segment, Year, ShipMode).

**Page 2 — Product detail**: sub-category × year matrix, monthly trend, revenue/margin/units cards,
margin-warning card, and a product table.

**Page 3 — Geography**: map of revenue by state with a profit-margin tooltip, plus a region bar chart.

## The model

```
FactSales[DateKey]     -> DimDate[DateKey]        (many-to-one, single, active)
FactSales[ProductKey]  -> DimProduct[ProductKey]
FactSales[CustomerKey] -> DimCustomer[CustomerKey]
FactSales[GeoKey]      -> DimGeography[GeoKey]

_Measures   24 measures (hidden 1-row table)
TopProducts 10 rows, pre-aggregated product revenue feeding the Top-10 visual
DimDate     marked as the date table (Date column is the key)
```

## Verified values (page 1, unfiltered)

| KPI | report | `metrics.json` |
|---|---|---|
| Total revenue | $2,297,200.65 | 2,297,200.65 |
| Total profit | $286,396.54 | 286,396.54 |
| Profit margin | 12.5% | 0.1247 |
| Units sold | 37,873 | 37,873 |
| Average order value | $458.61 | 458.61 |
| YoY growth (2017 vs 2016) | +20.4% | 0.2036 |

`YoY Growth Last Year` deliberately compares the last full year in the data (2017) with the year
before it. The plain `YoY Growth` measure shifts the whole selected range back one year, so at the
total level (2014–2017) it returns a range artefact (~+47%), not a year-over-year comparison — use it
inside visuals that have a single year in context.

## Rebuilding

```bash
cd untitled-project/task_08
python build_pbix_project.py     # writes pbip/SuperstoreInsights.pbip (+ TopProducts.csv)
```

Open `pbip/SuperstoreInsights.pbip` in Power BI Desktop → **Refresh** → **File → Save as → Power BI
files (*.pbix)** to regenerate the `.pbix`.

## Notes and limits

- The partitions read the CSVs from an **absolute path** on this machine. If the folder moves, update
  the path in Power Query (Transform data → Source) or re-run the generator.
- Data is imported (not DirectQuery), so the `.pbix` opens with its numbers already cached.
- Map visuals need **File → Options → Security → Map and filled map visuals** enabled.
- The `pbip/` source can also be version-controlled directly; the `.pbix` is a build artefact of it.
