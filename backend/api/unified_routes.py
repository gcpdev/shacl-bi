from flask import Blueprint, request, jsonify
from rdflib import Graph
from core.validation import run_validation
from core.database import insert_validation_report, create_violation_instances, get_violation_by_id, get_violations_count, get_all_violations
from core.config import VALIDATION_GRAPH, VIOLATION_KG_GRAPH
from core.llm import generate_explanation

bp = Blueprint('unified', __name__, url_prefix='/api')

@bp.route('/')
def index():
    return 'Hello, World!'

@bp.route('/validate', methods=['POST'])
def validate_route():
    """Validation route that accepts data and shapes graphs as Turtle strings."""
    data = request.get_json()
    if not data or 'data_graph' not in data or 'shapes_graph' not in data:
        return jsonify({'error': 'Missing data_graph or shapes_graph in request body'}), 400

    data_graph = Graph().parse(data=data['data_graph'], format='turtle')
    shapes_graph = Graph().parse(data=data['shapes_graph'], format='turtle')

    mode = data.get('mode', 'analytics')

    conforms, results_graph, results_text = run_validation(data_graph, shapes_graph, mode)

    if not conforms:
        insert_validation_report(results_graph, VALIDATION_GRAPH)
        create_violation_instances(VALIDATION_GRAPH, VIOLATION_KG_GRAPH)

    return jsonify({
        'conforms': conforms,
        'results_text': results_text
    })

@bp.route('/violations', methods=['GET'])
def violations_route():
    """Returns a list of all violations."""
    sort_by = request.args.get('sort_by', 'severity')
    order = request.args.get('order', 'desc')
    violations = get_all_violations(VIOLATION_KG_GRAPH, sort_by, order)
    return jsonify(violations)

@bp.route('/violations/<violation_id>', methods=['GET'])
def violation_route(violation_id):
    """Returns the details of a specific violation."""
    violation = get_violation_by_id(violation_id, VIOLATION_KG_GRAPH)

    if not violation:
        return jsonify({'error': 'Violation not found'}), 404

    explanation = generate_explanation(violation['validation_result'])
    violation['explanation'] = explanation
    violation['repair_suggestion'] = 'AI-powered repair suggestion will be here.'

    return jsonify(violation)

@bp.route('/statistics', methods=['GET'])
def statistics_route():
    """Returns the total number of violations."""
    count = get_violations_count(VIOLATION_KG_GRAPH)
    return jsonify({'violations_count': count})
