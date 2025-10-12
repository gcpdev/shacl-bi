from flask import Blueprint, jsonify, request
from functions.dashboard_service import get_dashboard_data
from functions import virtuoso_service

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/api/test-violation-count', methods=['GET'])
def test_violation_count():
    """Test endpoint to directly check violation count"""
    try:
        session_id = request.args.get('session_id')
        if session_id:
            validation_graph_uri = f"http://ex.org/ValidationReport/Session_{session_id}"
        else:
            validation_graph_uri = "http://ex.org/ValidationReport"

        print(f"Test endpoint: Querying violations from {validation_graph_uri}")
        count = virtuoso_service.get_number_of_violations_in_validation_report(validation_graph_uri)
        print(f"Test endpoint: Found {count} violations")

        return jsonify({
            'violation_count': count,
            'validation_graph_uri': validation_graph_uri
        }), 200
    except Exception as e:
        print(f"Test endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/dashboard-data', methods=['GET'])
def get_dashboard_data_route():
    """
    Get dashboard analytics data
    Returns comprehensive statistics for the SHACL dashboard
    Supports session-specific data isolation
    """
    try:
        # Check for session_id parameter for tenant isolation
        session_id = request.args.get('session_id')
        if session_id:
            validation_graph_uri = f"http://ex.org/ValidationReport/Session_{session_id}"
        else:
            # Fallback to default graph for backward compatibility
            validation_graph_uri = "http://ex.org/ValidationReport"

        data = get_dashboard_data(validation_graph_uri)
        return jsonify({
            **data,
            'session_id': session_id,
            'validation_graph_uri': validation_graph_uri
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
