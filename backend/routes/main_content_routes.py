
from flask import Blueprint, jsonify, request
from functions.main_content_service import get_main_content_data
from functions.xpshacl_engine.xpshacl_engine import get_explanation_and_suggestion

main_content_bp = Blueprint('main_content', __name__)

@main_content_bp.route('/api/main-content', methods=['POST'])
def main_content():
    data = request.get_json()
    directory_path = data.get('directoryPath')
    shapes_graph_name = data.get('shapesGraphName')
    validation_report_name = data.get('validationReportName')
    
    main_content_data = get_main_content_data(directory_path, shapes_graph_name, validation_report_name)
    
    return jsonify(main_content_data)

@main_content_bp.route('/api/violation-details', methods=['POST'])
def violation_details():
    data = request.get_json()
    violation = data.get('violation')
    
    explanation, suggestion = get_explanation_and_suggestion(violation)
    
    return jsonify({'explanation': explanation, 'suggestion': suggestion})
