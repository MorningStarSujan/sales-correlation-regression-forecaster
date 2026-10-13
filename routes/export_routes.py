import io
from flask import Blueprint, render_template, send_file, flash, redirect, url_for, request, g
from database.models import AnalysisModel, RegressionModelDao, ForecastDao
from services.report_service import ReportService
from services.currency_service import CurrencyService

export_bp = Blueprint('export', __name__)

@export_bp.route('/reports')
def reports_page():
    analyses = AnalysisModel.get_all_active()
    selected_id = request.args.get('analysis_id')
    selected_analysis = None
    
    if selected_id:
        selected_analysis = AnalysisModel.get_by_id(selected_id)
    elif analyses:
        selected_analysis = AnalysisModel.get_by_id(analyses[0]['id'])
        
    models = []
    forecasts = []
    if selected_analysis:
        models = RegressionModelDao.get_by_analysis_id(selected_analysis['id'])
        forecasts = ForecastDao.get_by_analysis_id(selected_analysis['id'])
        
    return render_template(
        'reports.html',
        analyses=analyses,
        selected_analysis=selected_analysis,
        models=models,
        forecasts=forecasts
    )

@export_bp.route('/export/pdf/<analysis_id>')
def export_pdf(analysis_id):
    analysis = AnalysisModel.get_by_id(analysis_id)
    if not analysis:
        flash("Analysis not found for PDF export.", 'danger')
        return redirect(url_for('export.reports_page'))
        
    models = RegressionModelDao.get_by_analysis_id(analysis_id)
    forecasts = ForecastDao.get_by_analysis_id(analysis_id)
    
    latest_model = models[0] if models else None
    latest_forecast = forecasts[0] if forecasts else None
    
    currency_code = (
        request.args.get('currency') or
        request.cookies.get('selected_currency') or
        getattr(g, 'currency_code', 'USD')
    )
    if currency_code not in CurrencyService.get_supported_currencies():
        currency_code = 'USD'
    
    try:
        pdf_bytes = ReportService.generate_pdf_report(
            analysis_data=analysis,
            regression_data=latest_model,
            forecast_data=latest_forecast,
            currency_code=currency_code
        )
        
        safe_filename = f"sales_report_{analysis_id}_{currency_code.lower()}.pdf"
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=safe_filename
        )
    except Exception as e:
        flash(f"Error generating PDF report: {str(e)}", 'danger')
        return redirect(url_for('export.reports_page', analysis_id=analysis_id))

@export_bp.route('/export/csv/<analysis_id>')
def export_csv(analysis_id):
    analysis = AnalysisModel.get_by_id(analysis_id)
    if not analysis:
        flash("Analysis not found for CSV export.", 'danger')
        return redirect(url_for('export.reports_page'))
        
    models = RegressionModelDao.get_by_analysis_id(analysis_id)
    forecasts = ForecastDao.get_by_analysis_id(analysis_id)
    
    latest_model = models[0] if models else None
    latest_forecast = forecasts[0] if forecasts else None
    
    currency_code = (
        request.args.get('currency') or
        request.cookies.get('selected_currency') or
        getattr(g, 'currency_code', 'USD')
    )
    if currency_code not in CurrencyService.get_supported_currencies():
        currency_code = 'USD'
    
    try:
        csv_content = ReportService.generate_csv_summary(
            analysis_data=analysis,
            regression_data=latest_model,
            forecast_data=latest_forecast,
            currency_code=currency_code
        )
        
        safe_filename = f"sales_summary_{analysis_id}_{currency_code.lower()}.csv"
        return send_file(
            io.BytesIO(csv_content.encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=safe_filename
        )
    except Exception as e:
        flash(f"Error exporting CSV: {str(e)}", 'danger')
        return redirect(url_for('export.reports_page', analysis_id=analysis_id))
