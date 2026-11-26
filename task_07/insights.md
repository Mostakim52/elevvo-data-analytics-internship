# Task 7 — Walmart retail sales: what the time series says

Source: `datasets/walmart_train.csv` (421,570 weekly store-department rows, Feb 2010 – Oct 2012),
joined with `walmart_stores.csv` and `walmart_features.csv`.

## Trend
- Total sales in the window: **$6.74B** across 45 stores and 81 departments.
- 2011 finished **+7.0%** above 2010.
- The 12-month moving average is flat-to-slightly-up; the visible swings are seasonal, not a trend change.

## Seasonality
- **December is the peak month** — index **1.40** against an average month (≈$288M in both 2010 and 2011).
- **January is the trough** — index **0.81**.
- A second, smaller peak appears in April–July (indices 1.01–1.05).
- The year × month heatmap shows the same shape repeating in all three years, which is what makes the series forecastable.

## Holidays
- Holiday weeks average **+7.8%** above ordinary weeks.
- The single largest week of each year is **Thanksgiving week** ($66.6M in 2011 vs $47.3M for Super Bowl week).
- Christmas week itself is *not* a peak — the seasonal build happens before it.

## Product (department) breakdown
- The ten largest departments are **46.0%** of revenue; dept 92 (grocery) leads at 7.2%.
- Like-for-like (Feb–Oct 2012 vs Feb–Oct 2010), **8 of the 10** grew: dept 92 **+11.0%**, dept 90 +7.2%;
  the laggards are dept 72 (−3.9%) and dept 13 (−2.2%).

## Store format ("region")
The dataset carries no state or city, so format is the only regional cut:
- Type A — 22 stores, **64.3%** of revenue, $20.1k average weekly sales.
- Type B — 17 stores, 29.7%, $12.2k.
- Type C — 6 stores, 6.0%, $9.5k.

## Forecast (bonus)
Holt-Winters (additive trend + seasonality) trained on 24 months and tested on the last 9:

| model | MAPE |
|---|---|
| Holt-Winters | **14.4%** |
| 3-month rolling mean | 14.6% |
| last value repeated | 16.0% |

Next six months: $171M–$296M per month, peaking in **December 2012 (~$296M)**.

Figures: `fig_trend.png`, `fig_yoy.png`, `fig_seasonality.png`, `fig_holidays.png`,
`fig_dept_trend.png`, `fig_type.png`, `fig_forecast.png`.
