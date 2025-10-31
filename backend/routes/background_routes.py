from flask import Blueprint, jsonify
from functions.background_processor import get_job_status

# Create blueprint
background_bp = Blueprint("background", __name__)


@background_bp.route("/api/background-status/<session_id>", methods=["GET"])
def get_background_status(session_id):
    """Get the status of background AI explanation processing for a session."""
    try:
        job_status = get_job_status(session_id)

        if job_status:
            return jsonify({"status": "success", "job_status": job_status}), 200
        else:
            return (
                jsonify(
                    {
                        "status": "not_found",
                        "message": "No background job found for this session",
                    }
                ),
                404,
            )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Error checking background status: {str(e)}",
                }
            ),
            500,
        )
