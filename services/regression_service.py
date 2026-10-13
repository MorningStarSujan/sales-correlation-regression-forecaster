import math
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

class RegressionService:
    @staticmethod
    def train_linear_regression(df, target_col, predictor_cols, split_type='chronological', test_size=0.2, date_col=None):
        """
        Trains an Ordinary Least Squares Linear Regression model using Scikit-learn.
        Ensures strict train/test splitting to prevent data leakage.
        Calculates R², MAE, RMSE, coefficients, actual vs predicted, and residuals.
        """
        if not target_col or target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found in dataset.")
            
        if not predictor_cols or len(predictor_cols) == 0:
            raise ValueError("At least one predictor variable must be selected.")
            
        for col in predictor_cols:
            if col not in df.columns:
                raise ValueError(f"Predictor column '{col}' not found in dataset.")
                
        # Prepare clean data subset
        needed_cols = [target_col] + list(predictor_cols)
        if date_col and date_col in df.columns and split_type == 'chronological':
            needed_cols.append(date_col)
            
        clean_df = df[needed_cols].copy()
        
        # Coerce numeric
        clean_df[target_col] = pd.to_numeric(clean_df[target_col], errors='coerce')
        for col in predictor_cols:
            clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce')
            
        initial_count = len(clean_df)
        clean_df = clean_df.dropna()
        dropped_count = initial_count - len(clean_df)
        
        if len(clean_df) < 5:
            raise ValueError(f"Insufficient valid data ({len(clean_df)} complete rows). At least 5 rows are required.")
            
        # Chronological ordering if specified
        if split_type == 'chronological':
            if date_col and date_col in clean_df.columns:
                try:
                    clean_df['_sort_dt'] = pd.to_datetime(clean_df[date_col], errors='coerce')
                    clean_df = clean_df.sort_values('_sort_dt').drop(columns=['_sort_dt'])
                except Exception:
                    pass
            # Chronological split: test is the latest portion of records
            split_idx = int(len(clean_df) * (1.0 - test_size))
            split_idx = max(2, min(split_idx, len(clean_df) - 1))
            
            train_df = clean_df.iloc[:split_idx]
            test_df = clean_df.iloc[split_idx:]
            
            X_train = train_df[predictor_cols]
            y_train = train_df[target_col]
            X_test = test_df[predictor_cols]
            y_test = test_df[target_col]
        else:
            # Random split with fixed seed for academic reproducibility
            X = clean_df[predictor_cols]
            y = clean_df[target_col]
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, shuffle=True
            )
            
        # Fit Linear Regression on training data strictly
        model = LinearRegression(fit_intercept=True)
        model.fit(X_train, y_train)
        
        # Predict on test set
        y_test_pred = model.predict(X_test)
        
        # Predict on entire set for comprehensive visual comparison
        y_all_pred = model.predict(clean_df[predictor_cols])
        
        # Evaluation Metrics on Test Set
        r2 = float(r2_score(y_test, y_test_pred))
        mae = float(mean_absolute_error(y_test, y_test_pred))
        mse = float(mean_squared_error(y_test, y_test_pred))
        rmse = float(math.sqrt(mse))
        
        # Training R² for overfitting diagnosis
        y_train_pred = model.predict(X_train)
        r2_train = float(r2_score(y_train, y_train_pred))
        
        # Coefficients
        coefficients = {}
        for feature, coef in zip(predictor_cols, model.coef_):
            coefficients[feature] = round(float(coef), 4)
            
        intercept = round(float(model.intercept_), 4)
        
        # Formulate mathematical regression equation
        eq_parts = [f"{intercept:+.4f}"]
        for feat, coef in coefficients.items():
            eq_parts.append(f"{coef:+.4f} × [{feat}]")
        equation_str = f"Estimated {target_col} = " + " ".join(eq_parts)
        
        # Actual vs Predicted comparison data (sample up to 60 points for charts)
        comparison_points = []
        residuals_list = []
        
        test_indices = set(X_test.index)
        
        for idx in clean_df.index:
            actual = float(clean_df.loc[idx, target_col])
            predicted = float(y_all_pred[clean_df.index.get_loc(idx)])
            resid = actual - predicted
            is_test = idx in test_indices
            
            row_label = str(clean_df.loc[idx, date_col]) if (date_col and date_col in clean_df.columns) else f"Row {idx + 1}"
            
            comparison_points.append({
                'label': row_label,
                'actual': round(actual, 2),
                'predicted': round(predicted, 2),
                'residual': round(resid, 2),
                'is_test': is_test
            })
            residuals_list.append(round(resid, 2))
            
        # Summary description
        if r2 >= 0.8:
            fit_quality = "High explanatory power"
        elif r2 >= 0.5:
            fit_quality = "Moderate explanatory power"
        elif r2 >= 0.2:
            fit_quality = "Weak explanatory power"
        else:
            fit_quality = "Poor predictive fit (non-linear or missing key drivers)"
            
        return {
            'target_variable': target_col,
            'predictor_variables': predictor_cols,
            'split_type': split_type,
            'test_size': test_size,
            'train_rows': len(X_train),
            'test_rows': len(X_test),
            'dropped_null_rows': dropped_count,
            'r2_score': round(r2, 4),
            'r2_train': round(r2_train, 4),
            'mae': round(mae, 2),
            'rmse': round(rmse, 2),
            'coefficients': coefficients,
            'intercept': intercept,
            'equation': equation_str,
            'fit_quality': fit_quality,
            'comparison_points': comparison_points,
            'residuals': residuals_list[:100]
        }

    @staticmethod
    def predict_scenario(coefficients, intercept, input_values):
        """
        Calculates deterministic linear prediction for user-provided scenario inputs:
        y = intercept + sum(coef_i * x_i)
        """
        predicted = float(intercept)
        contributions = {}
        
        for feat, val in input_values.items():
            coef = coefficients.get(feat, 0.0)
            contrib = float(val) * coef
            contributions[feat] = round(contrib, 2)
            predicted += contrib
            
        return {
            'predicted_value': round(predicted, 2),
            'intercept': intercept,
            'contributions': contributions
        }
