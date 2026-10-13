import unittest
from pathlib import Path
from services.data_processor import DataProcessor
from services.sales_analyzer import SalesAnalyzer
from services.correlation_service import CorrelationService

class TestSalesAnalyzer(unittest.TestCase):
    def setUp(self):
        self.sample_csv = Path(__file__).resolve().parent.parent / 'data' / 'sample_sales_data.csv'
        self.df = DataProcessor.load_file(self.sample_csv)
        self.mapping = DataProcessor.auto_detect_columns(self.df)

    def test_sales_analysis_metrics(self):
        stats = SalesAnalyzer.analyze(self.df, self.mapping)
        self.assertGreater(stats['total_revenue'], 0)
        self.assertGreater(stats['total_units'], 0)
        self.assertGreater(stats['average_sale'], 0)
        self.assertIn('time_series', stats)
        self.assertGreater(len(stats['time_series']['labels']), 0)
        self.assertIn('product_summary', stats)
        self.assertGreater(len(stats['product_summary']), 0)

    def test_correlation_service(self):
        corr = CorrelationService.calculate_correlation(self.df)
        self.assertTrue(corr['has_correlation'])
        self.assertGreater(len(corr['columns']), 2)
        self.assertGreater(len(corr['top_pairs']), 0)
        self.assertIn('causation_notice', corr)

if __name__ == '__main__':
    unittest.main()
