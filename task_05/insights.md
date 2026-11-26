# Task 5 — Key Findings (Chinook)

The Chinook dataset is a small, static demo database with near-flat pricing ($0.99–$1.99 per track) and two purchases per track in most cases — so "top-sellers" are effectively ties broken by alphabetical order. That is a property of the data, and the queries in `queries.sql` are written correctly regardless.

**Business answers:**

1. **Top-selling products** — TV-show episode tracks (The Office, Heroes, Battlestar Galactica, Lost) lead by units; revenue is flat because of uniform pricing. Rock is the dominant genre, year after year (Q1, Q2, Q6).
2. **Revenue by region** — Europe €1,114 vs Americas $1,101 — a genuine balance; USA is the single largest country ($523, 91 invoices) followed by Canada ($304) (Q3, Q4).
3. **Monthly performance** — revenue is mostly flat ~$37.62/month (a fixed set of recurring invoices) with seasonal spikes (Jan-2022 $491, Apr-2023 $500, Nov-2025 $502) (Q5, Q10).
4. **CLV** — the top 15 customers each bought 7 times for ~$40–50 lifetime value; cumulative top-15 ≈ 28% of revenue — extremely flat distribution typical of a demo store (Q7).
5. **Sales reps** — Jane Peacock leads (21 customers, $833 revenue) ahead of Margaret Park ($775) and Steve Johnson ($720) (Q8).

**Window functions used (bonus):** `RANK() OVER (ORDER BY …)` (Q2), `ROW_NUMBER() OVER (PARTITION BY …)` (Q6), `SUM(…) OVER (… UNBOUNDED PRECEDING)` (Q7), `LAG() OVER (ORDER BY month)` (Q10).
