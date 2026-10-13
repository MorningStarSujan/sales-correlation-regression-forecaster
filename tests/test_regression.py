import unittest
from pathlib import Path
from services.data_processor import DataProcessor
from services.regression_service import RegressionService
from services.forecaster_service import ForecasterService

class TestRegressionAndForecasting(unittest.TestCase):
    def setUp(self):
        self.sample_csv = Path(__file__).resolve().parent.parent / 'data' / 'sample_sales_data.csv'
        self.df = DataProcessor.load_file(self.sample_csv)

    def test_train_linear_regression(self):
        target = 'Sales_Revenue'
        predictors = ['Marketing_Spend', 'Website_Traffic', 'Discount_Percent']
        
        results = RegressionService.train_linear_regression(
            df=self.df,
            target_col=target,
            predictor_cols=predictors,
            split_type='chronological',
            test_size=0.2,
            date_col='Date'
        )
        
        self.assertEqual(results['target_variable'], target)
        self.assertGreaterEqual(results['r2_score'], 0.5, "Model should explain significant variance")
        self.assertGreater(results['rmse'], 0)
        self.assertGreater(results['mae'], 0)
        self.assertIn('intercept', results)
        self.assertIn('coefficients', results)
        self.assertEqual(len(results['coefficients']), 3)

    def test_scenario_forecast(self):
        target = 'Sales_Revenue'
        predictors = ['Marketing_Spend', 'Website_Traffic']
        reg_res = RegressionService.train_linear_regression(
            df=self.df,
            target_col=target,
            predictor_cols=predictors,
            split_type='random',
            test_size=0.2
        )
        
        user_inputs = {'Marketing_Spend': 2500.0, 'Website_Traffic': 11000.0}
        fc_res = ForecasterService.forecast_scenario(reg_res, user_inputs)
        
        self.assertGreater(fc_res['predicted_value'], 0)
        self.assertLessEqual(fc_res['lower_bound_95'], fc_res['predicted_value'])
        self.assertGreaterEqual(fc_res['upper_bound_95'], fc_res['predicted_value'])
        self.assertIn('assumptions', fc_res)
        self.assertIn('limitations', fc_res)

    def test_horizon_forecast(self):
        target = 'Sales_Revenue'
        predictors = ['Marketing_Spend', 'Website_Traffic']
        reg_res = RegressionService.train_linear_regression(
            df=self.df,
            target_col=target,
            predictor_cols=predictors
        )
        
        horizon_res = ForecasterService.forecast_horizon(
            model_data=reg_res,
            df=self.df,
            periods=6,
            growth_rate_pct=2.0,
            date_col='Date'
        )
        
        self.assertEqual(len(horizon_res['results']), 6)
        self.assertGreater(horizon_res['results'][0]['predicted_sales'], 0)

if __name__ == '__main__':
    unittest.main()
