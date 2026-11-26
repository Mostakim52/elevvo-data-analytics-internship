-- ============================================================
-- Elevvo Internship — Task 5: SQL-Based Analysis of Product Sales
-- Dataset: Chinook Database (SQLite) — a digital media store
-- Tables used: Invoice, InvoiceLine, Track, Album, Artist,
--              Customer, Genre, Employee
-- ============================================================

-- ------------------------------------------------------------
-- Q1. Top-selling products (tracks) by units and revenue
-- JOINs: InvoiceLine × Track × Album × Artist
-- ------------------------------------------------------------
SELECT
    t.TrackId,
    t.Name                      AS track,
    ar.Name                     AS artist,
    al.Title                    AS album,
    SUM(il.Quantity)            AS units_sold,
    ROUND(SUM(il.UnitPrice * il.Quantity), 2) AS revenue
FROM InvoiceLine il
JOIN Track  t  ON t.TrackId  = il.TrackId
JOIN Album  al ON al.AlbumId = t.AlbumId
JOIN Artist ar ON ar.ArtistId = al.ArtistId
GROUP BY t.TrackId
ORDER BY revenue DESC, units_sold DESC, track
LIMIT 10;

-- ------------------------------------------------------------
-- Q2. Top-selling tracks by units (alternative ranking)
-- Ranked with a WINDOW FUNCTION (bonus requirement)
-- ------------------------------------------------------------
SELECT
    t.Name AS track,
    ar.Name AS artist,
    SUM(il.Quantity) AS units_sold,
    RANK() OVER (ORDER BY SUM(il.Quantity) DESC) AS units_rank,
    RANK() OVER (ORDER BY SUM(il.UnitPrice * il.Quantity) DESC) AS revenue_rank
FROM InvoiceLine il
JOIN Track  t  ON t.TrackId  = il.TrackId
JOIN Album  al ON al.AlbumId = t.AlbumId
JOIN Artist ar ON ar.ArtistId = al.ArtistId
GROUP BY t.TrackId
ORDER BY units_sold DESC
LIMIT 10;

-- ------------------------------------------------------------
-- Q3. Revenue per country (region proxy), with customer counts
-- JOINs: Invoice × Customer
-- ------------------------------------------------------------
SELECT
    c.Country,
    COUNT(DISTINCT c.CustomerId)              AS customers,
    COUNT(DISTINCT i.InvoiceId)               AS invoices,
    ROUND(SUM(i.Total), 2)                    AS revenue,
    ROUND(AVG(i.Total), 2)                    AS avg_invoice_value
FROM Invoice i
JOIN Customer c ON c.CustomerId = i.CustomerId
GROUP BY c.Country
ORDER BY revenue DESC;

-- ------------------------------------------------------------
-- Q4. Revenue per continent-ish region (billing country grouped)
-- Shows aggregation + classification with CASE
-- ------------------------------------------------------------
SELECT
    CASE
        WHEN c.Country IN ('USA','Canada','Brazil','Argentina','Chile','Mexico') THEN 'Americas'
        WHEN c.Country IN ('Germany','France','United Kingdom','Portugal','Spain','Italy','Netherlands','Belgium','Austria','Switzerland','Denmark','Norway','Sweden','Poland','Czech Republic','Finland','Ireland','Hungary') THEN 'Europe'
        WHEN c.Country IN ('India','Australia','Japan') THEN 'Asia-Pacific'
        ELSE 'Other'
    END AS region,
    ROUND(SUM(i.Total), 2) AS revenue,
    COUNT(DISTINCT c.CustomerId) AS customers
FROM Invoice i
JOIN Customer c ON c.CustomerId = i.CustomerId
GROUP BY region
ORDER BY revenue DESC;

-- ------------------------------------------------------------
-- Q5. Monthly performance — revenue, orders, avg order value
-- JOINs: Invoice × InvoiceLine (for units)
-- ------------------------------------------------------------
SELECT
    strftime('%Y-%m', i.InvoiceDate)             AS month,
    COUNT(DISTINCT i.InvoiceId)                  AS orders,
    SUM(il.Quantity)                             AS units_sold,
    ROUND(SUM(i.Total), 2)                       AS revenue,
    ROUND(SUM(i.Total) / COUNT(DISTINCT i.InvoiceId), 2) AS avg_order_value
FROM Invoice i
JOIN InvoiceLine il ON il.InvoiceId = i.InvoiceId
GROUP BY month
ORDER BY month;

-- ------------------------------------------------------------
-- Q6. Top genre by revenue per year — uses ROW_NUMBER()
-- (window function, bonus requirement)
-- ------------------------------------------------------------
WITH genre_year AS (
    SELECT
        strftime('%Y', i.InvoiceDate)   AS year,
        g.Name                          AS genre,
        ROUND(SUM(il.UnitPrice * il.Quantity), 2) AS revenue,
        ROW_NUMBER() OVER (PARTITION BY strftime('%Y', i.InvoiceDate)
                           ORDER BY SUM(il.UnitPrice * il.Quantity) DESC) AS rn
    FROM InvoiceLine il
    JOIN Invoice i ON i.InvoiceId = il.InvoiceId
    JOIN Track  t ON t.TrackId   = il.TrackId
    JOIN Genre  g ON g.GenreId   = t.GenreId
    GROUP BY year, g.Name
)
SELECT year, genre, revenue
FROM genre_year
WHERE rn = 1
ORDER BY year;

-- ------------------------------------------------------------
-- Q7. Customer lifetime value with running total (window fn)
-- ------------------------------------------------------------
SELECT
    c.CustomerId,
    c.FirstName || ' ' || c.LastName               AS customer,
    c.Country,
    ROUND(SUM(i.Total), 2)                         AS lifetime_value,
    COUNT(i.InvoiceId)                             AS orders,
    ROUND(SUM(SUM(i.Total)) OVER (ORDER BY SUM(i.Total) DESC
                                  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2)
                                                   AS running_revenue,
    ROUND(100.0 * SUM(SUM(i.Total)) OVER (ORDER BY SUM(i.Total) DESC
                                  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
          / SUM(SUM(i.Total)) OVER (), 1)          AS cumulative_pct
FROM Customer c
JOIN Invoice i ON i.CustomerId = c.CustomerId
GROUP BY c.CustomerId
ORDER BY lifetime_value DESC
LIMIT 15;

-- ------------------------------------------------------------
-- Q8. Employee sales performance (support rep leaderboard)
-- JOINs: Employee × Customer × Invoice
-- ------------------------------------------------------------
SELECT
    e.EmployeeId,
    e.FirstName || ' ' || e.LastName               AS rep,
    e.Title,
    COUNT(DISTINCT c.CustomerId)                    AS customers,
    COUNT(DISTINCT i.InvoiceId)                     AS orders,
    ROUND(SUM(i.Total), 2)                          AS revenue
FROM Employee e
JOIN Customer c ON c.SupportRepId = e.EmployeeId
JOIN Invoice  i ON i.CustomerId   = c.CustomerId
GROUP BY e.EmployeeId
ORDER BY revenue DESC;

-- ------------------------------------------------------------
-- Q9. Average track price vs units sold, per genre (HAVING filter)
-- ------------------------------------------------------------
SELECT
    g.Name                                          AS genre,
    COUNT(DISTINCT t.TrackId)                       AS tracks,
    ROUND(AVG(il.UnitPrice), 2)                     AS avg_price,
    SUM(il.Quantity)                                AS units_sold,
    ROUND(SUM(il.UnitPrice * il.Quantity), 2)       AS revenue
FROM Genre g
JOIN Track t       ON t.GenreId  = g.GenreId
JOIN InvoiceLine il ON il.TrackId = t.TrackId
GROUP BY g.GenreId
HAVING units_sold > 100
ORDER BY revenue DESC;

-- ------------------------------------------------------------
-- Q10. Monthly revenue with previous month via LAG() (window fn)
-- ------------------------------------------------------------
WITH monthly AS (
    SELECT
        strftime('%Y-%m', InvoiceDate) AS month,
        SUM(Total)                     AS revenue
    FROM Invoice
    GROUP BY month
)
SELECT
    month,
    ROUND(revenue, 2)                            AS revenue,
    ROUND(LAG(revenue) OVER (ORDER BY month), 2) AS prev_month_revenue,
    ROUND(revenue - LAG(revenue) OVER (ORDER BY month), 2) AS mom_change
FROM monthly
ORDER BY month;
