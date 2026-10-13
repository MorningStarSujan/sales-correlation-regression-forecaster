import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

def generate_sample_sales():
    np.random.seed(42)
    start_date = datetime(2024, 1, 1)
    n_days = 180  # 6 months of daily data
    
    categories = ['Electronics', 'Home Appliances', 'Office Supplies', 'Accessories', 'Software']
    regions = ['North America', 'Europe', 'Asia Pacific', 'Latin America']
    
    rows = []
    
    for i in range(n_days):
        current_date = start_date + timedelta(days=i)
        # Category cycle or random
        cat = categories[i % len(categories)]
        region = regions[(i // 3) % len(regions)]
        
        # Base pricing by category
        price_bases = {
            'Electronics': 450.0,
            'Home Appliances': 320.0,
            'Office Supplies': 85.0,
            'Accessories': 45.0,
            'Software': 150.0
        }
        
        base_price = price_bases[cat]
        unit_price = round(float(np.random.normal(base_price, base_price * 0.08)), 2)
        unit_price = max(15.0, unit_price)
        
        # Seasonality / trend: slight upward trend over the half year
        trend_factor = 1.0 + (i / n_days) * 0.25
        weekend_boost = 1.2 if current_date.weekday() >= 5 else 1.0
        
        # Marketing Spend between $400 and $6000
        marketing_spend = round(float(np.random.uniform(500, 5000) * trend_factor), 2)
        
        # Website traffic correlated with marketing spend
        website_traffic = int(np.random.normal(marketing_spend * 4.5, 600))
        website_traffic = max(800, website_traffic)
        
        # Discount percent (0 to 25%)
        discount_percent = round(float(np.random.choice([0, 5, 10, 15, 20], p=[0.3, 0.25, 0.25, 0.15, 0.05])), 1)
        
        # Competitor price index (100 is parity)
        competitor_price_index = round(float(np.random.normal(100.0, 5.0)), 1)
        
        # Units sold driven by traffic, discount, marketing, and category
        cat_multipliers = {
            'Electronics': 0.025,
            'Home Appliances': 0.035,
            'Office Supplies': 0.12,
            'Accessories': 0.18,
            'Software': 0.08
        }
        
        base_units = (website_traffic * cat_multipliers[cat]) * (1.0 + discount_percent / 50.0) * weekend_boost
        units_sold = int(max(5, np.random.normal(base_units, base_units * 0.12)))
        
        # Sales Revenue = Units_Sold * Unit_Price * (1 - Discount/100)
        sales_revenue = round(float(units_sold * unit_price * (1.0 - discount_percent / 100.0)), 2)
        
        rows.append({
            'Date': current_date.strftime('%Y-%m-%d'),
            'Product_Category': cat,
            'Region': region,
            'Units_Sold': units_sold,
            'Unit_Price': unit_price,
            'Marketing_Spend': marketing_spend,
            'Website_Traffic': website_traffic,
            'Discount_Percent': discount_percent,
            'Competitor_Price_Index': competitor_price_index,
            'Sales_Revenue': sales_revenue
        })
        
    df = pd.DataFrame(rows)
    
    out_dir = Path(__file__).resolve().parent.parent / 'data'
    out_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = out_dir / 'sample_sales_data.csv'
    xlsx_path = out_dir / 'sample_sales_data.xlsx'
    
    df.to_csv(csv_path, index=False)
    df.to_excel(xlsx_path, index=False)
    print(f"Generated {len(df)} rows.")
    print(f"Saved CSV to: {csv_path}")
    print(f"Saved Excel to: {xlsx_path}")

if __name__ == '__main__':
    generate_sample_sales()
