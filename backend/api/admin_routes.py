from flask import Blueprint, jsonify, request
from core.database import load_ontology
from core.config import VIOLATION_KG_GRAPH
from auth import encode_auth_token, token_required
import os

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@bp.route('/login', methods=['POST'])
def login():
    """Generates a JWT token for a user."""
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({'error': 'Missing user_id in request body'}), 400
    
    token = encode_auth_token(data['user_id'])
    return jsonify({'token': token})

@bp.route('/load_ontology', methods=['POST'])
@token_required
def load_ontology_route(user_id):
    """Loads the violation ontology into the database."""
    try:
        ontology_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ontologies', 'violation.ttl'))
        load_ontology(ontology_file, VIOLATION_KG_GRAPH)
        return jsonify({'message': 'Ontology loaded successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
