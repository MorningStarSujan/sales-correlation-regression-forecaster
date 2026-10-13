import uuid
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify, url_for, session
from werkzeug.utils import secure_filename
from config import Config
from database.models import DatasetModel, AnalysisModel
from services.data_processor import DataProcessor
from services.sales_analyzer import SalesAnalyzer
from services.correlation_service import CorrelationService

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload')
def upload_page():
    return render_template('upload.html')

@upload_bp.route('/api/upload', methods=['POST'])
def handle_upload():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded in the request.'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Empty filename selected.'}), 400
        
    orig_name = secure_filename(file.filename)
    ext = Path(orig_name).suffix.lower().replace('.', '')
    
    if ext not in Config.ALLOWED_EXTENSIONS:
        return jsonify({
            'success': False, 
            'error': f"Invalid file format '.{ext}'. Only CSV (.csv) and Excel (.xlsx, .xls) files are supported."
        }), 400
        
    # Generate unique stored filename to prevent overwriting
    unique_prefix = uuid.uuid4().hex[:8]
    stored_name = f"{unique_prefix}_{orig_name}"
    save_path = Config.UPLOAD_FOLDER / stored_name
    file.save(str(save_path))
    
    try:
        # Load and validate dataset
        df = DataProcessor.load_file(save_path)
        
        if df.empty or len(df) == 0:
            save_path.unlink(missing_ok=True)
            return jsonify({'success': False, 'error': 'The uploaded file contains no data rows.'}), 400
            
        quality = DataProcessor.inspect_dataset(df)
        detected_mapping = DataProcessor.auto_detect_columns(df)
        preview = DataProcessor.get_preview_data(df, max_rows=15)
        
        file_size = save_path.stat().st_size
        
        dataset_id = DatasetModel.create(
            filename=orig_name,
            stored_filename=stored_name,
            file_path=str(save_path),
            file_type=ext,
            file_size_bytes=file_size,
            row_count=len(df),
            col_count=len(df.columns),
            column_metadata=quality['columns'],
            column_mapping=detected_mapping,
            source='upload'
        )
        
        return jsonify({
            'success': True,
            'dataset_id': dataset_id,
            'filename': orig_name,
            'file_size': file_size,
            'row_count': len(df),
            'col_count': len(df.columns),
            'columns': list(df.columns),
            'quality': quality,
            'detected_mapping': detected_mapping,
            'preview': preview
        })
        
    except Exception as e:
        save_path.unlink(missing_ok=True)
        return jsonify({'success': False, 'error': f"Error processing file: {str(e)}"}), 500

@upload_bp.route('/api/confirm-mapping', methods=['POST'])
def confirm_mapping():
    data = request.get_json() or {}
    dataset_id = data.get('dataset_id')
    mapping = data.get('column_mapping') or {}
    title = data.get('title') or 'Automated Sales Analysis'
    description = data.get('description', '')
    
    if not dataset_id:
        return jsonify({'success': False, 'error': 'Missing dataset_id.'}), 400
        
    ds = DatasetModel.get_by_id(dataset_id)
    if not ds:
        return jsonify({'success': False, 'error': 'Dataset record not found.'}), 404
        
    try:
        # Update mapping on dataset
        DatasetModel.update_mapping(dataset_id, mapping)
        
        # Load dataset and execute automated analyses
        df = DataProcessor.load_file(ds['file_path'])
        quality = DataProcessor.inspect_dataset(df)
        sales_stats = SalesAnalyzer.analyze(df, mapping)
        corr_results = CorrelationService.calculate_correlation(df)
        
        analysis_id = AnalysisModel.create(
            dataset_id=dataset_id,
            title=title.strip(),
            description=description.strip(),
            summary_stats=sales_stats,
            correlation_results=corr_results,
            data_quality_report=quality
        )

        # Mark this freshly uploaded & analyzed dataset as the active dashboard dataset
        session['active_analysis_id'] = analysis_id
        
        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'redirect_url': url_for('analysis.view_analysis', analysis_id=analysis_id)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f"Analysis generation error: {str(e)}"}), 500
