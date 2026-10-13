import unittest
import pandas as pd
from pathlib import Path
from services.data_processor import DataProcessor

class TestDataProcessor(unittest.TestCase):
    def setUp(self):
        self.sample_csv = Path(__file__).resolve().parent.parent / 'data' / 'sample_sales_data.csv'
        self.sample_xlsx = Path(__file__).resolve().parent.parent / 'data' / 'sample_sales_data.xlsx'

    def test_load_csv_file(self):
        self.assertTrue(self.sample_csv.exists(), "Sample CSV dataset must exist")
        df = DataProcessor.load_file(self.sample_csv)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 50)
        self.assertIn('Sales_Revenue', df.columns)

    def test_load_excel_file(self):
        self.assertTrue(self.sample_xlsx.exists(), "Sample Excel dataset must exist")
        df = DataProcessor.load_file(self.sample_xlsx)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 50)

    def test_inspect_dataset(self):
        df = DataProcessor.load_file(self.sample_csv)
        quality = DataProcessor.inspect_dataset(df)
        self.assertEqual(quality['total_rows'], len(df))
        self.assertEqual(quality['total_cols'], len(df.columns))
        self.assertIn('columns', quality)
        self.assertIsInstance(quality['has_missing'], bool)

    def test_auto_detect_columns(self):
        df = DataProcessor.load_file(self.sample_csv)
        mapping = DataProcessor.auto_detect_columns(df)
        self.assertEqual(mapping['sales_col'], 'Sales_Revenue')
        self.assertEqual(mapping['date_col'], 'Date')
        self.assertEqual(mapping['units_col'], 'Units_Sold')
        self.assertEqual(mapping['product_col'], 'Product_Category')

    def test_preview_data(self):
        df = DataProcessor.load_file(self.sample_csv)
        preview = DataProcessor.get_preview_data(df, max_rows=10)
        self.assertIn('headers', preview)
        self.assertIn('rows', preview)
        self.assertEqual(len(preview['rows']), 10)

if __name__ == '__main__':
    unittest.main()
