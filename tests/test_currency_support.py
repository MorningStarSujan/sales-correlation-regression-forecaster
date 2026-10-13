import unittest
import json
from app import create_app
from services.currency_service import CurrencyService
from database.models import SettingsModel, AnalysisModel, RegressionModelDao, ForecastDao
from services.report_service import ReportService

class TestCurrencySupport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_currency_service_definitions(self):
        currencies = CurrencyService.get_supported_currencies()
        self.assertIn('USD', currencies)
        self.assertIn('EUR', currencies)
        self.assertIn('GBP', currencies)
        self.assertIn('JPY', currencies)
        self.assertIn('INR', currencies)
        self.assertIn('CAD', currencies)
        self.assertIn('AUD', currencies)
        self.assertIn('CHF', currencies)
        self.assertIn('SEK', currencies)

        self.assertEqual(CurrencyService.get_symbol('USD'), '$')
        self.assertEqual(CurrencyService.get_symbol('EUR'), '€')
        self.assertEqual(CurrencyService.get_symbol('GBP'), '£')
        self.assertEqual(CurrencyService.get_symbol('JPY'), '¥')
        self.assertEqual(CurrencyService.get_symbol('INR'), '₹')

    def test_currency_service_formatting(self):
        # USD
        self.assertEqual(CurrencyService.format(1234.56, 'USD'), '$1,234.56')
        self.assertEqual(CurrencyService.format(-1234.56, 'USD'), '-$1,234.56')
        self.assertEqual(CurrencyService.format(0, 'USD'), '$0.00')

        # EUR
        self.assertEqual(CurrencyService.format(1234.56, 'EUR'), '€1,234.56')
        self.assertEqual(CurrencyService.format(-1234.56, 'EUR'), '-€1,234.56')

        # GBP
        self.assertEqual(CurrencyService.format(1234.56, 'GBP'), '£1,234.56')

        # JPY
        self.assertEqual(CurrencyService.format(1234.56, 'JPY'), '¥1,234.56')

        # INR
        self.assertEqual(CurrencyService.format(1234.56, 'INR'), '₹1,234.56')

        # SEK (suffix)
        self.assertEqual(CurrencyService.format(1234.56, 'SEK'), '1,234.56 kr')

        # Short formatting for axes
        self.assertEqual(CurrencyService.format_short(15000, 'USD'), '$15k')
        self.assertEqual(CurrencyService.format_short(15000, 'EUR'), '€15k')
        self.assertEqual(CurrencyService.format_short(2500000, 'GBP'), '£2.5M')
        self.assertEqual(CurrencyService.format_short(15000, 'SEK'), '15k kr')

        # Invalid/None values
        self.assertEqual(CurrencyService.format(None, 'USD'), '$0.00')
        self.assertEqual(CurrencyService.format('invalid', 'EUR'), '€0.00')

    def test_currency_api_get_and_post(self):
        # 1. GET currency
        res = self.client.get('/api/currency')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertIn('currencies', data)
        self.assertIn('current_currency', data)

        # 2. POST currency to change to EUR
        res_post = self.client.post(
            '/api/currency',
            data=json.dumps({'currency': 'EUR'}),
            content_type='application/json'
        )
        self.assertEqual(res_post.status_code, 200)
        post_data = json.loads(res_post.data)
        self.assertTrue(post_data['success'])
        self.assertEqual(post_data['currency'], 'EUR')
        self.assertEqual(post_data['currency_info']['symbol'], '€')

        # Check cookie was set
        self.assertIn('selected_currency=EUR', res_post.headers.get('Set-Cookie', ''))

        # Check DB persistence
        self.assertEqual(SettingsModel.get('selected_currency'), 'EUR')

        # 3. POST invalid currency returns 400
        res_invalid = self.client.post(
            '/api/currency',
            data=json.dumps({'currency': 'XYZ'}),
            content_type='application/json'
        )
        self.assertEqual(res_invalid.status_code, 400)

        # Reset back to USD for subsequent tests
        self.client.post(
            '/api/currency',
            data=json.dumps({'currency': 'USD'}),
            content_type='application/json'
        )

    def test_currency_selector_only_on_analysis_page(self):
        # Load sample data to ensure an analysis exists
        self.client.post('/api/load-sample')

        # Currency selector MUST be present on Data Analysis page
        res_analysis = self.client.get('/analysis')
        # If redirected to /analysis/<id>
        if res_analysis.status_code in (301, 302):
            res_analysis = self.client.get(res_analysis.headers['Location'])
        self.assertEqual(res_analysis.status_code, 200)
        self.assertIn(b'id="currencySelector"', res_analysis.data)
        self.assertIn(b'class="currency-selector-wrapper"', res_analysis.data)

        # Currency selector MUST NOT be present on other pages
        pages_without_selector = [
            '/',
            '/upload',
            '/regression',
            '/forecasting',
            '/history',
            '/reports'
        ]

        for page in pages_without_selector:
            res = self.client.get(page, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertNotIn(
                b'id="currencySelector"',
                res.data,
                f"Page {page} should NOT contain currency selector dropdown"
            )

    def test_currency_symbol_propagation_across_application(self):
        # Set currency to EUR via cookie/API
        self.client.post('/api/currency', data=json.dumps({'currency': 'EUR'}), content_type='application/json')
        self.client.set_cookie('selected_currency', 'EUR')

        # 1. Dashboard
        res_dash = self.client.get('/')
        self.assertEqual(res_dash.status_code, 200)
        self.assertIn('€'.encode('utf-8'), res_dash.data)

        # 2. Analysis page
        res_anal = self.client.get('/analysis', follow_redirects=True)
        self.assertEqual(res_anal.status_code, 200)
        self.assertIn('€'.encode('utf-8'), res_anal.data)

        # 3. Reports page
        res_reports = self.client.get('/reports', follow_redirects=True)
        self.assertEqual(res_reports.status_code, 200)
        self.assertIn('€'.encode('utf-8'), res_reports.data)

        # 4. History page
        res_hist = self.client.get('/history')
        self.assertEqual(res_hist.status_code, 200)
        self.assertIn('€'.encode('utf-8'), res_hist.data)

        # Switch to GBP
        self.client.post('/api/currency', data=json.dumps({'currency': 'GBP'}), content_type='application/json')
        self.client.set_cookie('selected_currency', 'GBP')

        res_dash_gbp = self.client.get('/')
        self.assertIn('£'.encode('utf-8'), res_dash_gbp.data)

        # Switch to INR
        self.client.post('/api/currency', data=json.dumps({'currency': 'INR'}), content_type='application/json')
        self.client.set_cookie('selected_currency', 'INR')

        res_dash_inr = self.client.get('/')
        self.assertIn('₹'.encode('utf-8'), res_dash_inr.data)

        # Reset to USD
        self.client.post('/api/currency', data=json.dumps({'currency': 'USD'}), content_type='application/json')
        self.client.set_cookie('selected_currency', 'USD')

    def test_pdf_and_csv_export_with_currency(self):
        # Get active analysis
        latest = AnalysisModel.get_latest(limit=1)
        self.assertTrue(len(latest) > 0)
        analysis_id = latest[0]['id']

        # 1. Export PDF with EUR
        self.client.set_cookie('selected_currency', 'EUR')
        res_pdf = self.client.get(f'/export/pdf/{analysis_id}?currency=EUR')
        self.assertEqual(res_pdf.status_code, 200)
        self.assertEqual(res_pdf.content_type, 'application/pdf')
        self.assertTrue(res_pdf.data.startswith(b'%PDF'))

        # 2. Export CSV with EUR
        res_csv = self.client.get(f'/export/csv/{analysis_id}?currency=EUR')
        self.assertEqual(res_csv.status_code, 200)
        csv_text = res_csv.data.decode('utf-8-sig')
        self.assertIn('EUR', csv_text)
        self.assertIn('€', csv_text)
        self.assertIn('Value (EUR)', csv_text)

        # 3. Export CSV with JPY
        res_csv_jpy = self.client.get(f'/export/csv/{analysis_id}?currency=JPY')
        self.assertEqual(res_csv_jpy.status_code, 200)
        csv_text_jpy = res_csv_jpy.data.decode('utf-8-sig')
        self.assertIn('JPY', csv_text_jpy)
        self.assertIn('¥', csv_text_jpy)
        self.assertIn('Value (JPY)', csv_text_jpy)

    def test_no_silent_data_conversion(self):
        """
        Verify that underlying numbers/statistics remain identical regardless of currency selected.
        """
        latest = AnalysisModel.get_latest(limit=1)
        self.assertTrue(len(latest) > 0)
        analysis = latest[0]
        raw_rev = analysis['summary_stats']['total_revenue']

        # Formatting in USD, EUR, JPY
        formatted_usd = CurrencyService.format(raw_rev, 'USD')
        formatted_eur = CurrencyService.format(raw_rev, 'EUR')
        formatted_jpy = CurrencyService.format(raw_rev, 'JPY')

        # The numeric part (e.g. '1,500,000.00') must be exactly identical
        num_part_usd = formatted_usd.replace('$', '').strip()
        num_part_eur = formatted_eur.replace('€', '').strip()
        num_part_jpy = formatted_jpy.replace('¥', '').strip()

        self.assertEqual(num_part_usd, num_part_eur)
        self.assertEqual(num_part_usd, num_part_jpy)

if __name__ == '__main__':
    unittest.main()
