"""
Sales Analytics - Data Generator
Generates realistic sales data with a star schema structure.
Run: python generate_data.py
Output: CSV files in ./data/
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)
os.makedirs("data", exist_ok=True)

# =============================================================
# 1. DIM_DATE - Calendar table (2022-01-01 to 2024-12-31)
# =============================================================
start_date = datetime(2022, 1, 1)
end_date = datetime(2024, 12, 31)
dates = pd.date_range(start_date, end_date, freq='D')

dim_date = pd.DataFrame({
    'DateKey': dates.strftime('%Y%m%d').astype(int),
    'Date': dates,
    'Year': dates.year,
    'Quarter': dates.quarter,
    'QuarterLabel': ['Q' + str(q) for q in dates.quarter],
    'Month': dates.month,
    'MonthName': dates.strftime('%B'),
    'MonthShort': dates.strftime('%b'),
    'Day': dates.day,
    'DayOfWeek': dates.dayofweek,
    'DayName': dates.strftime('%A'),
    'WeekNumber': dates.isocalendar().week.astype(int),
    'IsWeekend': dates.dayofweek.isin([5, 6]).astype(int),
    'YearMonth': dates.strftime('%Y-%m')
})

dim_date.to_csv('data/dim_date.csv', index=False)
print(f"dim_date: {len(dim_date)} rows")

# =============================================================
# 2. DIM_PRODUCT - Products with categories and subcategories
# =============================================================
product_data = {
    'Electronics': {
        'Laptops': [('Laptop Pro 15', 1299), ('Laptop Air 13', 999), ('Laptop Business 14', 1099)],
        'Phones': [('Smartphone X', 799), ('Smartphone Lite', 499), ('Smartphone Pro Max', 1199)],
        'Accessories': [('Wireless Mouse', 29), ('USB-C Hub', 49), ('Bluetooth Headphones', 89)],
    },
    'Office': {
        'Furniture': [('Standing Desk', 599), ('Ergonomic Chair', 449), ('Monitor Stand', 79)],
        'Supplies': [('Printer Paper (500)', 12), ('Ink Cartridge', 35), ('Whiteboard Markers', 8)],
    },
    'Software': {
        'Licenses': [('Office Suite Annual', 120), ('Antivirus 1-Year', 45), ('Cloud Storage Plan', 99)],
        'Services': [('IT Support Monthly', 199), ('Data Backup Service', 59), ('VPN Annual', 79)],
    }
}

products = []
pid = 1
for category, subcats in product_data.items():
    for subcat, items in subcats.items():
        for name, price in items:
            cost = round(price * np.random.uniform(0.4, 0.65), 2)
            products.append({
                'ProductKey': pid,
                'ProductName': name,
                'Category': category,
                'SubCategory': subcat,
                'UnitPrice': price,
                'UnitCost': cost,
            })
            pid += 1

dim_product = pd.DataFrame(products)
dim_product.to_csv('data/dim_product.csv', index=False)
print(f"dim_product: {len(dim_product)} rows")

# =============================================================
# 3. DIM_CUSTOMER - Customers with segments
# =============================================================
segments = ['Corporate', 'Small Business', 'Consumer', 'Government']
regions = {
    'North': ['New York', 'Boston', 'Chicago', 'Detroit'],
    'South': ['Miami', 'Houston', 'Atlanta', 'Dallas'],
    'West': ['Los Angeles', 'Seattle', 'San Francisco', 'Denver'],
    'East': ['Philadelphia', 'Washington DC', 'Charlotte', 'Pittsburgh']
}

customers = []
for cid in range(1, 201):
    segment = np.random.choice(segments, p=[0.3, 0.35, 0.25, 0.1])
    region = np.random.choice(list(regions.keys()))
    city = np.random.choice(regions[region])
    customers.append({
        'CustomerKey': cid,
        'CustomerName': f'Customer_{cid:04d}',
        'Segment': segment,
        'Region': region,
        'City': city,
    })

dim_customer = pd.DataFrame(customers)
dim_customer.to_csv('data/dim_customer.csv', index=False)
print(f"dim_customer: {len(dim_customer)} rows")

# =============================================================
# 4. DIM_STORE - Sales channels / stores
# =============================================================
stores = [
    {'StoreKey': 1, 'StoreName': 'Online Store', 'Channel': 'Online', 'Country': 'USA'},
    {'StoreKey': 2, 'StoreName': 'NYC Flagship', 'Channel': 'Retail', 'Country': 'USA'},
    {'StoreKey': 3, 'StoreName': 'LA Store', 'Channel': 'Retail', 'Country': 'USA'},
    {'StoreKey': 4, 'StoreName': 'Chicago Outlet', 'Channel': 'Outlet', 'Country': 'USA'},
    {'StoreKey': 5, 'StoreName': 'Partner Resellers', 'Channel': 'Wholesale', 'Country': 'USA'},
]

dim_store = pd.DataFrame(stores)
dim_store.to_csv('data/dim_store.csv', index=False)
print(f"dim_store: {len(dim_store)} rows")

# =============================================================
# 5. FACT_SALES - Sales transactions
# =============================================================
n_orders = 15000

# Generate order dates with seasonal patterns (more sales in Q4, less in Q1)
order_dates = []
for _ in range(n_orders):
    year = np.random.choice([2022, 2023, 2024], p=[0.25, 0.35, 0.40])
    month = np.random.choice(range(1, 13), p=[
        0.06, 0.06, 0.07, 0.07, 0.08, 0.08,
        0.08, 0.08, 0.09, 0.09, 0.11, 0.13
    ])
    max_day = 28 if month == 2 else 30 if month in [4, 6, 9, 11] else 31
    day = np.random.randint(1, max_day + 1)
    order_dates.append(datetime(year, month, day))

order_dates.sort()

# Build fact table
sales_records = []
order_id = 10000

for date in order_dates:
    order_id += 1
    n_lines = np.random.choice([1, 2, 3, 4], p=[0.45, 0.30, 0.15, 0.10])

    customer_id = np.random.randint(1, 201)
    store_id = np.random.choice([1, 2, 3, 4, 5], p=[0.40, 0.20, 0.15, 0.10, 0.15])
    products_in_order = np.random.choice(dim_product['ProductKey'].values, size=n_lines, replace=False)

    for prod_id in products_in_order:
        product = dim_product[dim_product['ProductKey'] == prod_id].iloc[0]
        quantity = np.random.randint(1, 8)

        # Random discount (most have none)
        discount_pct = np.random.choice([0, 0, 0, 0, 0.05, 0.10, 0.15, 0.20], p=[0.50, 0.15, 0.05, 0.05, 0.08, 0.08, 0.05, 0.04])

        unit_price = product['UnitPrice']
        unit_cost = product['UnitCost']
        gross_amount = round(unit_price * quantity, 2)
        discount_amount = round(gross_amount * discount_pct, 2)
        net_amount = round(gross_amount - discount_amount, 2)
        total_cost = round(unit_cost * quantity, 2)

        date_key = int(date.strftime('%Y%m%d'))

        sales_records.append({
            'OrderID': order_id,
            'OrderLineID': f'{order_id}-{prod_id}',
            'DateKey': date_key,
            'CustomerKey': customer_id,
            'ProductKey': prod_id,
            'StoreKey': store_id,
            'Quantity': quantity,
            'UnitPrice': unit_price,
            'UnitCost': unit_cost,
            'DiscountPct': discount_pct,
            'GrossAmount': gross_amount,
            'DiscountAmount': discount_amount,
            'NetAmount': net_amount,
            'TotalCost': total_cost,
        })

fact_sales = pd.DataFrame(sales_records)
fact_sales.to_csv('data/fact_sales.csv', index=False)
print(f"fact_sales: {len(fact_sales)} rows")

# =============================================================
# 6. FACT_BUDGET - Monthly budget targets
# =============================================================
budget_records = []
for year in [2022, 2023, 2024]:
    yearly_sales = fact_sales[fact_sales['DateKey'] // 10000 == year]['NetAmount'].sum()
    for month in range(1, 13):
        # Budget = slightly above actual (growth target)
        month_weight = [0.06, 0.06, 0.07, 0.07, 0.08, 0.08, 0.08, 0.08, 0.09, 0.09, 0.11, 0.13][month - 1]
        budget_amount = round(yearly_sales * month_weight * np.random.uniform(1.02, 1.12), 2)
        budget_records.append({
            'Year': year,
            'Month': month,
            'BudgetAmount': budget_amount,
        })

fact_budget = pd.DataFrame(budget_records)
fact_budget.to_csv('data/fact_budget.csv', index=False)
print(f"fact_budget: {len(fact_budget)} rows")

print("\n--- All CSV files generated in ./data/ ---")
