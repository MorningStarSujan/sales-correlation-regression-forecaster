from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from database.models import AnalysisModel, RegressionModelDao, ForecastDao
from services.data_processor import DataProcessor
from services.forecaster_service import ForecasterService

forecast_bp = Blueprint('forecast', __name__)

@forecast_bp.route('/forecasting')
def default_forecast():
    latest = AnalysisModel.get_latest(limit=1)
    if latest:
        return redirect(url_for('forecast.view_forecast', analysis_id=latest[0]['id']))
    flash('Please upload a sales dataset before accessing forecasting.', 'info')
    return redirect(url_for('upload.upload_page'))

@forecast_bp.route('/forecasting/<analysis_id>')
def view_forecast(analysis_id):
    analysis = AnalysisModel.get_by_id(analysis_id)
    if not analysis:
        flash(f"Analysis '{analysis_id}' not found.", 'danger')
        return redirect(url_for('dashboard.index'))
        
    models = RegressionModelDao.get_by_analysis_id(analysis_id)
    forecasts = ForecastDao.get_by_analysis_id(analysis_id)
    
    # Calculate historical min/max/mean ranges for each numeric predictor
    stats = analysis.get('summary_stats', {})
    desc = stats.get('descriptive_stats', {})
    
    # Selected model (defaults to the first/latest model if available)
    selected_model = models[0] if models else None
    
    return render_template(
        'forecast.html',
        analysis=analysis,
        models=models,
        selected_model=selected_model,
        forecasts=forecasts,
        descriptive_stats=desc
    )

@forecast_bp.route('/api/forecast/scenario', methods=['POST'])
def run_scenario():
    data = request.get_json() or {}
    model_id = data.get('model_id')
    analysis_id = data.get('analysis_id')
    user_inputs = data.get('inputs') or {}
    
    if not model_id or not analysis_id:
        return jsonify({'success': False, 'error': 'Missing model_id or analysis_id.'}), 400
        
    model = RegressionModelDao.get_by_id(model_id)
    if not model:
        return jsonify({'success': False, 'error': 'Regression model not found.'}), 404
        
    analysis = AnalysisModel.get_by_id(analysis_id)
    if not analysis:
        return jsonify({'success': False, 'error': 'Analysis not found.'}), 404
        
    try:
        # Get historical bounds to check for extrapolation
        desc = analysis.get('summary_stats', {}).get('descriptive_stats', {})
        
        result = ForecasterService.forecast_scenario(
            model_data=model,
            user_inputs=user_inputs,
            historical_ranges=desc
        )
        
        # Save in SQLite
        fc_id = ForecastDao.create(
            model_id=model_id,
            analysis_id=analysis_id,
            forecast_type='scenario',
            forecast_params={'inputs': user_inputs},
            forecast_results=result,
            assumptions=result['assumptions'],
            limitations=result['limitations']
        )
        
        result['forecast_id'] = fc_id
        result['success'] = True
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@forecast_bp.route('/api/forecast/horizon', methods=['POST'])
def run_horizon():
    data = request.get_json() or {}
    model_id = data.get('model_id')
    analysis_id = data.get('analysis_id')
    periods = int(data.get('periods', 6))
    growth_rate = float(data.get('growth_rate_pct', 0.0))
    
    if not model_id or not analysis_id:
        return jsonify({'success': False, 'error': 'Missing model_id or analysis_id.'}), 400
        
    model = RegressionModelDao.get_by_id(model_id)
    if not model:
        return jsonify({'success': False, 'error': 'Regression model not found.'}), 404
        
    analysis = AnalysisModel.get_by_id(analysis_id)
    if not analysis:
        return jsonify({'success': False, 'error': 'Analysis not found.'}), 404
        
    try:
        df = DataProcessor.load_file(analysis['file_path'])
        date_col = analysis.get('column_mapping', {}).get('date_col')
        
        result = ForecasterService.forecast_horizon(
            model_data=model,
            df=df,
            periods=periods,
            growth_rate_pct=growth_rate,
            date_col=date_col
        )
        
        fc_id = ForecastDao.create(
            model_id=model_id,
            analysis_id=analysis_id,
            forecast_type='horizon',
            forecast_params={'periods': periods, 'growth_rate_pct': growth_rate},
            forecast_results=result['results'],
            assumptions=result['assumptions'],
            limitations=result['limitations']
        )
        
        result['forecast_id'] = fc_id
        result['success'] = True
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
