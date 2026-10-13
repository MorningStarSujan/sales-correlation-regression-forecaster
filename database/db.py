import sqlite3
import json
from contextlib import contextmanager
from config import Config

def get_db_connection():
    conn = sqlite3.connect(Config.DATABASE_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

@contextmanager
def get_db():
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    Config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Datasets Table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS datasets (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size_bytes INTEGER NOT NULL,
            row_count INTEGER NOT NULL,
            col_count INTEGER NOT NULL,
            column_metadata TEXT NOT NULL, -- JSON string
            column_mapping TEXT NOT NULL,  -- JSON string
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        );
        ''')

        # 1b. Migration: add 'source' column to distinguish sample vs uploaded
        # datasets on databases created before this column existed. Safe to
        # run every startup - it's a no-op once the column is present.
        cursor.execute("PRAGMA table_info(datasets)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if 'source' not in existing_cols:
            cursor.execute(
                "ALTER TABLE datasets ADD COLUMN source TEXT DEFAULT 'upload'"
            )
            # Best-effort backfill: any pre-existing rows created from the
            # built-in sample file are relabeled as 'sample' so history/dashboard
            # views can keep sample and uploaded data visually separate.
            cursor.execute(
                "UPDATE datasets SET source = 'sample' WHERE filename = 'sample_sales_data.csv' AND (source IS NULL OR source != 'sample')"
            )

        # 2. Analyses Table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id TEXT PRIMARY KEY,
            dataset_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            summary_stats TEXT NOT NULL,       -- JSON string
            correlation_results TEXT NOT NULL, -- JSON string
            data_quality_report TEXT NOT NULL, -- JSON string
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
        );
        ''')
        
        # 3. Regression Models Table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS regression_models (
            id TEXT PRIMARY KEY,
            analysis_id TEXT NOT NULL,
            target_variable TEXT NOT NULL,
            predictor_variables TEXT NOT NULL,  -- JSON list
            split_type TEXT NOT NULL,           -- 'chronological' or 'random'
            test_size REAL NOT NULL,
            r2_score REAL NOT NULL,
            mae REAL NOT NULL,
            rmse REAL NOT NULL,
            coefficients TEXT NOT NULL,         -- JSON dict: feature -> coef
            intercept REAL NOT NULL,
            actual_vs_predicted TEXT NOT NULL,  -- JSON sample data for chart
            residuals TEXT NOT NULL,            -- JSON sample residuals
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
        );
        ''')
        
        # 4. Forecasts Table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS forecasts (
            id TEXT PRIMARY KEY,
            model_id TEXT NOT NULL,
            analysis_id TEXT NOT NULL,
            forecast_type TEXT NOT NULL,       -- 'scenario' or 'future_steps'
            forecast_params TEXT NOT NULL,     -- JSON dict
            forecast_results TEXT NOT NULL,    -- JSON list of predicted rows
            assumptions TEXT NOT NULL,
            limitations TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (model_id) REFERENCES regression_models(id) ON DELETE CASCADE,
            FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
        );
        ''')
        
        # 5. App Settings Table (Key-Value configuration persistence)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        
        conn.commit()

if __name__ == '__main__':
    init_db()
    print("Database schema initialized successfully.")
