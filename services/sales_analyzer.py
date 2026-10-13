import pandas as pd
import numpy as np

class SalesAnalyzer:
    @staticmethod
    def analyze(df, column_mapping):
        """
        Executes comprehensive, adaptive sales analysis based on detected or user-confirmed column mappings.
        Never fabricates missing metrics; calculates exactly what the data supports.
        """
        sales_col = column_mapping.get('sales_col')
        date_col = column_mapping.get('date_col')
        units_col = column_mapping.get('units_col')
        product_col = column_mapping.get('product_col')
        
        # Clean working copy
        work_df = df.copy()
        
        # 1. Sales / Revenue Metrics
        total_revenue = 0.0
        average_sale = 0.0
        median_sale = 0.0
        std_sale = 0.0
        min_sale = 0.0
        max_sale = 0.0
        
        if sales_col and sales_col in work_df.columns:
            work_df[sales_col] = pd.to_numeric(work_df[sales_col], errors='coerce')
            valid_sales = work_df[sales_col].dropna()
            if not valid_sales.empty:
                total_revenue = round(float(valid_sales.sum()), 2)
                average_sale = round(float(valid_sales.mean()), 2)
                median_sale = round(float(valid_sales.median()), 2)
                std_sale = round(float(valid_sales.std()), 2) if len(valid_sales) > 1 else 0.0
                min_sale = round(float(valid_sales.min()), 2)
                max_sale = round(float(valid_sales.max()), 2)

        # 2. Units Sold Metrics
        total_units = 0
        average_units = 0.0
        if units_col and units_col in work_df.columns:
            work_df[units_col] = pd.to_numeric(work_df[units_col], errors='coerce')
            valid_units = work_df[units_col].dropna()
            if not valid_units.empty:
                total_units = int(valid_units.sum())
                average_units = round(float(valid_units.mean()), 2)

        # 3. Date / Time Series Trends & Growth Calculation
        time_series = {
            'labels': [],
            'sales': [],
            'units': [],
            'granularity': 'none'
        }
        sales_growth_rate = None
        date_range_str = "No temporal column provided"
        
        if date_col and date_col in work_df.columns:
            try:
                work_df['_dt'] = pd.to_datetime(work_df[date_col], errors='coerce')
                valid_dt_df = work_df.dropna(subset=['_dt']).sort_values('_dt')
                
                if not valid_dt_df.empty:
                    min_dt = valid_dt_df['_dt'].min()
                    max_dt = valid_dt_df['_dt'].max()
                    date_range_str = f"{min_dt.strftime('%b %d, %Y')} – {max_dt.strftime('%b %d, %Y')}"
                    days_span = (max_dt - min_dt).days
                    
                    # Choose sensible grouping granularity
                    if days_span <= 45:
                        granularity = 'daily'
                        valid_dt_df['_period'] = valid_dt_df['_dt'].dt.strftime('%Y-%m-%d')
                    elif days_span <= 180:
                        granularity = 'weekly'
                        valid_dt_df['_period'] = valid_dt_df['_dt'].dt.to_period('W').apply(lambda r: r.start_time.strftime('%Y-%m-%d'))
                    else:
                        granularity = 'monthly'
                        valid_dt_df['_period'] = valid_dt_df['_dt'].dt.strftime('%Y-%m')
                    
                    agg_dict = {}
                    if sales_col and sales_col in valid_dt_df.columns:
                        agg_dict[sales_col] = 'sum'
                    if units_col and units_col in valid_dt_df.columns:
                        agg_dict[units_col] = 'sum'
                    
                    if agg_dict:
                        period_grp = valid_dt_df.groupby('_period', as_index=False).agg(agg_dict)
                        time_series['labels'] = period_grp['_period'].tolist()
                        time_series['granularity'] = granularity
                        
                        if sales_col and sales_col in period_grp.columns:
                            time_series['sales'] = [round(float(v), 2) for v in period_grp[sales_col]]
                        if units_col and units_col in period_grp.columns:
                            time_series['units'] = [int(v) for v in period_grp[units_col]]
                            
                        # Calculate Sales Growth Rate (first half vs second half of periods)
                        if sales_col and len(time_series['sales']) >= 4:
                            half = len(time_series['sales']) // 2
                            first_half_sum = sum(time_series['sales'][:half])
                            second_half_sum = sum(time_series['sales'][half:])
                            if first_half_sum > 0:
                                growth = ((second_half_sum - first_half_sum) / first_half_sum) * 100
                                sales_growth_rate = round(float(growth), 2)
            except Exception:
                pass

        # 4. Product / Category Breakdown
        product_summary = []
        if product_col and product_col in work_df.columns:
            prod_agg = {}
            if sales_col and sales_col in work_df.columns:
                prod_agg[sales_col] = 'sum'
            if units_col and units_col in work_df.columns:
                prod_agg[units_col] = 'sum'
            
            if prod_agg:
                try:
                    p_grp = work_df.groupby(product_col, as_index=False).agg(prod_agg)
                    # Sort by sales descending if available
                    sort_key = sales_col if sales_col in p_grp.columns else (units_col if units_col in p_grp.columns else None)
                    if sort_key:
                        p_grp = p_grp.sort_values(sort_key, ascending=False)
                    
                    for _, row in p_grp.head(15).iterrows():
                        p_sales = round(float(row[sales_col]), 2) if sales_col and sales_col in row else 0.0
                        p_units = int(row[units_col]) if units_col and units_col in row else 0
                        pct = round((p_sales / total_revenue * 100), 2) if total_revenue > 0 else 0.0
                        product_summary.append({
                            'product': str(row[product_col]),
                            'sales': p_sales,
                            'units': p_units,
                            'percentage': pct
                        })
                except Exception:
                    pass

        # 5. Descriptive Statistics for All Numeric Columns
        numeric_cols = [c for c in work_df.select_dtypes(include=[np.number]).columns if not str(c).startswith('_')]
        descriptive_stats = {}
        for col in numeric_cols:
            s = work_df[col].dropna()
            if not s.empty:
                descriptive_stats[col] = {
                    'count': int(s.count()),
                    'mean': round(float(s.mean()), 2),
                    'std': round(float(s.std()), 2) if len(s) > 1 else 0.0,
                    'min': round(float(s.min()), 2),
                    'p25': round(float(s.quantile(0.25)), 2),
                    'median': round(float(s.median()), 2),
                    'p75': round(float(s.quantile(0.75)), 2),
                    'max': round(float(s.max()), 2)
                }

        return {
            'total_revenue': total_revenue,
            'total_units': total_units,
            'average_sale': average_sale,
            'median_sale': median_sale,
            'std_sale': std_sale,
            'min_sale': min_sale,
            'max_sale': max_sale,
            'average_units': average_units,
            'sales_growth_rate': sales_growth_rate,
            'date_range_str': date_range_str,
            'time_series': time_series,
            'product_summary': product_summary,
            'descriptive_stats': descriptive_stats,
            'numeric_columns': numeric_cols
        }
