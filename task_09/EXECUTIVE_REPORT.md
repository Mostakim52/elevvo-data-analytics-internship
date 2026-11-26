# Olist e-commerce — Executive Report

**To:** CEO &nbsp;•&nbsp; **Re:** *Are the customers we acquired in 2017 still buying in 2018?*
**Data:** 99,441 orders, 112,650 items, 103,886 payments, 104,720 reviews (Sep 2016 – Oct 2018)
**Method:** star schema in SQLite (`olist_star.sqlite`) → SQL joins → cohort matrix → CLV

---

## The answer, in one line

**No — almost none of them.** Of **42,131 customers acquired in 2017**, only **643 (1.5%)** placed another
delivered order in 2018. The business is not retaining customers; it is repeatedly re-acquiring them.

## Headline numbers

| Metric | Value |
|---|---|
| Delivered revenue | **R$15.4M** |
| Repeat purchase rate (all time) | **3.0%** |
| Maximum orders by a single customer | 15 |
| Average month-1 retention | **0.5%** |
| Average observed CLV | **≈R$170** |
| Top state | **SP — R$5.8M** |
| Top 1% of customers | **10.4% of revenue** |

## 1. Retention by cohort

Each cohort is the month of a customer's first delivered purchase. Retention in month *n* is the share of
that cohort that bought again *n* months later.

- Month-1 retention peaks at **1.9%** (Jul 2018 cohort) and is **0.2–1.0%** for most 2017 cohorts.
- Cumulative 12-month repurchase is **2.5–3.5%** for every cohort — the pattern is stable, not a one-off dip.
- The 2017 cohorts show **0.9%–2.2%** of their members buying at any point in 2018.

**Interpretation:** this is a low-frequency, high-consideration marketplace. A repeat rate near 3% is
normal for Olist-type platforms, but it still means marketing spend buys one transaction, not a relationship.

## 2. Where the money comes from

| State | Revenue | Orders | AOV |
|---|---|---|---|
| SP | R$5.8M | ~40k | R$138 |
| RJ | R$2.1M | — | R$147 |
| MG | R$1.9M | — | R$140 |

Revenue is heavily concentrated in the south-east. Any retention programme should start there — it has the
volume to measure lift, and the shortest delivery times.

## 3. Delivery is the retention lever

Correlation between average delivery days and average review score across 24 states: **r = −0.56**.

| Delivery time | Orders | Avg review |
|---|---|---|
| under 5 days | 13,374 | **4.45** |
| 5–10 days | 32,885 | 4.36 |
| 10–15 days | 23,470 | 4.27 |
| 15–25 days | 18,461 | 4.04 |
| **25+ days** | 7,634 | **2.70** |

A slow delivery costs more than a full review point. The worst states (AM 26.4 days, AL 24.4, PA 23.6) are
exactly the ones with the lowest scores — and they are also where sellers are furthest from customers.

## 4. Power users

The top **1% of customers (934 people)** generate **10.4% of revenue** at an average of R$1,709 each, versus
R$170 for a typical customer. They order 1.11 times on average — even the best customers are not loyal yet.

## Recommendations

1. **Fix fulfilment in the north-east/north before spending on retention.** Cutting 25+ day deliveries is
   the cheapest route to higher review scores, and reviews drive the next purchase.
2. **Treat the top 1% as a named segment.** At R$1,709 average value, a small account-management or loyalty
   programme pays for itself with a handful of saved customers.
3. **Measure retention properly.** A cohort dashboard refreshed monthly (this notebook) should replace the
   revenue-only reporting the CEO complained about.
4. **Set a realistic target.** Moving cumulative 12-month repurchase from 3% to 5% is worth roughly
   R$750k of incremental revenue on the current base — a credible first-year goal.

Artefacts: `Olist_Cohort_Analysis.ipynb`, `olist_star.sqlite`, `fig_cohort_heatmap.png`,
`fig_revenue.png`, `fig_clv.png`, `fig_delivery_review.png`.
