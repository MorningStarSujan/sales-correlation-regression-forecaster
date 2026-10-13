import json
import uuid
from datetime import datetime
from database.db import get_db

class DatasetModel:
    @staticmethod
    def create(filename, stored_filename, file_path, file_type, file_size_bytes, 
               row_count, col_count, column_metadata, column_mapping, source='upload'):
        dataset_id = f"ds_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO datasets (
                    id, filename, stored_filename, file_path, file_type, 
                    file_size_bytes, row_count, col_count, column_metadata, 
                    column_mapping, created_at, status, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
            ''', (
                dataset_id, filename, stored_filename, str(file_path), file_type,
                file_size_bytes, row_count, col_count,
                json.dumps(column_metadata), json.dumps(column_mapping), now, source
            ))
        return dataset_id

    @staticmethod
    def get_by_id(dataset_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM datasets WHERE id = ? AND status = "active"', (dataset_id,))
            row = cursor.fetchone()
            if not row:
                return None
            data = dict(row)
            data['column_metadata'] = json.loads(data['column_metadata'])
            data['column_mapping'] = json.loads(data['column_mapping'])
            return data

    @staticmethod
    def update_mapping(dataset_id, column_mapping):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE datasets SET column_mapping = ? WHERE id = ?', 
                           (json.dumps(column_mapping), dataset_id))

    @staticmethod
    def get_all_active():
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM datasets WHERE status = "active" ORDER BY created_at DESC')
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item['column_metadata'] = json.loads(item['column_metadata'])
                item['column_mapping'] = json.loads(item['column_mapping'])
                results.append(item)
            return results

    @staticmethod
    def delete(dataset_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE datasets SET status = "deleted" WHERE id = ?', (dataset_id,))


class AnalysisModel:
    @staticmethod
    def create(dataset_id, title, description, summary_stats, correlation_results, data_quality_report):
        analysis_id = f"an_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO analyses (
                    id, dataset_id, title, description, summary_stats, 
                    correlation_results, data_quality_report, created_at, updated_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
            ''', (
                analysis_id, dataset_id, title, description or '',
                json.dumps(summary_stats), json.dumps(correlation_results),
                json.dumps(data_quality_report), now, now
            ))
        return analysis_id

    @staticmethod
    def get_by_id(analysis_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.*, d.filename as dataset_filename, d.file_path, d.row_count, d.col_count, d.column_mapping, d.source as dataset_source
                FROM analyses a
                JOIN datasets d ON a.dataset_id = d.id
                WHERE a.id = ? AND a.status = "active"
            ''', (analysis_id,))
            row = cursor.fetchone()
            if not row:
                return None
            data = dict(row)
            data['summary_stats'] = json.loads(data['summary_stats'])
            data['correlation_results'] = json.loads(data['correlation_results'])
            data['data_quality_report'] = json.loads(data['data_quality_report'])
            data['column_mapping'] = json.loads(data['column_mapping'])
            return data

    @staticmethod
    def get_latest(limit=5):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.id, a.dataset_id, a.title, a.description, a.created_at, a.summary_stats,
                       d.filename as dataset_filename, d.row_count, d.source as dataset_source
                FROM analyses a
                JOIN datasets d ON a.dataset_id = d.id
                WHERE a.status = "active"
                ORDER BY a.created_at DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                stats = json.loads(item['summary_stats'])
                item['summary_stats'] = stats
                item['total_revenue'] = stats.get('total_revenue', 0)
                item['total_units'] = stats.get('total_units', 0)
                item['average_sale'] = stats.get('average_sale', 0)
                item['sales_growth_rate'] = stats.get('sales_growth_rate')
                results.append(item)
            return results

    @staticmethod
    def get_all_active():
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.*, d.filename as dataset_filename, d.row_count, d.col_count, d.source as dataset_source
                FROM analyses a
                JOIN datasets d ON a.dataset_id = d.id
                WHERE a.status = "active"
                ORDER BY a.created_at DESC
            ''', ( ))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item['summary_stats'] = json.loads(item['summary_stats'])
                item['correlation_results'] = json.loads(item['correlation_results'])
                item['data_quality_report'] = json.loads(item['data_quality_report'])
                results.append(item)
            return results

    @staticmethod
    def rename(analysis_id, new_title):
        now = datetime.now().isoformat()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE analyses 
                SET title = ?, updated_at = ?
                WHERE id = ? AND status = "active"
            ''', (new_title.strip(), now, analysis_id))

    @staticmethod
    def delete(analysis_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE analyses SET status = "deleted" WHERE id = ?', (analysis_id,))


class RegressionModelDao:
    @staticmethod
    def create(analysis_id, target_variable, predictor_variables, split_type, test_size,
               r2_score, mae, rmse, coefficients, intercept, actual_vs_predicted, residuals):
        model_id = f"mod_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO regression_models (
                    id, analysis_id, target_variable, predictor_variables,
                    split_type, test_size, r2_score, mae, rmse,
                    coefficients, intercept, actual_vs_predicted, residuals, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                model_id, analysis_id, target_variable, json.dumps(predictor_variables),
                split_type, test_size, r2_score, mae, rmse,
                json.dumps(coefficients), intercept, json.dumps(actual_vs_predicted),
                json.dumps(residuals), now
            ))
        return model_id

    @staticmethod
    def get_by_id(model_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM regression_models WHERE id = ?', (model_id,))
            row = cursor.fetchone()
            if not row:
                return None
            data = dict(row)
            data['predictor_variables'] = json.loads(data['predictor_variables'])
            data['coefficients'] = json.loads(data['coefficients'])
            data['actual_vs_predicted'] = json.loads(data['actual_vs_predicted'])
            data['residuals'] = json.loads(data['residuals'])
            return data

    @staticmethod
    def get_by_analysis_id(analysis_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM regression_models 
                WHERE analysis_id = ? 
                ORDER BY created_at DESC
            ''', (analysis_id,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                data = dict(r)
                data['predictor_variables'] = json.loads(data['predictor_variables'])
                data['coefficients'] = json.loads(data['coefficients'])
                data['actual_vs_predicted'] = json.loads(data['actual_vs_predicted'])
                data['residuals'] = json.loads(data['residuals'])
                results.append(data)
            return results


class ForecastDao:
    @staticmethod
    def create(model_id, analysis_id, forecast_type, forecast_params, forecast_results, assumptions, limitations):
        forecast_id = f"fc_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO forecasts (
                    id, model_id, analysis_id, forecast_type, forecast_params,
                    forecast_results, assumptions, limitations, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                forecast_id, model_id, analysis_id, forecast_type,
                json.dumps(forecast_params), json.dumps(forecast_results),
                assumptions, limitations, now
            ))
        return forecast_id

    @staticmethod
    def get_by_id(forecast_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM forecasts WHERE id = ?', (forecast_id,))
            row = cursor.fetchone()
            if not row:
                return None
            data = dict(row)
            data['forecast_params'] = json.loads(data['forecast_params'])
            data['forecast_results'] = json.loads(data['forecast_results'])
            return data

    @staticmethod
    def get_by_analysis_id(analysis_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT f.*, m.target_variable, m.predictor_variables, m.r2_score
                FROM forecasts f
                JOIN regression_models m ON f.model_id = m.id
                WHERE f.analysis_id = ?
                ORDER BY f.created_at DESC
            ''', (analysis_id,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                data = dict(r)
                data['forecast_params'] = json.loads(data['forecast_params'])
                data['forecast_results'] = json.loads(data['forecast_results'])
                data['predictor_variables'] = json.loads(data['predictor_variables'])
                results.append(data)
            return results


class SettingsModel:
    @staticmethod
    def get(key, default=None):
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT value FROM app_settings WHERE key = ?', (key,))
                row = cursor.fetchone()
                return row['value'] if row else default
        except Exception:
            return default

    @staticmethod
    def set(key, value):
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO app_settings (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                ''', (key, str(value)))
                return True
        except Exception:
            return False
