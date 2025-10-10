from flask import Flask, send_file, abort
from flask_cors import CORS
import os
import subprocess
import logging

# Configure logging to reduce noise from LiteLLM
logging.getLogger("litellm").setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from routes.landing_routes import landing_bp
from routes.shape_view_routes import shape_view_bp
from routes.shapes_overview_routes import shapes_overview_bp
from routes.validation_routes import validation_bp
from routes.analytics_routes import analytics_bp
from routes.main_content_routes import main_content_bp
from routes.phoenix_routes import phoenix_bp
from functions import virtuoso_service

STATIC_FOLDER = os.path.abspath(os.path.join("..", "frontend", "dist"))
VUE_SOURCE_FOLDER = os.path.abspath("../frontend")

app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path="")

# Enable CORS for all routes
CORS(app)

# Register blueprints
app.register_blueprint(landing_bp)
app.register_blueprint(shape_view_bp)
app.register_blueprint(shapes_overview_bp)
app.register_blueprint(validation_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(main_content_bp)
app.register_blueprint(phoenix_bp)

@app.route("/api/debug-user")
def debug_user():
    query = "SELECT (bif:SESSION_USER() AS ?currentUser) WHERE {}"
    try:
        results = virtuoso_service.execute_sparql_query(query)
        return str(results)
    except Exception as e:
        return str(e)


def build_frontend():
    print("Checking if frontend needs to be built...")
    index_path = os.path.join(STATIC_FOLDER, "index.html")
    if not os.path.exists(index_path):
        print("Building the Vue.js frontend...")
        try:
            subprocess.check_call(["npm", "install"], cwd=VUE_SOURCE_FOLDER)
            subprocess.check_call(["npm", "run", "build"], cwd=VUE_SOURCE_FOLDER)
            print("Frontend built successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error building frontend: {e}")
            raise


@app.route("/")
def serve_index():
    index_path = os.path.join(STATIC_FOLDER, "index.html")
    if os.path.exists(index_path):
        return send_file(index_path)
    else:
        abort(404)


if __name__ == "__main__":
    #if os.environ.get("DOCKER_ENV") is None:
    #    build_frontend()
    app.run(debug=True, host="0.0.0.0", port=80, threaded=True)
