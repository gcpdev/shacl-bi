from flask import Blueprint, request, jsonify
from functions.analytics_service import prioritize_violations
from functions.xpshacl_engine.xpshacl_architecture import ConstraintViolation

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/api/analytics/prioritize', methods=['POST'])
def prioritize_violations_route():
    violations_dict = request.get_json()
    violations = [ConstraintViolation.from_dict(v) for v in violations_dict]

    prioritized_violations = prioritize_violations(violations)

    return jsonify([v.to_dict() for v in prioritized_violations]), 200