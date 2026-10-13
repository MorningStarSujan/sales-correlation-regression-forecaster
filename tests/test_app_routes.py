import unittest
import json
from app import create_app
from config import Config

class TestAppRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_dashboard_route(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Sales Forecaster', res.data)

    def test_load_sample_dataset_and_full_workflow(self):
        # 1. Load sample data
        res_sample = self.client.post('/api/load-sample')
        self.assertEqual(res_sample.status_code, 200)
        sample_json = json.loads(res_sample.data)
        self.assertTrue(sample_json['success'])
        analysis_id = sample_json['analysis_id']

        # 2. View Analysis
        res_analysis = self.client.get(f'/analysis/{analysis_id}')
        self.assertEqual(res_analysis.status_code, 200)
        self.assertIn(b'Correlation', res_analysis.data)

        # 3. Train Regression Model
        train_payload = {
            'analysis_id': analysis_id,
            'target_variable': 'Sales_Revenue',
            'predictor_variables': ['Marketing_Spend', 'Website_Traffic', 'Discount_Percent'],
            'split_type': 'chronological',
            'test_size': 0.2
        }
        res_train = self.client.post(
            '/api/regression/train',
            data=json.dumps(train_payload),
            content_type='application/json'
        )
        self.assertEqual(res_train.status_code, 200)
        train_json = json.loads(res_train.data)
        self.assertTrue(train_json['success'])
        model_id = train_json['model_id']
        self.assertIn('r2_score', train_json)

        # 4. Run Scenario Forecast
        scen_payload = {
            'model_id': model_id,
            'analysis_id': analysis_id,
            'inputs': {
                'Marketing_Spend': 3000.0,
                'Website_Traffic': 13500.0,
                'Discount_Percent': 5.0
            }
        }
        res_scen = self.client.post(
            '/api/forecast/scenario',
            data=json.dumps(scen_payload),
            content_type='application/json'
        )
        self.assertEqual(res_scen.status_code, 200)
        scen_json = json.loads(res_scen.data)
        self.assertTrue(scen_json['success'])
        self.assertGreater(scen_json['predicted_value'], 0)

        # 5. Export PDF
        res_pdf = self.client.get(f'/export/pdf/{analysis_id}')
        self.assertEqual(res_pdf.status_code, 200)
        self.assertEqual(res_pdf.content_type, 'application/pdf')
        self.assertTrue(res_pdf.data.startswith(b'%PDF'))

        # 6. Export CSV
        res_csv = self.client.get(f'/export/csv/{analysis_id}')
        self.assertEqual(res_csv.status_code, 200)
        self.assertIn('text/csv', res_csv.content_type)
        self.assertIn(b'SALES CORRELATION & REGRESSION FORECASTER', res_csv.data)

if __name__ == '__main__':
    unittest.main()
