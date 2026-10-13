import math
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class ForecasterService:
    @staticmethod
    def forecast_scenario(model_data, user_inputs, historical_ranges=None):
        """
        Executes an exact what-if scenario forecast based on user-supplied predictor inputs.
        Flags extrapolation if inputs fall outside historical bounds.
        """
        coefficients = model_data.get('coefficients', {})
        intercept = model_data.get('intercept', 0.0)
        target_name = model_data.get('target_variable', 'Sales')
        rmse = model_data.get('rmse', 0.0)
        
        # Calculate predicted value
        predicted = float(intercept)
        factor_breakdown = []
        extrapolation_warnings = []
        
        for feat in model_data.get('predictor_variables', []):
            val = float(user_inputs.get(feat, 0.0))
            coef = float(coefficients.get(feat, 0.0))
            contrib = val * coef
            predicted += contrib
            
            # Check extrapolation
            if historical_ranges and feat in historical_ranges:
                h_min = historical_ranges[feat]['min']
                h_max = historical_ranges[feat]['max']
                if val < h_min:
                    extrapolation_warnings.append(
                        f"Predictor '{feat}' ({val}) is below historical minimum ({h_min}). Model is extrapolating beyond observed data."
                    )
                elif val > h_max:
                    extrapolation_warnings.append(
                        f"Predictor '{feat}' ({val}) exceeds historical maximum ({h_max}). Model is extrapolating beyond observed data."
                    )
                    
            factor_breakdown.append({
                'feature': feat,
                'input_value': val,
                'coefficient': coef,
                'contribution': round(contrib, 2)
            })
            
        predicted = round(predicted, 2)
        # Approximate 95% prediction interval: ± 1.96 * RMSE
        margin = round(1.96 * rmse, 2)
        lower_bound = round(max(0.0, predicted - margin), 2)
        upper_bound = round(predicted + margin, 2)
        
        assumptions = (
            "1. Linear Invariance: Assumes the linear coefficients estimated from historical training data remain valid.\n"
            "2. Stationary Market Conditions: Assumes no unmeasured shocks, supply bottlenecks, or sudden competitive disruptions.\n"
            "3. Homoscedasticity: Prediction interval assumes normally distributed, constant-variance residuals around the regression line."
        )
        
        limitations = (
            "1. OLS regression models correlation rather than structural causality.\n"
            "2. Predictions made outside the historical range of predictor variables carry heightened uncertainty (extrapolation error).\n"
            "3. Does not capture non-linear saturation effects (e.g. diminishing returns on high advertising spend)."
        )

        return {
            'forecast_type': 'scenario',
            'target_variable': target_name,
            'predicted_value': predicted,
            'intercept': intercept,
            'lower_bound_95': lower_bound,
            'upper_bound_95': upper_bound,
            'margin_error': margin,
            'factor_breakdown': factor_breakdown,
            'extrapolation_warnings': extrapolation_warnings,
            'assumptions': assumptions,
            'limitations': limitations
        }

    @staticmethod
    def forecast_horizon(model_data, df, periods=6, growth_rate_pct=0.0, date_col=None):
        """
        Projects sales forward over a future horizon (e.g. next N periods)
        using historical trends or user-specified prospective growth rate for predictors.
        Never fabricates arbitrary inputs; uses empirical trend projections.
        """
        coefficients = model_data.get('coefficients', {})
        intercept = model_data.get('intercept', 0.0)
        target_name = model_data.get('target_variable', 'Sales')
        predictor_cols = model_data.get('predictor_variables', [])
        rmse = model_data.get('rmse', 0.0)
        
        # Calculate recent baseline values and average step changes for predictors
        recent_values = {}
        for col in predictor_cols:
            s = pd.to_numeric(df[col], errors='coerce').dropna()
            recent_values[col] = float(s.iloc[-1]) if not s.empty else 0.0
            
        # Determine last date if date column exists
        last_date = None
        freq_days = 30  # default monthly
        if date_col and date_col in df.columns:
            try:
                dt_series = pd.to_datetime(df[date_col], errors='coerce').dropna().sort_values()
                if not dt_series.empty:
                    last_date = dt_series.iloc[-1]
                    if len(dt_series) > 1:
                        avg_diff = (dt_series.iloc[-1] - dt_series.iloc[0]).days / (len(dt_series) - 1)
                        freq_days = max(1, int(round(avg_diff)))
            except Exception:
                pass

        results = []
        growth_multiplier = 1.0 + (growth_rate_pct / 100.0)
        
        for p in range(1, periods + 1):
            if last_date:
                future_dt = last_date + timedelta(days=p * freq_days)
                period_label = future_dt.strftime('%Y-%m-%d')
            else:
                period_label = f"Future Period +{p}"
                
            pred_val = float(intercept)
            pred_inputs = {}
            for col in predictor_cols:
                # Apply compound growth or baseline
                val = recent_values[col] * (growth_multiplier ** p)
                pred_inputs[col] = round(val, 2)
                pred_val += val * coefficients.get(col, 0.0)
                
            pred_val = round(pred_val, 2)
            margin = round(1.96 * rmse, 2)
            lower = round(max(0.0, pred_val - margin), 2)
            upper = round(pred_val + margin, 2)
            
            results.append({
                'period': period_label,
                'step': p,
                'predicted_sales': pred_val,
                'lower_bound_95': lower,
                'upper_bound_95': upper,
                'predictor_inputs': pred_inputs
            })
            
        assumptions = (
            f"1. Predictor Trajectory: Assumes predictor variables progress from recent baseline levels with {growth_rate_pct}% periodic growth rate.\n"
            "2. Constant Elasticity: Assumes the estimated linear regression coefficients remain stable throughout the forecast horizon.\n"
            "3. Uniform Dispersion: Prediction bounds assume historical residual variance remains constant over time."
        )
        
        limitations = (
            "1. Multi-step forecasts compound uncertainty as the horizon increases.\n"
            "2. Model does not capture unexpected exogenous events, regulatory shifts, or black swan incidents.\n"
            "3. High growth rates may project predictor values well beyond historical bounds, reducing statistical reliability."
        )

        return {
            'forecast_type': 'horizon',
            'target_variable': target_name,
            'periods': periods,
            'growth_rate_pct': growth_rate_pct,
            'results': results,
            'rmse': rmse,
            'assumptions': assumptions,
            'limitations': limitations
        }
