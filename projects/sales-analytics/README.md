# Sales Analytics Dashboard

Interactive Power BI dashboard analyzing 3 years of sales data (2022–2024) across multiple channels, product categories, and customer segments.

> **Dataset:** ~28,700 transactions | 200 customers | 21 products | 5 stores

<!-- Add a screenshot of your final dashboard here -->
<!-- ![Dashboard Preview](screenshots/dashboard.png) -->

---

## Table of Contents

- [Data Model](#data-model)
- [Loading the Data in Power BI](#loading-the-data-in-power-bi)
- [Relationships](#relationships)
- [DAX Measures](#dax-measures)
  - [Base Measures](#1-base-measures)
  - [Profitability](#2-profitability)
  - [Time Intelligence](#3-time-intelligence-yoy--mom)
  - [Budget vs Actual](#4-budget-vs-actual)
  - [Customer Analytics](#5-customer-analytics)
  - [Rankings & Top N](#6-rankings--top-n)
- [Suggested Visuals](#suggested-visuals)
- [How to Run](#how-to-run)

---

## Data Model

This project uses a **Star Schema** — the standard for analytical models in Power BI. The idea is simple: one central **fact table** (transactions) surrounded by **dimension tables** (descriptive context).

```
                    ┌──────────────┐
                    │   DIM_DATE   │
                    │──────────────│
                    │ DateKey (PK) │
                    │ Year         │
                    │ Quarter      │
                    │ Month        │
                    │ MonthName    │
                    │ DayName      │
                    │ IsWeekend    │
                    └──────┬───────┘
                           │ 1:N
┌──────────────┐   ┌──────┴───────────┐   ┌────────────────┐
│ DIM_CUSTOMER │   │    FACT_SALES    │   │  DIM_PRODUCT   │
│──────────────│   │──────────────────│   │────────────────│
│ CustomerKey  │──▶│ OrderID          │◀──│ ProductKey (PK)│
│ CustomerName │   │ DateKey (FK)     │   │ ProductName    │
│ Segment      │   │ CustomerKey (FK) │   │ Category       │
│ Region       │   │ ProductKey (FK)  │   │ SubCategory    │
│ City         │   │ StoreKey (FK)    │   │ UnitPrice      │
└──────────────┘   │ Quantity         │   │ UnitCost       │
                   │ UnitPrice        │   └────────────────┘
┌──────────────┐   │ DiscountPct      │
│  DIM_STORE   │   │ GrossAmount      │   ┌────────────────┐
│──────────────│   │ DiscountAmount   │   │  FACT_BUDGET   │
│ StoreKey(PK) │──▶│ NetAmount        │   │────────────────│
│ StoreName    │   │ TotalCost        │   │ Year           │
│ Channel      │   └──────────────────┘   │ Month          │
│ Country      │                          │ BudgetAmount   │
└──────────────┘                          └────────────────┘
```

### Why Star Schema?

| Benefit | Explanation |
|---------|------------|
| **Performance** | Power BI's engine (VertiPaq) is optimized for star schemas — faster queries |
| **Simplicity** | Easy to understand: facts = "what happened", dimensions = "the context" |
| **Flexibility** | Add new dimensions without changing the fact table |
| **DAX friendly** | Functions like `CALCULATE`, `FILTER`, `RELATED` work naturally with this structure |

### Tables Explained

| Table | Type | Rows | Purpose |
|-------|------|------|---------|
| `fact_sales` | Fact | ~28,700 | Each row = one order line (product sold in an order) |
| `fact_budget` | Fact | 36 | Monthly sales targets for budget comparison |
| `dim_date` | Dimension | 1,096 | Calendar table — required for time intelligence in DAX |
| `dim_product` | Dimension | 21 | Product catalog with categories and pricing |
| `dim_customer` | Dimension | 200 | Customer info with segments and regions |
| `dim_store` | Dimension | 5 | Sales channels (online, retail, outlet, wholesale) |

---

## Loading the Data in Power BI

1. Open Power BI Desktop
2. **Get Data** → **Text/CSV**
3. Load each file from the `data/` folder:
   - `dim_date.csv`
   - `dim_product.csv`
   - `dim_customer.csv`
   - `dim_store.csv`
   - `fact_sales.csv`
   - `fact_budget.csv`
4. In Power Query, verify column types (dates, integers, decimals)
5. Click **Close & Apply**

---

## Relationships

Set these up in **Model View** (drag and drop):

| From (Fact) | → | To (Dimension) | Cardinality | Direction |
|-------------|---|-----------------|-------------|-----------|
| `fact_sales[DateKey]` | → | `dim_date[DateKey]` | Many to One | Single |
| `fact_sales[ProductKey]` | → | `dim_product[ProductKey]` | Many to One | Single |
| `fact_sales[CustomerKey]` | → | `dim_customer[CustomerKey]` | Many to One | Single |
| `fact_sales[StoreKey]` | → | `dim_store[StoreKey]` | Many to One | Single |

> **Note:** `fact_budget` connects to `dim_date` via Year + Month. Create a calculated column `YearMonth` in both tables, or use `TREATAS` in DAX (shown below).

---

## DAX Measures

Create a new table called **`_Measures`** to organize all measures in one place:
```
_Measures = ROW("Placeholder", 0)
```

### 1. Base Measures

These are the foundation — simple aggregations over the fact table.

```dax
// Total revenue after discounts
// SUM iterates over every row in fact_sales and adds up NetAmount
Total Sales = SUM(fact_sales[NetAmount])
```

```dax
// Total cost of goods sold
Total Cost = SUM(fact_sales[TotalCost])
```

```dax
// Revenue BEFORE discounts
Gross Sales = SUM(fact_sales[GrossAmount])
```

```dax
// Total discount given to customers
Total Discount = SUM(fact_sales[DiscountAmount])
```

```dax
// Number of units sold
Total Quantity = SUM(fact_sales[Quantity])
```

```dax
// Count distinct orders (not lines — one order can have multiple products)
Total Orders = DISTINCTCOUNT(fact_sales[OrderID])
```

```dax
// Average revenue per order
// DIVIDE handles division by zero safely (returns BLANK instead of error)
Avg Order Value =
    DIVIDE(
        [Total Sales],
        [Total Orders],
        0
    )
```

---

### 2. Profitability

```dax
// Profit = what we sold it for - what it cost us
Total Profit =
    [Total Sales] - [Total Cost]
```

```dax
// Profit Margin = profit as a percentage of sales
// Example: if margin = 0.45, we keep 45 cents of every dollar
Profit Margin =
    DIVIDE(
        [Total Profit],
        [Total Sales],
        0
    )
```

> **Format** `Profit Margin` as **Percentage** in the Modeling tab.

```dax
// Discount Rate = how much of gross sales was discounted away
Discount Rate =
    DIVIDE(
        [Total Discount],
        [Gross Sales],
        0
    )
```

---

### 3. Time Intelligence (YoY & MoM)

These use DAX time intelligence functions. **They require a proper date table** (`dim_date`) marked as a Date Table in Power BI.

> **Important:** Go to Model View → select `dim_date` → Mark as Date Table → select the `Date` column.

```dax
// Sales from the same period last year
// SAMEPERIODLASTYEAR shifts the current date context back 12 months
Sales LY =
    CALCULATE(
        [Total Sales],
        SAMEPERIODLASTYEAR(dim_date[Date])
    )
```

```dax
// Year-over-Year change in absolute terms
Sales YoY =
    [Total Sales] - [Sales LY]
```

```dax
// Year-over-Year change as percentage
// If LY was 100 and this year is 120, YoY% = 20%
Sales YoY % =
    DIVIDE(
        [Sales YoY],
        [Sales LY],
        0
    )
```

```dax
// Sales from the previous month
// DATEADD shifts the date context by -1 month
Sales PM =
    CALCULATE(
        [Total Sales],
        DATEADD(dim_date[Date], -1, MONTH)
    )
```

```dax
// Month-over-Month change as percentage
Sales MoM % =
    DIVIDE(
        [Total Sales] - [Sales PM],
        [Sales PM],
        0
    )
```

```dax
// Running total: accumulates sales from the start of the year
// DATESYTD returns all dates from Jan 1 to the current date in context
Sales YTD =
    CALCULATE(
        [Total Sales],
        DATESYTD(dim_date[Date])
    )
```

```dax
// Same running total but for last year (for comparison)
Sales YTD LY =
    CALCULATE(
        [Total Sales],
        DATESYTD(SAMEPERIODLASTYEAR(dim_date[Date]))
    )
```

---

### 4. Budget vs Actual

```dax
// Total budget (from the budget table)
Budget = SUM(fact_budget[BudgetAmount])
```

```dax
// Variance: positive = over budget (good), negative = under target
Budget Variance = [Total Sales] - [Budget]
```

```dax
// Variance as percentage: how far off from target
Budget Variance % =
    DIVIDE(
        [Budget Variance],
        [Budget],
        0
    )
```

```dax
// Budget attainment: what % of budget did we achieve
// 1.05 = achieved 105% of target
Budget Attainment =
    DIVIDE(
        [Total Sales],
        [Budget],
        0
    )
```

> If budget and sales don't share the same date dimension, use `TREATAS` to create a virtual relationship:
```dax
Budget (via TREATAS) =
    CALCULATE(
        SUM(fact_budget[BudgetAmount]),
        TREATAS(
            SUMMARIZE(dim_date, dim_date[Year], dim_date[Month]),
            fact_budget[Year],
            fact_budget[Month]
        )
    )
```

---

### 5. Customer Analytics

```dax
// How many unique customers bought something in the current filter context
Active Customers =
    DISTINCTCOUNT(fact_sales[CustomerKey])
```

```dax
// Average revenue generated per customer
Revenue per Customer =
    DIVIDE(
        [Total Sales],
        [Active Customers],
        0
    )
```

```dax
// New customers: those whose FIRST purchase falls within the current period
// FILTER keeps only customers where their earliest order date is
// within the dates currently visible on the report
New Customers =
    COUNTROWS(
        FILTER(
            VALUES(fact_sales[CustomerKey]),
            CALCULATE(
                MIN(fact_sales[DateKey]),
                ALL(dim_date)
            ) >= MIN(dim_date[DateKey])
            &&
            CALCULATE(
                MIN(fact_sales[DateKey]),
                ALL(dim_date)
            ) <= MAX(dim_date[DateKey])
        )
    )
```

---

### 6. Rankings & Top N

```dax
// Rank products by sales — useful for Top N visuals
Product Rank =
    IF(
        HASONEVALUE(dim_product[ProductName]),
        RANKX(
            ALL(dim_product[ProductName]),
            [Total Sales],
            ,
            DESC,
            DENSE
        )
    )
```

```dax
// Dynamic Top 5 product flag — use this in a visual filter
Is Top 5 Product =
    IF([Product Rank] <= 5, 1, 0)
```

---

## Suggested Visuals

Here's a recommended dashboard layout with 3 pages:

### Page 1: Executive Overview
| Visual | Metric | Notes |
|--------|--------|-------|
| **KPI Cards** (top row) | Total Sales, Profit, Margin %, Orders | Use conditional formatting (red/green) |
| **Line Chart** | Sales & Sales LY by Month | Show YoY trend |
| **Bar Chart** | Sales by Category | Horizontal, sorted desc |
| **Donut Chart** | Sales by Channel | Online vs Retail vs Outlet |
| **Table** | Top 5 Products | Sales, Qty, Margin |

### Page 2: Time & Budget Analysis
| Visual | Metric | Notes |
|--------|--------|-------|
| **Area Chart** | Sales YTD vs YTD LY | Cumulative comparison |
| **Waterfall Chart** | Sales MoM change | Show month-to-month deltas |
| **Clustered Bar** | Budget vs Actual by Month | Side by side |
| **Gauge** | Budget Attainment | Target = 100% |

### Page 3: Customer & Region
| Visual | Metric | Notes |
|--------|--------|-------|
| **Map** | Sales by Region | Bubble size = sales |
| **Bar Chart** | Sales by Customer Segment | Corporate vs SMB vs Consumer |
| **KPI** | Active Customers, New Customers | With MoM trend |
| **Scatter Plot** | Revenue per Customer vs Orders | Size = profit |

---

## How to Run

1. **Generate data** (optional — CSVs are already included):
   ```bash
   pip install pandas numpy
   python generate_data.py
   ```

2. **Open Power BI Desktop** and load the 6 CSV files from `data/`

3. **Set up relationships** as described in the [Relationships](#relationships) section

4. **Mark `dim_date` as Date Table** (Model View → right-click → Mark as Date Table)

5. **Create the `_Measures` table** and add the DAX measures above

6. **Build your visuals** following the [Suggested Visuals](#suggested-visuals) guide

---

## Tech Stack

- **Power BI Desktop** — Dashboards & data modeling
- **DAX** — Measures & calculations
- **Python / Pandas** — Data generation
- **Star Schema** — Data model pattern

---

## License

This project is open source and available under the [MIT License](LICENSE).
