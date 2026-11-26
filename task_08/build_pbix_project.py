"""
Task 8 - generate a real Power BI project (PBIP) for the Superstore star schema.

Output: task_08/pbip/SuperstoreInsights.pbip
  SuperstoreInsights.SemanticModel/   TMDL: 5 tables, 4 relationships, 23 measures
  SuperstoreInsights.Report/          PBIR: 3 pages, KPI cards, charts, table, slicers

Schema versions / file layout follow the PBIR structure Power BI Desktop creates
(definition/report.json 3.2.0, page 2.1.0, visualContainer 2.7.0, versionMetadata 1.0.0).

Run:  python build_pbix_project.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import uuid

import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
MODEL = HERE / "model"
OUT = HERE / "pbip"
NAME = "SuperstoreInsights"

SM = OUT / f"{NAME}.SemanticModel"
RP = OUT / f"{NAME}.Report"

THEME_NAME = "SuperstoreTheme"

# ---------------------------------------------------------------- schemas ---
DEFINITION_PBIR_SCHEMA = (
    "https://developer.microsoft.com/json-schemas/fabric/item/report/"
    "definitionProperties/2.0.0/schema.json"
)
VERSION_SCHEMA = (
    "https://developer.microsoft.com/json-schemas/fabric/item/report/"
    "definition/versionMetadata/1.0.0/schema.json"
)
REPORT_SCHEMA = (
    "https://developer.microsoft.com/json-schemas/fabric/item/report/"
    "definition/report/3.2.0/schema.json"
)
PAGES_SCHEMA = (
    "https://developer.microsoft.com/json-schemas/fabric/item/report/"
    "definition/pagesMetadata/1.0.0/schema.json"
)
PAGE_SCHEMA = (
    "https://developer.microsoft.com/json-schemas/fabric/item/report/"
    "definition/page/2.1.0/schema.json"
)
VISUAL_SCHEMA = (
    "https://developer.microsoft.com/json-schemas/fabric/item/report/"
    "definition/visualContainer/2.7.0/schema.json"
)


def tag() -> str:
    return str(uuid.uuid4())


def hex_id(label: str) -> str:
    return hashlib.sha1(label.encode()).hexdigest()[:20]


def w(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def wj(path: pathlib.Path, obj) -> None:
    w(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


# ================================================================ MODEL ====
M_TYPE = {
    "object": "type text",
    "int64": "Int64.Type",
    "float64": "Double.Type",
    "datetime64[ns]": "type date",
}


def m_source(table: str) -> str:
    df = pd.read_csv(MODEL / f"{table}.csv")
    pandas_type = {
        c: ("datetime64[ns]" if (table == "DimDate" and c == "Date") else str(d))
        for c, d in df.dtypes.items()
    }
    csv_path = str(MODEL / f"{table}.csv")

    cols = ", ".join(f'"{c}"' for c in df.columns)
    types = ",\n                ".join(
        f'{{"{c}", {M_TYPE[pandas_type[c]]}}}' for c in df.columns
    )
    return (
        "let\n"
        f'    Source = Csv.Document(File.Contents("{csv_path}"),'
        f'[Delimiter=",", Columns={len(df.columns)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),\n'
        "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),\n"
        f"    Selected = Table.SelectColumns(Promoted, {{{cols}}}),\n"
        "    Typed = Table.TransformColumnTypes(Selected, {\n                "
        f"{types}\n            }})\n"
        "in\n"
        "    Typed"
    )


TABLES = {
    "FactSales": {
        "OrderID": ("string", "none"),
        "DateKey": ("int64", "none", "0"),
        "ProductKey": ("string", "none"),
        "CustomerKey": ("string", "none"),
        "GeoKey": ("int64", "none", "0"),
        "ShipMode": ("string", "none"),
        "Sales": ("double", "sum", "\\$#,0.00"),
        "Quantity": ("int64", "sum", "\\#,##0"),
        "Discount": ("double", "none", "0.0%"),
        "Profit": ("double", "sum", "\\$#,0.00"),
        "ShipDays": ("int64", "none", "0"),
    },
    "DimDate": {
        "DateKey": ("int64", "none", "0"),
        "Date": ("dateTime", "none", "yyyy-mm-dd", True),
        "Year": ("int64", "none", "0"),
        "Quarter": ("string", "none"),
        "Month": ("int64", "none", "0"),
        "MonthName": ("string", "none"),
        "YearMonth": ("string", "none"),
        "Weekday": ("string", "none"),
    },
    "DimProduct": {
        "ProductKey": ("string", "none"),
        "Category": ("string", "none"),
        "SubCategory": ("string", "none"),
        "ProductName": ("string", "none"),
    },
    "DimCustomer": {
        "CustomerKey": ("string", "none"),
        "CustomerName": ("string", "none"),
        "Segment": ("string", "none"),
    },
    "DimGeography": {
        "GeoKey": ("int64", "none", "0"),
        "Country": ("string", "none"),
        "Region": ("string", "none"),
        "State": ("string", "none"),
        "City": ("string", "none"),
        "PostalCode": ("int64", "none", "0"),
    },
}

MEASURES = [
    ("Total Revenue", "SUM ( FactSales[Sales] )", "\\$#,0.00"),
    ("Total Profit", "SUM ( FactSales[Profit] )", "\\$#,0.00"),
    ("Units Sold", "SUM ( FactSales[Quantity] )", "\\#,##0"),
    ("Orders", "DISTINCTCOUNT ( FactSales[OrderID] )", "\\#,##0"),
    ("Profit Margin", "DIVIDE ( [Total Profit], [Total Revenue] )", "0.0%"),
    ("Average Order Value", "DIVIDE ( [Total Revenue], [Orders] )", "\\$#,0.00"),
    ("Average Discount", "AVERAGE ( FactSales[Discount] )", "0.0%"),
    ("Avg Ship Days", "AVERAGE ( FactSales[ShipDays] )", "0.0"),
    ("Revenue LY", "CALCULATE ( [Total Revenue], SAMEPERIODLASTYEAR ( DimDate[Date] ) )", "\\$#,0.00"),
    ("YoY Growth", "DIVIDE ( [Total Revenue] - [Revenue LY], [Revenue LY] )", "+0.0%;-0.0%;0.0%"),
    ("Revenue PM", "CALCULATE ( [Total Revenue], DATEADD ( DimDate[Date], -1, MONTH ) )", "\\$#,0.00"),
    ("MoM Growth", "DIVIDE ( [Total Revenue] - [Revenue PM], [Revenue PM] )", "+0.0%;-0.0%;0.0%"),
    ("Revenue YTD", "TOTALYTD ( [Total Revenue], DimDate[Date] )", "\\$#,0.00"),
    ("Product Revenue Rank", "RANKX ( ALLSELECTED ( DimProduct[ProductName] ), [Total Revenue], , DESC )", "\\#,##0"),
    (
        "Revenue of Top 10 Products",
        "CALCULATE ( [Total Revenue], KEEPFILTERS ( TOPN ( 10, ALLSELECTED "
        "( DimProduct[ProductName] ), [Total Revenue], DESC ) ) )",
        "\\$#,0.00",
    ),
    (
        "Top 10 Share of Revenue",
        "DIVIDE ( [Revenue of Top 10 Products], CALCULATE ( [Total Revenue], "
        "ALLSELECTED ( DimProduct[ProductName] ) ) )",
        "0.0%",
    ),
    (
        "YoY Growth Last Year",
        "VAR y = CALCULATE ( MAX ( DimDate[Year] ), ALL ( DimDate ) ) "
        "VAR cur = CALCULATE ( [Total Revenue], DimDate[Year] = y ) "
        "VAR prev = CALCULATE ( [Total Revenue], DimDate[Year] = y - 1 ) "
        "RETURN DIVIDE ( cur - prev, prev )",
        "+0.0%;-0.0%;0.0%",
    ),
    ("Top Product Revenue", "SUM ( TopProducts[Revenue] )", "\\$#,0.00"),
    ("Customers", "DISTINCTCOUNT ( FactSales[CustomerKey] )", "\\#,##0"),
    ("Revenue per Customer", "DIVIDE ( [Total Revenue], [Customers] )", "\\$#,0.00"),
    (
        "Region Revenue Rank",
        "RANKX ( ALLSELECTED ( DimGeography[Region] ), [Total Revenue], , DESC )",
        "\\#,##0",
    ),
    (
        "Best Region",
        "CALCULATE ( SELECTEDVALUE ( DimGeography[Region] ), TOPN ( 1, ALL "
        "( DimGeography[Region] ), [Total Revenue], DESC ) )",
        None,
    ),
    (
        "Revenue Colour",
        'SWITCH ( TRUE (), [YoY Growth] >= 0.1, "#2E7D32", [YoY Growth] >= 0, "#F2A900", "#C0392B" )',
        None,
    ),
    ("Margin Warning", 'IF ( [Profit Margin] < 0.05, "Below 5% margin", "Healthy" )', None),
    (
        "Report Title",
        '"Superstore Retail Insights — " & FORMAT ( MIN ( DimDate[Date] ), "mmm yyyy" ) '
        '& " to " & FORMAT ( MAX ( DimDate[Date] ), "mmm yyyy" ) & "  |  Revenue " '
        '& FORMAT ( [Total Revenue], "$#,##0" )',
        None,
    ),
]


def table_tmdl(name: str, cols: dict) -> str:
    out = [f"table {name}"]
    if name == "DimDate":
        out.append("\tdataCategory: Time")
    out.append(f"\tlineageTag: {tag()}")
    out.append("")
    for col, spec in cols.items():
        dtype, summarise = spec[0], spec[1]
        fmt = spec[2] if len(spec) > 2 else None
        is_key = len(spec) > 3 and spec[3]
        out.append(f"\tcolumn {col}")
        out.append(f"\t\tdataType: {dtype}")
        if is_key:
            out.append("\t\tisKey")
        if fmt:
            out.append(f"\t\tformatString: {fmt}")
        out.append(f"\t\tsummarizeBy: {summarise}")
        out.append(f"\t\tlineageTag: {tag()}")
        out.append("")

    body = m_source(name).replace("\n", "\n\t\t\t\t")
    out += [
        f"\tpartition {name} = m",
        "\t\tmode: import",
        "\t\tsource =",
        f"\t\t\t\t{body}",
        "",
        "\tannotation PBI_ResultType = Table",
        "",
    ]
    return "\n".join(out)


def measures_tmdl() -> str:
    out = ["table _Measures", f"\tlineageTag: {tag()}", ""]
    out += [
        "\tcolumn Value",
        "\t\tdataType: int64",
        "\t\tisHidden",
        "\t\tsourceColumn: [Value]",
        "\t\tsummarizeBy: none",
        f"\t\tlineageTag: {tag()}",
        "",
    ]
    for name, dax, fmt in MEASURES:
        out.append(f"\tmeasure '{name}' = {dax}")
        if fmt:
            out.append(f"\t\tformatString: {fmt}")
        out.append(f"\t\tlineageTag: {tag()}")
        out.append("")
    out += [
        "\tpartition _Measures = calculated",
        "\t\tmode: import",
        "\t\tsource = {1}",
        "",
    ]
    return "\n".join(out)


TOPPRODUCTS_COLS = {
    "ProductName": ("string", "none"),
    "Revenue": ("double", "sum", "\$#,0.00"),
}


def write_top_products_csv() -> None:
    """Top 10 products by revenue, materialised as a CSV so the table is a plain import."""
    fact = pd.read_csv(MODEL / "FactSales.csv", usecols=["ProductKey", "Sales"])
    dim = pd.read_csv(MODEL / "DimProduct.csv", usecols=["ProductKey", "ProductName"])
    top = (
        fact.merge(dim, on="ProductKey")
        .groupby("ProductName", as_index=False)["Sales"]
        .sum()
        .sort_values("Sales", ascending=False)
        .head(10)
        .rename(columns={"Sales": "Revenue"})
    )
    top.to_csv(MODEL / "TopProducts.csv", index=False)
    print(f"TopProducts.csv: {len(top)} rows, top = {top.iloc[0, 0]} ({top.iloc[0, 1]:,.2f})")


RELATIONSHIPS = [
    ("rel_Fact_Date", "FactSales", "DateKey", "DimDate", "DateKey"),
    ("rel_Fact_Product", "FactSales", "ProductKey", "DimProduct", "ProductKey"),
    ("rel_Fact_Customer", "FactSales", "CustomerKey", "DimCustomer", "CustomerKey"),
    ("rel_Fact_Geo", "FactSales", "GeoKey", "DimGeography", "GeoKey"),
]


def relationships_tmdl() -> str:
    out = []
    for name, f_tbl, f_col, t_tbl, t_col in RELATIONSHIPS:
        out += [
            f"relationship {name}",
            f"\tfromColumn: {f_tbl}.{f_col}",
            f"\ttoColumn: {t_tbl}.{t_col}",
            "",
        ]
    return "\n".join(out)


def model_tmdl() -> str:
    out = [
        "model Model",
        "\tculture: en-US",
        "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tsourceQueryCulture: en-US",
        "\tdataAccessOptions",
        "\t\tlegacyRedirects",
        "\t\treturnErrorValuesAsNull",
        "",
    ]
    for t in list(TABLES) + ["_Measures", "TopProducts"]:
        out.append(f"ref table {t}")
    out += [
        "",
        'annotation PBI_QueryOrder = ["FactSales","DimDate","DimProduct",'
        '"DimCustomer","DimGeography","_Measures"]',
        "",
    ]
    return "\n".join(out)


def build_semantic_model() -> None:
    wj(
        SM / "definition.pbism",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
            "version": "4.0",
            "settings": {},
        },
    )
    wj(
        SM / ".platform",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {"type": "SemanticModel", "displayName": NAME},
            "config": {"version": "2.0", "logicalId": tag()},
        },
    )
    w(SM / "definition" / "database.tmdl", "database\n\tcompatibilityLevel: 1604\n")
    w(SM / "definition" / "model.tmdl", model_tmdl())
    w(SM / "definition" / "relationships.tmdl", relationships_tmdl())
    for name, cols in TABLES.items():
        w(SM / "definition" / "tables" / f"{name}.tmdl", table_tmdl(name, cols))
    w(SM / "definition" / "tables" / "_Measures.tmdl", measures_tmdl())
    w(
        SM / "definition" / "tables" / "TopProducts.tmdl",
        table_tmdl("TopProducts", TOPPRODUCTS_COLS),
    )


# =============================================================== REPORT ====
def ref_col(entity: str, prop: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def ref_measure(entity: str, prop: str) -> dict:
    return {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def proj_col(entity: str, prop: str) -> dict:
    return {
        "field": ref_col(entity, prop),
        "queryRef": f"{entity}.{prop}",
        "nativeQueryRef": prop,
    }


def proj_measure(entity: str, prop: str) -> dict:
    return {
        "field": ref_measure(entity, prop),
        "queryRef": f"{entity}.{prop}",
        "nativeQueryRef": prop,
    }


def proj_col_agg(entity: str, prop: str, func: str = "Sum") -> dict:
    """Implicit aggregation of a column: queryRef must read Sum(Table.Column)."""
    return {
        "field": ref_col(entity, prop),
        "queryRef": f"{func}({entity}.{prop})",
        "nativeQueryRef": f"{func} of {prop}",
    }


def visual(
    name: str,
    vtype: str,
    pos: dict,
    query_state: dict,
    sort: dict | None = None,
    filters: dict | None = None,
    **extra,
) -> dict:
    query: dict = {"queryState": query_state}
    if sort:
        query["sortDefinition"] = sort
    body = {
        "visualType": vtype,
        "query": query,
        "drillFilterOtherVisuals": True,
    }
    body.update(extra)
    out = {
        "$schema": VISUAL_SCHEMA,
        "name": name,
        "position": pos,
    }
    if filters:
        out["filterConfig"] = filters
    out["visual"] = body
    return out


def pos(x: int, y: int, wd: int, ht: int, order: int = 0) -> dict:
    return {"x": x, "y": y, "z": 0, "width": wd, "height": ht, "tabOrder": order}


def card(name: str, posd: dict, field: dict) -> dict:
    return visual(name, "cardVisual", posd, {"Data": {"projections": [field]}})


def build_overview_page() -> list[dict]:
    v: list[dict] = []
    order = 0

    order += 1
    v.append(card("vTitle", pos(8, 4, 1264, 44, order), proj_measure("_Measures", "Report Title")))

    for i, m in enumerate(
        ["Total Revenue", "Total Profit", "Profit Margin", "Units Sold",
         "Average Order Value", "YoY Growth Last Year"]
    ):
        order += 1
        v.append(
            card(
                f"vKpi{i}",
                pos(8 + i * 212, 52, 200, 62, order),
                proj_measure("_Measures", m),
            )
        )

    order += 1
    v.append(
        visual(
            "vTrend",
            "lineChart",
            pos(8, 120, 620, 250, order),
            {
                "Category": {"projections": [proj_col("DimDate", "YearMonth")]},
                "Y": {"projections": [proj_measure("_Measures", "Total Revenue")]},
            },
            sort={
                "sort": [{"field": ref_col("DimDate", "YearMonth"), "direction": "Ascending"}]
            },
        )
    )

    order += 1
    v.append(
        visual(
            "vRegion",
            "barChart",
            pos(636, 120, 636, 250, order),
            {
                "Category": {"projections": [proj_col("DimGeography", "Region")]},
                "Y": {"projections": [proj_measure("_Measures", "Total Revenue")]},
            },
            sort={
                "sort": [{"field": ref_measure("_Measures", "Total Revenue"), "direction": "Descending"}]
            },
        )
    )

    order += 1
    v.append(
        visual(
            "vTop10",
            "barChart",
            pos(8, 376, 620, 200, order),
            {
                "Category": {"projections": [proj_col("TopProducts", "ProductName")]},
                "Y": {"projections": [proj_measure("_Measures", "Top Product Revenue")]},
            },
            sort={
                "sort": [{"field": ref_measure("_Measures", "Top Product Revenue"), "direction": "Descending"}]
            },
        )
    )

    order += 1
    v.append(
        visual(
            "vCategory",
            "donutChart",
            pos(636, 376, 300, 200, order),
            {
                "Category": {"projections": [proj_col("DimProduct", "Category")]},
                "Y": {"projections": [proj_measure("_Measures", "Total Revenue")]},
            },
        )
    )

    order += 1
    v.append(
        visual(
            "vSegment",
            "tableEx",
            pos(944, 376, 328, 200, order),
            {
                "Values": {
                    "projections": [
                        proj_col("DimCustomer", "Segment"),
                        proj_measure("_Measures", "Total Revenue"),
                        proj_measure("_Measures", "Total Profit"),
                        proj_measure("_Measures", "Profit Margin"),
                    ]
                }
            },
        )
    )

    slicers = [
        ("DimGeography", "Region"),
        ("DimProduct", "Category"),
        ("DimCustomer", "Segment"),
        ("DimDate", "Year"),
        ("FactSales", "ShipMode"),
    ]
    for i, (ent, col) in enumerate(slicers):
        order += 1
        v.append(
            visual(
                f"vSlicer{i}",
                "slicer",
                pos(8 + i * 252, 582, 248, 128, order),
                {"Values": {"projections": [proj_col(ent, col)]}},
            )
        )
    return v


def build_product_page() -> list[dict]:
    return [
        visual(
            "pMatrix",
            "matrix",
            pos(8, 8, 620, 300, 1),
            {
                "Rows": {"projections": [proj_col("DimProduct", "SubCategory")]},
                "Columns": {"projections": [proj_col("DimDate", "Year")]},
                "Values": {"projections": [proj_measure("_Measures", "Total Revenue")]},
            },
        ),
        visual(
            "pTrend",
            "lineChart",
            pos(636, 8, 636, 300, 2),
            {
                "Category": {"projections": [proj_col("DimDate", "YearMonth")]},
                "Y": {"projections": [proj_measure("_Measures", "Total Revenue")]},
            },
            sort={
                "sort": [{"field": ref_col("DimDate", "YearMonth"), "direction": "Ascending"}]
            },
        ),
        card("pRev", pos(8, 316, 300, 90, 3), proj_measure("_Measures", "Total Revenue")),
        card("pMargin", pos(316, 316, 300, 90, 4), proj_measure("_Measures", "Profit Margin")),
        card("pUnits", pos(624, 316, 300, 90, 5), proj_measure("_Measures", "Units Sold")),
        card("pWarn", pos(932, 316, 340, 90, 6), proj_measure("_Measures", "Margin Warning")),
        card("pProduct", pos(8, 414, 1264, 90, 7), proj_col_agg("DimProduct", "ProductName", "First")),
        visual(
            "pTable",
            "tableEx",
            pos(8, 512, 1264, 190, 8),
            {
                "Values": {
                    "projections": [
                        proj_col("DimProduct", "ProductName"),
                        proj_measure("_Measures", "Total Revenue"),
                        proj_measure("_Measures", "Total Profit"),
                        proj_measure("_Measures", "Profit Margin"),
                    ]
                }
            },
        ),
    ]


def build_geo_page() -> list[dict]:
    return [
        visual(
            "gMap",
            "map",
            pos(8, 8, 740, 560, 1),
            {
                "Category": {"projections": [proj_col("DimGeography", "State")]},
                "Size": {"projections": [proj_measure("_Measures", "Total Revenue")]},
                "Tooltips": {"projections": [proj_measure("_Measures", "Profit Margin")]},
            },
        ),
        visual(
            "gRegion",
            "barChart",
            pos(756, 8, 516, 560, 2),
            {
                "Category": {"projections": [proj_col("DimGeography", "Region")]},
                "Y": {"projections": [proj_measure("_Measures", "Total Revenue")]},
            },
            sort={
                "sort": [{"field": ref_measure("_Measures", "Total Revenue"), "direction": "Descending"}]
            },
        ),
    ]


def write_theme() -> None:
    """A real theme file so report.json's themeCollection resolves."""
    theme = {
        "name": THEME_NAME,
        "dataColors": [
            "#1F3864", "#2C7FB8", "#2E7D32", "#F2A900", "#C0392B",
            "#7B4CA0", "#00A6A6", "#6C7A89", "#D06C8D", "#4C9A2A",
        ],
        "background": "#FFFFFF",
        "foreground": "#1F3864",
        "tableAccent": "#2C7FB8",
        "textClasses": {
            "title": {"fontFace": "Segoe UI Semibold", "fontSize": 14, "color": "#1F3864"},
            "header": {"fontFace": "Segoe UI Semibold", "fontSize": 11, "color": "#1F3864"},
            "label": {"fontFace": "Segoe UI", "fontSize": 9, "color": "#333333"},
            "callout": {"fontFace": "Segoe UI Semibold", "fontSize": 26, "color": "#1F3864"},
        },
    }
    wj(
        RP / "StaticResources" / "SharedResources" / "BaseThemes" / f"{THEME_NAME}.json",
        theme,
    )


def build_report() -> None:
    pages = [
        (hex_id("page-overview"), "Overview", build_overview_page()),
        (hex_id("page-product"), "Product detail", build_product_page()),
        (hex_id("page-geo"), "Geography", build_geo_page()),
    ]

    wj(
        RP / "definition" / "version.json",
        {"$schema": VERSION_SCHEMA, "version": "2.0.0"},
    )
    wj(
        RP / "definition" / "report.json",
        {
            "$schema": REPORT_SCHEMA,
            "themeCollection": {
                "baseTheme": {
                    "name": THEME_NAME,
                    "reportVersionAtImport": {"visual": "2.6.0", "report": "3.1.0", "page": "2.3.0"},
                    "type": "SharedResources",
                }
            },
            "resourcePackages": [
                {
                    "name": "SharedResources",
                    "type": "SharedResources",
                    "items": [
                        {
                            "name": THEME_NAME,
                            "path": f"BaseThemes/{THEME_NAME}.json",
                            "type": "BaseTheme",
                        }
                    ],
                }
            ],
            "settings": {
                "useStylableVisualContainerHeader": True,
                "exportDataMode": "AllowSummarized",
                "defaultDrillFilterOtherVisuals": True,
                "allowChangeFilterTypes": True,
                "useEnhancedTooltips": True,
                "useDefaultAggregateDisplayName": True,
            },
        },
    )
    write_theme()

    wj(
        RP / "definition" / "pages" / "pages.json",
        {
            "$schema": PAGES_SCHEMA,
            "pageOrder": [p[0] for p in pages],
            "activePageName": pages[0][0],
        },
    )
    for page_id, display, visuals in pages:
        wj(
            RP / "definition" / "pages" / page_id / "page.json",
            {
                "$schema": PAGE_SCHEMA,
                "name": page_id,
                "displayName": display,
                "displayOption": "FitToPage",
                "height": 720,
                "width": 1280,
            },
        )
        for vi in visuals:
            wj(
                RP / "definition" / "pages" / page_id / "visuals" / vi["name"] / "visual.json",
                vi,
            )

    wj(
        RP / "definition.pbir",
        {
            "$schema": DEFINITION_PBIR_SCHEMA,
            "version": "4.0",
            "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}},
        },
    )
    wj(
        RP / ".platform",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {"type": "Report", "displayName": f"{NAME} Report"},
            "config": {"version": "2.0", "logicalId": tag()},
        },
    )


def main() -> None:
    write_top_products_csv()
    if OUT.exists():
        shutil.rmtree(OUT)
    build_semantic_model()
    build_report()
    wj(
        OUT / f"{NAME}.pbip",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
            "version": "1.0",
            "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
            "settings": {"enableAutoRecovery": True},
        },
    )
    n = sum(1 for f in OUT.rglob("*") if f.is_file())
    print(f"PBIP written to {OUT}  ({n} files)")


if __name__ == "__main__":
    main()
