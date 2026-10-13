from flask import Blueprint, render_template, jsonify, redirect, url_for, flash, request, session
from config import Config
from database.models import AnalysisModel, DatasetModel, RegressionModelDao
from services.data_processor import DataProcessor
from services.sales_analyzer import SalesAnalyzer
from services.correlation_service import CorrelationService

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    latest_analyses = AnalysisModel.get_latest(limit=6)
    active_analysis = None

    # The dashboard starts empty and only shows a dataset once the user has
    # explicitly activated one this session - by loading the sample data,
    # uploading and confirming a file, or opening an analysis. It never
    # falls back to silently re-displaying old history on its own.
    analysis_id = request.args.get('analysis_id') or session.get('active_analysis_id')
    if analysis_id:
        active_analysis = AnalysisModel.get_by_id(analysis_id)
        if active_analysis:
            session['active_analysis_id'] = active_analysis['id']
        else:
            session.pop('active_analysis_id', None)

    return render_template(
        'dashboard.html',
        active_analysis=active_analysis,
        latest_analyses=latest_analyses
    )

@dashboard_bp.route('/api/load-sample', methods=['POST'])
def load_sample():
    """
    One-click helper to automatically load the built-in sample sales dataset,
    inspect it, run automated analysis, and store it in SQLite.
    """
    try:
        sample_path = Config.SAMPLE_DATA_PATH
        if not sample_path.exists():
            return jsonify({'success': False, 'error': 'Sample dataset not found on disk.'}), 404
            
        df = DataProcessor.load_file(sample_path)
        quality = DataProcessor.inspect_dataset(df)
        mapping = DataProcessor.auto_detect_columns(df)
        
        # Save dataset record
        ds_id = DatasetModel.create(
            filename='sample_sales_data.csv',
            stored_filename='sample_sales_data.csv',
            file_path=str(sample_path),
            file_type='csv',
            file_size_bytes=sample_path.stat().st_size,
            row_count=len(df),
            col_count=len(df.columns),
            column_metadata=quality['columns'],
            column_mapping=mapping,
            source='sample'
        )
        
        # Run automated analysis
        sales_stats = SalesAnalyzer.analyze(df, mapping)
        corr_results = CorrelationService.calculate_correlation(df)
        
        analysis_id = AnalysisModel.create(
            dataset_id=ds_id,
            title='Sample Retail Sales Analysis (Demonstration)',
            description='Automated analysis of 180-day multi-category retail sales transaction dataset.',
            summary_stats=sales_stats,
            correlation_results=corr_results,
            data_quality_report=quality
        )

        # Mark this sample analysis as the active dashboard dataset for this session
        session['active_analysis_id'] = analysis_id
        
        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'redirect_url': url_for('analysis.view_analysis', analysis_id=analysis_id)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
