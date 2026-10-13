import pandas as pd
import numpy as np

class CorrelationService:
    @staticmethod
    def calculate_correlation(df, selected_columns=None):
        """
        Calculates Pearson correlation matrix for suitable numerical variables.
        Generates factual interpretations and emphasizes correlation vs causation.
        """
        # Filter for numeric columns
        numeric_df = df.select_dtypes(include=[np.number]).copy()
        
        # Exclude temporary or non-informative columns (e.g. IDs, indices with constant variance)
        valid_cols = []
        for col in numeric_df.columns:
            if selected_columns and col not in selected_columns:
                continue
            # Must have non-zero variance and at least 3 distinct values
            s = numeric_df[col].dropna()
            if len(s) >= 3 and s.std() > 1e-9 and s.nunique() > 1:
                valid_cols.append(col)
                
        if len(valid_cols) < 2:
            return {
                'has_correlation': False,
                'message': 'At least two numerical variables with non-zero variation are required to calculate correlation.',
                'columns': valid_cols,
                'matrix': [],
                'pairs': [],
                'insights': []
            }

        corr_matrix = numeric_df[valid_cols].corr(method='pearson')
        
        # Convert to 2D list with rounded values
        matrix_data = []
        for row_col in valid_cols:
            row_vals = []
            for col_col in valid_cols:
                val = corr_matrix.loc[row_col, col_col]
                row_vals.append(round(float(val), 3) if not np.isnan(val) else 0.0)
            matrix_data.append(row_vals)
            
        # Extract pairs (upper triangle, excluding diagonal)
        pairs = []
        insights = []
        for i in range(len(valid_cols)):
            for j in range(i + 1, len(valid_cols)):
                c1 = valid_cols[i]
                c2 = valid_cols[j]
                r_val = corr_matrix.loc[c1, c2]
                if np.isnan(r_val):
                    continue
                r_rounded = round(float(r_val), 3)
                
                # Determine strength and direction
                abs_r = abs(r_rounded)
                if abs_r >= 0.7:
                    strength = 'Strong'
                elif abs_r >= 0.4:
                    strength = 'Moderate'
                elif abs_r >= 0.2:
                    strength = 'Weak'
                else:
                    strength = 'Negligible'
                    
                direction = 'Positive' if r_rounded > 0 else ('Negative' if r_rounded < 0 else 'None')
                
                # Factual interpretation
                if abs_r < 0.2:
                    interp = f"There is virtually no linear relationship between '{c1}' and '{c2}' (r = {r_rounded})."
                elif r_rounded > 0:
                    interp = f"As '{c1}' increases, '{c2}' tends to increase correspondingly ({strength.lower()} linear association, r = {r_rounded})."
                else:
                    interp = f"As '{c1}' increases, '{c2}' tends to decrease ({strength.lower()} inverse association, r = {r_rounded})."
                    
                pairs.append({
                    'var1': c1,
                    'var2': c2,
                    'correlation': r_rounded,
                    'abs_correlation': abs_r,
                    'strength': strength,
                    'direction': direction,
                    'interpretation': interp
                })

        # Sort pairs by absolute correlation descending
        pairs.sort(key=lambda x: x['abs_correlation'], reverse=True)
        
        # Generate 3-5 top factual insights
        for p in pairs[:5]:
            insights.append(p['interpretation'])
            
        causation_notice = (
            "Critical Statistical Principle: Correlation does NOT imply causation. "
            "A strong statistical correlation between two variables demonstrates mutual co-movement, "
            "but does not prove that changes in one variable cause changes in the other. External "
            "market factors, customer seasonality, or unobserved variables may drive both."
        )

        return {
            'has_correlation': True,
            'columns': valid_cols,
            'matrix': matrix_data,
            'pairs': pairs,
            'top_pairs': pairs[:8],
            'insights': insights,
            'causation_notice': causation_notice
        }
