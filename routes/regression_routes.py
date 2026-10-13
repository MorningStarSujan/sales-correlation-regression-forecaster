from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from database.models import AnalysisModel, RegressionModelDao
from services.data_processor import DataProcessor
from services.regression_service import RegressionService

regression_bp = Blueprint('regression', __name__)

@regression_bp.route('/regression')
def default_regression():
    latest = AnalysisModel.get_latest(limit=1)
    if latest:
        return redirect(url_for('regression.view_regression', analysis_id=latest[0]['id']))
    flash('Please upload or load a dataset first before running regression.', 'info')
    return redirect(url_for('upload.upload_page'))

@regression_bp.route('/regression/<analysis_id>')
def view_regression(analysis_id):
    analysis = AnalysisModel.get_by_id(analysis_id)
    if not analysis:
        flash(f"Analysis '{analysis_id}' not found.", 'danger')
        return redirect(url_for('dashboard.index'))
        
    models = RegressionModelDao.get_by_analysis_id(analysis_id)
    stats = analysis.get('summary_stats', {})
    numeric_cols = stats.get('numeric_columns', [])
    mapping = analysis.get('column_mapping', {})
    
    # Pre-select target: mapped sales_col or first numeric
    default_target = mapping.get('sales_col')
    if not default_target or default_target not in numeric_cols:
        default_target = numeric_cols[0] if numeric_cols else ''
        
    # Default predictors: all other numeric columns
    default_predictors = [c for c in numeric_cols if c != default_target]
    
    return render_template(
        'regression.html',
        analysis=analysis,
        models=models,
        numeric_columns=numeric_cols,
        default_target=default_target,
        default_predictors=default_predictors,
        has_date=bool(mapping.get('date_col'))
    )

@regression_bp.route('/api/regression/train', methods=['POST'])
def train_model():
    data = request.get_json() or {}
    analysis_id = data.get('analysis_id')
    target_var = data.get('target_variable')
    predictor_vars = data.get('predictor_variables') or []
    split_type = data.get('split_type', 'chronological')
    test_size = float(data.get('test_size', 0.2))
    
    if not analysis_id:
        return jsonify({'success': False, 'error': 'Missing analysis_id parameter.'}), 400
        
    analysis = AnalysisModel.get_by_id(analysis_id)
    if not analysis:
        return jsonify({'success': False, 'error': 'Analysis not found.'}), 404
        
    if not target_var:
        return jsonify({'success': False, 'error': 'Please select a target variable (dependent variable).'}), 400
        
    if not predictor_vars:
        return jsonify({'success': False, 'error': 'Please select at least one predictor variable (independent variable).'}), 400
        
    try:
        # Load dataset
        df = DataProcessor.load_file(analysis['file_path'])
        date_col = analysis.get('column_mapping', {}).get('date_col')
        
        # Train and evaluate linear regression model
        results = RegressionService.train_linear_regression(
            df=df,
            target_col=target_var,
            predictor_cols=predictor_vars,
            split_type=split_type,
            test_size=test_size,
            date_col=date_col
        )
        
        # Save model record in SQLite
        model_id = RegressionModelDao.create(
            analysis_id=analysis_id,
            target_variable=target_var,
            predictor_variables=predictor_vars,
            split_type=split_type,
            test_size=test_size,
            r2_score=results['r2_score'],
            mae=results['mae'],
            rmse=results['rmse'],
            coefficients=results['coefficients'],
            intercept=results['intercept'],
            actual_vs_predicted=results['comparison_points'],
            residuals=results['residuals']
        )
        
        results['model_id'] = model_id
        results['success'] = True
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
