from flask import Blueprint, request, jsonify
from rdflib import Graph
from functions.validation import validate

validation_bp = Blueprint('validation', __name__)

@validation_bp.route('/api/validate', methods=['POST'])
def validate_route():
    data = request.get_json()
    data_graph_str = data.get('data_graph')
    shapes_graph_str = data.get('shapes_graph')
    validation_report_str = data.get('validation_report')

    if not data_graph_str or not shapes_graph_str:
        return jsonify({'error': 'data_graph and shapes_graph are required'}), 400

    data_graph = Graph().parse(data=data_graph_str, format='turtle')
    shapes_graph = Graph().parse(data=shapes_graph_str, format='turtle')

    validation_report = None
    if validation_report_str:
        validation_report = Graph().parse(data=validation_report_str, format='turtle')

    result_graph = validate(data_graph, shapes_graph, validation_report)

    return jsonify({'validation_report': result_graph.serialize(format='turtle')}), 200
