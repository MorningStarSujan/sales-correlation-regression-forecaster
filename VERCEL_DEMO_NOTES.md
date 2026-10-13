# Vercel demo notes

This is the original Sales Correlation & Regression Forecaster application with minimal deployment adjustments.

## Deploy
- Import this project in Vercel with the project root set to this directory.
- Vercel should detect the Flask application in `app.py` and install `requirements.txt`.
- Set `SECRET_KEY` in Vercel Project Settings > Environment Variables to a long random value for Production and Preview.
- Deploy and test sample data, upload, analysis, regression, forecasting, and exports.

## Temporary storage limitation
When `VERCEL=1`, the SQLite database, uploaded files, and generated reports use `/tmp`. Vercel's temporary filesystem is not durable and may not be shared between function instances. This is suitable only for a short academic demonstration. History and uploads can disappear or fail to be available on later requests. Do not use this setup for important data or multi-user production workloads.

## Local development
Outside Vercel, the original project paths remain in use. Run locally with `python app.py` after installing `requirements.txt`.
