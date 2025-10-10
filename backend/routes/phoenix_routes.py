from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from functions.phoenix_service import validate_with_phoenix, explanation_cache

phoenix_bp = Blueprint('phoenix_bp', __name__)

@phoenix_bp.route('/api/validate-phoenix', methods=['POST'])
def validate_phoenix_route():
    # Handle both naming conventions for file upload
    data_file = None
    shapes_file = None

    # Try different possible field names
    if 'dataGraphFile' in request.files:
        data_file = request.files['dataGraphFile']
    elif 'data_file' in request.files:
        data_file = request.files['data_file']
    elif 'data' in request.files:
        data_file = request.files['data']

    if 'shapesGraphFile' in request.files:
        shapes_file = request.files['shapesGraphFile']
    elif 'shapes_file' in request.files:
        shapes_file = request.files['shapes_file']
    elif 'shapes' in request.files:
        shapes_file = request.files['shapes']

    if not data_file or not shapes_file:
        return jsonify({'error': 'Missing data or shapes file'}), 400

    # Create a temporary directory
    temp_dir = 'temp'
    os.makedirs(temp_dir, exist_ok=True)

    data_filename = secure_filename(data_file.filename)
    shapes_filename = secure_filename(shapes_file.filename)

    data_file_path = os.path.join(temp_dir, data_filename)
    shapes_file_path = os.path.join(temp_dir, shapes_filename)

    data_file.save(data_file_path)
    shapes_file.save(shapes_file_path)

    # The cleanup of the temporary files will be handled by the background thread
    # after the explanations have been generated.
    conforms, report_graph_json, report_text, explanations, violations, constraints = validate_with_phoenix(data_file_path, shapes_file_path)

    return jsonify({
        'conforms': conforms,
        'report_graph': report_graph_json,
        'report_text': report_text,
        'explanations': explanations,
        'violations': violations,
        'constraints': constraints
    })

@phoenix_bp.route('/api/explanations/<session_id>', methods=['GET'])
def get_explanations(session_id):
    """
    Fetch enhanced explanations for a validation session.
    Returns the AI-generated explanations when they are ready.
    """
    try:
        if session_id in explanation_cache:
            explanations = explanation_cache[session_id]
            return jsonify({
                'status': 'completed',
                'explanations': explanations
            })
        else:
            return jsonify({
                'status': 'processing',
                'message': 'AI explanations are still being generated. Please try again in a moment.'
            }), 202
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching explanations: {str(e)}'
        }), 500