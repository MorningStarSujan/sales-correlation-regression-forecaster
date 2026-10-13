from flask import Blueprint, render_template, jsonify, redirect, url_for, flash, request, session, g, make_response
from database.models import AnalysisModel, RegressionModelDao, SettingsModel
from services.currency_service import CurrencyService

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/analysis')
def default_analysis():
    # Find latest active analysis
    latest = AnalysisModel.get_latest(limit=1)
    if latest:
        return redirect(url_for('analysis.view_analysis', analysis_id=latest[0]['id']))
    flash('No sales analyses found yet. Please upload a dataset or load the sample data to get started.', 'info')
    return redirect(url_for('upload.upload_page'))

@analysis_bp.route('/analysis/<analysis_id>')
def view_analysis(analysis_id):
    analysis = AnalysisModel.get_by_id(analysis_id)
    if not analysis:
        flash(f"Analysis '{analysis_id}' not found.", 'danger')
        return redirect(url_for('dashboard.index'))
        
    models = RegressionModelDao.get_by_analysis_id(analysis_id)

    # Viewing an analysis makes it the dashboard's active dataset for this session
    session['active_analysis_id'] = analysis_id
    
    return render_template(
        'analysis.html',
        analysis=analysis,
        stats=analysis['summary_stats'],
        corr=analysis['correlation_results'],
        quality=analysis['data_quality_report'],
        models=models
    )

@analysis_bp.route('/api/analysis/<analysis_id>')
def get_analysis_json(analysis_id):
    analysis = AnalysisModel.get_by_id(analysis_id)
    if not analysis:
        return jsonify({'success': False, 'error': 'Analysis not found.'}), 404
    return jsonify({'success': True, 'analysis': analysis})

@analysis_bp.route('/api/currency', methods=['GET', 'POST'])
def manage_currency():
    if request.method == 'POST':
        data = request.get_json() or {}
        currency_code = data.get('currency', '').upper()
        supported = CurrencyService.get_supported_currencies()
        if currency_code not in supported:
            return jsonify({'success': False, 'error': f"Invalid currency code '{currency_code}'."}), 400

        # Persist across session, DB, and cookie
        session['selected_currency'] = currency_code
        SettingsModel.set('selected_currency', currency_code)
        
        info = CurrencyService.get_currency(currency_code)
        resp = make_response(jsonify({
            'success': True,
            'currency': currency_code,
            'currency_info': info
        }))
        resp.set_cookie('selected_currency', currency_code, max_age=31536000, samesite='Lax', path='/')
        return resp

    # GET method
    curr_code = getattr(g, 'currency_code', 'USD')
    return jsonify({
        'success': True,
        'current_currency': curr_code,
        'currency_info': CurrencyService.get_currency(curr_code),
        'currencies': CurrencyService.get_supported_currencies()
    })
