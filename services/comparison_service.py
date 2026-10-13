import pandas as pd
import numpy as np

class ComparisonService:
    @staticmethod
    def compare_analyses(analysis_a, analysis_b):
        """
        Compares two historical analyses/datasets.
        Evaluates schema overlap, date intervals, KPI differences, and generates comparability warnings.
        """
        stats_a = analysis_a.get('summary_stats', {})
        stats_b = analysis_b.get('summary_stats', {})
        
        mapping_a = analysis_a.get('column_mapping', {})
        mapping_b = analysis_b.get('column_mapping', {})
        
        # 1. KPI Comparison & Percentage Deltas
        rev_a = float(stats_a.get('total_revenue', 0.0))
        rev_b = float(stats_b.get('total_revenue', 0.0))
        rev_diff = rev_b - rev_a
        rev_pct = round((rev_diff / rev_a * 100), 2) if rev_a > 0 else None
        
        units_a = int(stats_a.get('total_units', 0))
        units_b = int(stats_b.get('total_units', 0))
        units_diff = units_b - units_a
        units_pct = round((units_diff / units_a * 100), 2) if units_a > 0 else None
        
        avg_a = float(stats_a.get('average_sale', 0.0))
        avg_b = float(stats_b.get('average_sale', 0.0))
        avg_diff = avg_b - avg_a
        avg_pct = round((avg_diff / avg_a * 100), 2) if avg_a > 0 else None
        
        rows_a = int(analysis_a.get('row_count', 0))
        rows_b = int(analysis_b.get('row_count', 0))
        rows_diff = rows_b - rows_a
        
        kpis = [
            {
                'metric': 'Total Revenue',
                'val_a': rev_a,
                'val_b': rev_b,
                'diff': round(rev_diff, 2),
                'pct_change': rev_pct,
                'format': 'currency'
            },
            {
                'metric': 'Units Sold',
                'val_a': units_a,
                'val_b': units_b,
                'diff': units_diff,
                'pct_change': units_pct,
                'format': 'number'
            },
            {
                'metric': 'Average Transaction Sale',
                'val_a': avg_a,
                'val_b': avg_b,
                'diff': round(avg_diff, 2),
                'pct_change': avg_pct,
                'format': 'currency'
            },
            {
                'metric': 'Record Count (Rows)',
                'val_a': rows_a,
                'val_b': rows_b,
                'diff': rows_diff,
                'pct_change': round((rows_diff / rows_a * 100), 2) if rows_a > 0 else None,
                'format': 'number'
            }
        ]
        
        # 2. Schema Differences
        num_cols_a = set(stats_a.get('numeric_columns', []))
        num_cols_b = set(stats_b.get('numeric_columns', []))
        
        shared_cols = sorted(list(num_cols_a.intersection(num_cols_b)))
        only_in_a = sorted(list(num_cols_a - num_cols_b))
        only_in_b = sorted(list(num_cols_b - num_cols_a))
        
        # 3. Date Range Comparison
        dates_a = stats_a.get('date_range_str', 'N/A')
        dates_b = stats_b.get('date_range_str', 'N/A')
        
        # 4. Warnings and Comparability Verdict
        warnings = []
        is_fully_compatible = True
        
        if mapping_a.get('sales_col') != mapping_b.get('sales_col'):
            warnings.append(
                f"Different revenue columns used: '{mapping_a.get('sales_col')}' vs '{mapping_b.get('sales_col')}'. "
                "Ensure both represent equivalent currency definitions."
            )
            is_fully_compatible = False
            
        if only_in_a:
            warnings.append(f"Variables present in Dataset A but missing in Dataset B: {', '.join(only_in_a)}.")
            is_fully_compatible = False
            
        if only_in_b:
            warnings.append(f"Variables present in Dataset B but missing in Dataset A: {', '.join(only_in_b)}.")
            is_fully_compatible = False
            
        if len(shared_cols) == 0:
            warnings.append("CRITICAL: The two datasets have zero shared numeric columns. Direct numerical comparison is not valid.")
            is_fully_compatible = False
            
        if dates_a != 'N/A' and dates_b != 'N/A' and dates_a != dates_b:
            warnings.append(f"Temporal interval discrepancy: Dataset A covers ({dates_a}) while Dataset B covers ({dates_b}).")
            
        return {
            'dataset_a_title': analysis_a.get('title'),
            'dataset_b_title': analysis_b.get('title'),
            'dataset_a_filename': analysis_a.get('dataset_filename'),
            'dataset_b_filename': analysis_b.get('dataset_filename'),
            'dates_a': dates_a,
            'dates_b': dates_b,
            'kpis': kpis,
            'shared_cols': shared_cols,
            'only_in_a': only_in_a,
            'only_in_b': only_in_b,
            'warnings': warnings,
            'is_fully_compatible': is_fully_compatible
        }
