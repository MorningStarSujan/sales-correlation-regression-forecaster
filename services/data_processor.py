import re
from pathlib import Path
import pandas as pd
import numpy as np

class DataProcessor:
    @staticmethod
    def load_file(file_path):
        """
        Loads CSV or Excel file safely with encoding fallbacks and delimiter detection.
        Returns a pandas DataFrame.
        """
        path = Path(file_path)
        ext = path.suffix.lower()
        
        if ext == '.csv':
            # Try utf-8 first, fallback to latin1 or cp1252
            encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
            last_err = None
            for enc in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=enc, sep=None, engine='python')
                    return df
                except Exception as e:
                    last_err = e
            # Try standard comma
            try:
                return pd.read_csv(file_path, encoding='latin1')
            except Exception:
                raise ValueError(f"Failed to read CSV file: {last_err}")
                
        elif ext in ['.xlsx', '.xls']:
            try:
                return pd.read_excel(file_path)
            except Exception as e:
                raise ValueError(f"Failed to read Excel file: {e}")
        else:
            raise ValueError(f"Unsupported file format '{ext}'. Allowed: .csv, .xlsx, .xls")

    @staticmethod
    def inspect_dataset(df):
        """
        Performs thorough automated data quality inspection and schema analysis.
        """
        total_rows = len(df)
        total_cols = len(df.columns)
        
        # Duplicates
        duplicate_rows = int(df.duplicated().sum())
        
        # Missing values and column details
        columns_info = []
        for col in df.columns:
            missing_count = int(df[col].isna().sum())
            missing_pct = round((missing_count / total_rows * 100), 2) if total_rows > 0 else 0
            unique_count = int(df[col].nunique(dropna=True))
            
            # Detect data type
            raw_dtype = str(df[col].dtype)
            detected_type = 'text'
            
            if pd.api.types.is_numeric_dtype(df[col]):
                detected_type = 'numeric'
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                detected_type = 'datetime'
            else:
                # Check if it could be a date formatted as string
                sample_non_null = df[col].dropna().astype(str).head(20)
                date_matches = 0
                for val in sample_non_null:
                    # Match YYYY-MM-DD or MM/DD/YYYY or DD-MM-YYYY
                    if re.match(r'^\d{4}[-/.]\d{1,2}[-/.]\d{1,2}', val) or re.match(r'^\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}', val):
                        date_matches += 1
                if len(sample_non_null) > 0 and (date_matches / len(sample_non_null)) >= 0.7:
                    detected_type = 'datetime'
            
            # Sample values (up to 3 distinct non-null)
            sample_vals = [str(x) for x in df[col].dropna().unique()[:3]]
            
            columns_info.append({
                'name': str(col),
                'type': detected_type,
                'raw_dtype': raw_dtype,
                'missing_count': missing_count,
                'missing_pct': missing_pct,
                'unique_count': unique_count,
                'sample_values': sample_vals
            })
            
        data_quality = {
            'total_rows': total_rows,
            'total_cols': total_cols,
            'duplicate_rows': duplicate_rows,
            'duplicate_pct': round((duplicate_rows / total_rows * 100), 2) if total_rows > 0 else 0,
            'columns': columns_info,
            'has_missing': any(c['missing_count'] > 0 for c in columns_info),
            'has_duplicates': duplicate_rows > 0
        }
        
        return data_quality

    @staticmethod
    def auto_detect_columns(df):
        """
        Smart heuristic detection of common sales-related columns:
        - date_col: Date/time
        - sales_col: Revenue / Total Sales / Amount
        - units_col: Quantity / Units sold
        - product_col: Category / Item / Product Name
        - unit_price_col: Price / Unit Price
        """
        mapping = {
            'date_col': None,
            'sales_col': None,
            'units_col': None,
            'product_col': None,
            'unit_price_col': None
        }
        
        col_names_lower = {str(c).lower().strip(): c for c in df.columns}
        
        # 1. Date Detection
        date_patterns = ['date', 'order_date', 'sale_date', 'transaction_date', 'day', 'timestamp', 'period', 'month']
        for p in date_patterns:
            for cl, orig in col_names_lower.items():
                if p == cl or p in cl:
                    mapping['date_col'] = orig
                    break
            if mapping['date_col']:
                break
        
        # If not found by name, try detecting by datetime type
        if not mapping['date_col']:
            for c in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[c]):
                    mapping['date_col'] = c
                    break

        # 2. Sales / Revenue Detection (must be numeric or convertible)
        sales_patterns = ['sales_revenue', 'revenue', 'total_sales', 'sales', 'sales_amount', 'amount', 'total_amount', 'turnover', 'gross_sales']
        for p in sales_patterns:
            for cl, orig in col_names_lower.items():
                if cl == p or p in cl:
                    if pd.api.types.is_numeric_dtype(df[orig]):
                        mapping['sales_col'] = orig
                        break
            if mapping['sales_col']:
                break

        # 3. Units / Quantity Detection
        unit_patterns = ['units_sold', 'units', 'quantity', 'qty', 'volume', 'units_ordered', 'count']
        for p in unit_patterns:
            for cl, orig in col_names_lower.items():
                if cl == p or p in cl:
                    if pd.api.types.is_numeric_dtype(df[orig]) and orig != mapping.get('sales_col'):
                        mapping['units_col'] = orig
                        break
            if mapping['units_col']:
                break

        # 4. Product / Category Detection
        prod_patterns = ['product_category', 'category', 'product_name', 'product', 'item_name', 'item', 'sku', 'department']
        for p in prod_patterns:
            for cl, orig in col_names_lower.items():
                if cl == p or p in cl:
                    mapping['product_col'] = orig
                    break
            if mapping['product_col']:
                break

        # 5. Unit Price Detection
        price_patterns = ['unit_price', 'price', 'unit_cost', 'cost_per_unit', 'item_price']
        for p in price_patterns:
            for cl, orig in col_names_lower.items():
                if cl == p or p in cl:
                    if pd.api.types.is_numeric_dtype(df[orig]) and orig not in [mapping.get('sales_col'), mapping.get('units_col')]:
                        mapping['unit_price_col'] = orig
                        break
            if mapping['unit_price_col']:
                break

        return mapping

    @staticmethod
    def get_preview_data(df, max_rows=15):
        """
        Returns JSON-safe preview records and column headers.
        """
        preview_df = df.head(max_rows).copy()
        # Format datetimes
        for col in preview_df.columns:
            if pd.api.types.is_datetime64_any_dtype(preview_df[col]):
                preview_df[col] = preview_df[col].dt.strftime('%Y-%m-%d')
            else:
                preview_df[col] = preview_df[col].fillna('')
                
        return {
            'headers': list(df.columns),
            'rows': preview_df.values.tolist(),
            'total_rows': len(df)
        }
