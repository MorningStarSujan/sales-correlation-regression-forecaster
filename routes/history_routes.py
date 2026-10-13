from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from database.models import AnalysisModel
from services.comparison_service import ComparisonService

history_bp = Blueprint('history', __name__)

@history_bp.route('/history')
def view_history():
    analyses = AnalysisModel.get_all_active()
    return render_template('history.html', analyses=analyses)

@history_bp.route('/api/analyses/<analysis_id>/rename', methods=['POST'])
def rename_analysis(analysis_id):
    data = request.get_json() or {}
    new_title = data.get('title')
    if not new_title or not new_title.strip():
        return jsonify({'success': False, 'error': 'Analysis title cannot be empty.'}), 400
        
    AnalysisModel.rename(analysis_id, new_title.strip())
    return jsonify({'success': True, 'title': new_title.strip()})

@history_bp.route('/api/analyses/<analysis_id>/delete', methods=['POST'])
def delete_analysis(analysis_id):
    AnalysisModel.delete(analysis_id)
    return jsonify({'success': True})

@history_bp.route('/api/compare', methods=['GET'])
def compare_datasets():
    id_a = request.args.get('id_a')
    id_b = request.args.get('id_b')
    
    if not id_a or not id_b:
        return jsonify({'success': False, 'error': 'Please select both datasets for comparison.'}), 400
        
    if id_a == id_b:
        return jsonify({'success': False, 'error': 'Please select two distinct analyses to compare.'}), 400
        
    analysis_a = AnalysisModel.get_by_id(id_a)
    analysis_b = AnalysisModel.get_by_id(id_b)
    
    if not analysis_a or not analysis_b:
        return jsonify({'success': False, 'error': 'One or both analyses could not be retrieved.'}), 404
        
    try:
        comparison_res = ComparisonService.compare_analyses(analysis_a, analysis_b)
        return jsonify({'success': True, 'comparison': comparison_res})
    except Exception as e:
        return jsonify({'success': False, 'error': f"Comparison failure: {str(e)}"}), 500
