from flask import Blueprint, request, jsonify

# Temporarily commented out to fix JSON serialization
# from functions.analytics_service import prioritize_violations
# Temporarily commented out to fix JSON serialization
# from functions.xpshacl_engine.xpshacl_architecture import ConstraintViolation

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/api/analytics/prioritize", methods=["POST"])
def prioritize_violations_route():
    # Temporarily disabled xpshacl engine functionality
    return (
        jsonify(
            {"error": "Analytics functionality temporarily disabled for debugging"}
        ),
        503,
    )
