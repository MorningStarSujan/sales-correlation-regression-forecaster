# Sales Correlation & Regression Forecaster

A complete, minimal, functional, and professional sales analysis and forecasting web application built with **Flask**, **Pandas**, **NumPy**, **Scikit-learn**, and **Chart.js**.

Designed for practical business forecasting and academic demonstration, this application utilizes **conventional statistics** and **traditional machine learning (Ordinary Least Squares Linear Regression)**. It strictly avoids external AI APIs, LLMs, or fabricated predictions.

---

## Key Features

1. **Executive Dashboard**
   - Live KPI cards: Total Revenue, Units Sold, Average Transaction Sale, and Sales Growth Rate.
   - Dual-axis interactive trend chart (Revenue & Units) powered by Chart.js.
   - Product category revenue contribution distribution.
   - Summary repository of recent analyses with quick-action links.

2. **Data Upload & Smart Inspection**
   - Supports both Excel (`.xlsx`, `.xls`) and CSV (`.csv`) files.
   - Automatic column role detection (Revenue/Sales, Dates, Units, Product Categories, Unit Prices).
   - Instant data hygiene diagnostics: row/column counts, duplicate records, missing value frequencies, and data type validation.
   - Interactive data preview table and customizable column mapping before analysis execution.

3. **Automated Sales Analysis**
   - Instant calculation of sales metrics: total revenue, mean, median, min, max, standard deviation, and period growth.
   - Granular time-series aggregation (daily, weekly, or monthly based on span).
   - Product category performance breakdown table with percentage contributions.
   - Comprehensive summary statistics table for all numerical attributes.

4. **Correlation Analysis & Heatmap**
   - Full Pearson correlation matrix for all continuous numerical features.
   - Color-coded correlation heatmap table with intensity gradients (positive blue, negative red).
   - Identification of top driver pairs with plain-language factual statistical interpretations.
   - **Causation Notice**: Prominently highlights that correlation measures linear co-movement, not direct causality.

5. **Scikit-learn Linear Regression**
   - User-selectable dependent variable (*y*) and multi-select independent predictor features (*X*).
   - Strict train/test splitting: Chronological partition (to prevent lookahead leakage in temporal series) or random split.
   - Rigorous error evaluation metrics: **R² (Coefficient of Determination)**, **MAE (Mean Absolute Error)**, **RMSE (Root Mean Squared Error)**, and training R² for overfitting diagnostics.
   - Explicit mathematical regression equation display: $y = \beta_0 + \sum \beta_i X_i$.
   - Interactive Actual vs. Predicted comparison chart and residual distribution plot ($e = y - \hat{y}$).

6. **Sales Forecasting Engine**
   - **What-If Scenario Simulator**: Input prospective predictor levels to obtain deterministic point predictions with **95% prediction intervals ($\pm 1.96 \times \text{RMSE}$)** and factor contribution breakdowns. Warns if inputs extrapolate beyond historical bounds.
   - **Multi-Period Horizon Projector**: Project future sales across 3, 6, or 12 periods with customizable periodic growth trajectories and shaded uncertainty bands.
   - Comprehensive methodological disclosures detailing model assumptions and limitations.

7. **Analysis History & SQLite Persistence**
   - Every upload and analysis is saved to a local SQLite database (`database/sales_forecaster.db`) with unique IDs (`an_...`, `ds_...`).
   - New uploads never overwrite historical records.
   - Rename, reopen, or delete previous analyses at any time.

8. **Dataset Comparison Diagnostics**
   - Side-by-side comparison of any two historical analyses.
   - Comparative KPI deltas (+/- % change in Revenue, Volume, Average Sale).
   - Automated schema inspection: shared columns, missing attributes, and date interval alignment.
   - Direct comparability warnings when column names, definitions, or units differ.

9. **Publication-Grade Reports**
   - **PDF Report**: Downloadable formatted PDF document (via ReportLab) containing KPIs, product breakdown, correlation drivers, regression coefficients, forecasts, and statistical disclosures.
   - **CSV Export**: Clean structured CSV summary for spreadsheet tools.

---

## Technology Stack

- **Frontend**: Semantic HTML5, Vanilla CSS3 (custom design system, light theme, subtle blue accents), JavaScript (ES6+), Chart.js
- **Backend**: Python 3, Flask
- **Data Processing**: Pandas, NumPy, OpenPyXL
- **Machine Learning**: Scikit-learn (LinearRegression, train_test_split, metrics)
- **Database**: SQLite (WAL mode, foreign keys enabled)
- **Reporting**: ReportLab (PDF), Python standard CSV library

---

## Project Structure

```
Sales Correlation & Regression Forecaster/
├── app.py                     # Flask application factory & entrypoint
├── config.py                  # File paths, upload limits, SQLite config
├── requirements.txt           # Project dependencies
├── README.md                  # Comprehensive documentation
├── .gitignore                 # Git ignore rules
├── database/
│   ├── __init__.py
│   ├── db.py                  # SQLite connection & schema initialization
│   └── models.py              # DAO models for datasets, analyses, models, forecasts
├── services/
│   ├── __init__.py
│   ├── data_processor.py      # File reading, column detection, quality inspection
│   ├── sales_analyzer.py      # Descriptive stats, trends, growth calculations
│   ├── correlation_service.py # Pearson matrix, heatmap data, interpretations
│   ├── regression_service.py  # Sklearn Linear Regression, metrics, residuals
│   ├── forecaster_service.py  # Scenario & horizon projections with 95% bounds
│   ├── comparison_service.py  # Dataset comparison, schema diffs, warnings
│   └── report_service.py      # PDF (ReportLab) & CSV report generators
├── routes/
│   ├── __init__.py
│   ├── dashboard_routes.py    # Dashboard & sample loader routes
│   ├── upload_routes.py       # Upload & column mapping routes
│   ├── analysis_routes.py     # Sales analysis & correlation routes
│   ├── regression_routes.py   # Regression model training & evaluation routes
│   ├── forecast_routes.py     # What-if scenario & horizon forecast routes
│   ├── history_routes.py      # History, rename, delete, and compare routes
│   └── export_routes.py       # PDF and CSV export routes
├── templates/
│   ├── base.html              # Core layout (sidebar nav, topbar)
│   ├── dashboard.html         # Executive overview & KPI cards
│   ├── upload.html            # File upload & column mapper
│   ├── analysis.html          # Stats, time series, correlation heatmap
│   ├── regression.html        # Model fitting, R²/MAE/RMSE, residuals
│   ├── forecast.html          # Scenario simulator & horizon chart
│   ├── history.html           # Previous analyses list & dataset comparison
│   ├── reports.html           # Export center & report overview
│   ├── 404.html               # Not found error page
│   └── 500.html               # Internal error page
├── static/
│   ├── css/
│   │   └── style.css          # Minimalist responsive stylesheet
│   └── js/
│       ├── main.js            # Sidebar toggle, sample data triggers
│       ├── dashboard.js       # Dashboard Chart.js charts
│       ├── upload.js          # File dropzone & column mapping
│       ├── analysis.js        # Trend charts & heatmap color coding
│       ├── regression.js      # Feature selectors, live train, residual plots
│       ├── forecast.js        # Scenario simulator & horizon projections
│       └── compare.js         # History actions & comparison diff engine
├── data/
│   ├── uploads/               # Securely stored uploaded files
│   ├── reports/               # Export storage directory
│   ├── sample_sales_data.csv  # 180-day multi-category demo dataset (CSV)
│   └── sample_sales_data.xlsx # 180-day multi-category demo dataset (Excel)
├── scripts/
│   └── generate_sample_data.py# Script to generate realistic test data
└── tests/
    ├── __init__.py
    ├── test_data_processor.py # File reading and column detection tests
    ├── test_sales_analyzer.py # Descriptive statistics and correlation tests
    ├── test_regression.py     # Regression, metrics, and forecast tests
    └── test_app_routes.py     # End-to-end Flask integration tests
```

---

## Installation & Running Locally

### 1. Prerequisites
- Python 3.10+ installed on your system.

### 2. Clone or Navigate to Project
```bash
cd "d:\ANTI GRAVITY\PROJECTS\Sales Correlation & Regression Forecaster"
```

### 3. Create and Activate Virtual Environment
On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 5. Run Automated Tests
```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

### 6. Start the Web Application
```powershell
.\.venv\Scripts\python.exe app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

---

## Demonstration Workflow

1. **Instant Demo**: Click **"Load Sample Data"** on the Dashboard to load the included 180-record multi-category sales dataset.
2. **Review Analysis**: Explore the sales trajectory, category breakdown, descriptive statistics, and the interactive correlation heatmap.
3. **Fit Regression Model**: Go to **Linear Regression**, select `Sales_Revenue` as the target and predictors like `Marketing_Spend`, `Website_Traffic`, and `Discount_Percent`. Choose a chronological or random split and inspect R², MAE, RMSE, and residual distribution.
4. **Forecast**: Navigate to **Forecasting** to run what-if scenarios with custom marketing inputs or project sales forward over 3 to 12 periods with 95% confidence bands.
5. **Download Report**: Go to **Reports** and click **"Download PDF Report"** for a publication-ready document or export as CSV.
6. **Compare**: Upload a second file or run a distinct analysis, then visit **History & Compare** to evaluate metric differences and schema compatibility.
