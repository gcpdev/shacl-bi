from flask import Flask, send_file, abort, current_app
from flask_cors import CORS
import os
import subprocess
import logging
import atexit

# Configure logging to reduce noise from LiteLLM
logging.getLogger("litellm").setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.INFO)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

STATIC_FOLDER = "static"
VUE_SOURCE_FOLDER = os.path.abspath("../frontend")

# Global flag to ensure background processor starts only once
_background_processor_started = False


def create_app(config_name="development"):
    """Application factory pattern."""
    app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path="")

    # Configuration
    if config_name == "testing":
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SECRET_KEY"] = "test-secret-key"
    else:
        app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
        app.config["WTF_CSRF_ENABLED"] = True

    # Enable CORS for all routes
    CORS(app)

    # Register all available blueprints
    try:
        from routes.dashboard_routes import dashboard_bp

        app.register_blueprint(dashboard_bp)
    except ImportError:
        app.logger.warning("dashboard_routes not found")

    try:
        from routes.simple_routes import simple_bp

        app.register_blueprint(simple_bp)
    except ImportError:
        app.logger.warning("simple_routes not found")

    try:
        from routes.upload_routes import upload_bp

        app.register_blueprint(upload_bp)
    except ImportError:
        app.logger.warning("upload_routes not found")

    try:
        from routes.landing_routes import landing_bp

        app.register_blueprint(landing_bp)
    except ImportError:
        app.logger.warning("landing_routes not found")

    try:
        from routes.shape_view_routes import shape_view_bp

        app.register_blueprint(shape_view_bp)
    except ImportError:
        app.logger.warning("shape_view_routes not found")

    try:
        from routes.shapes_overview_routes import shapes_overview_bp

        app.register_blueprint(shapes_overview_bp)
    except ImportError:
        app.logger.warning("shapes_overview_routes not found")

    try:
        from routes.validation_routes import validation_bp

        app.register_blueprint(validation_bp)
    except ImportError:
        app.logger.warning("validation_routes not found")

    try:
        from routes.analytics_routes import analytics_bp

        app.register_blueprint(analytics_bp)
    except ImportError:
        app.logger.warning("analytics_routes not found")

    try:
        from routes.main_content_routes import main_content_bp

        app.register_blueprint(main_content_bp)
    except ImportError:
        app.logger.warning("main_content_routes not found")

    try:
        from routes.phoenix_routes import phoenix_bp

        app.register_blueprint(phoenix_bp)
    except ImportError:
        app.logger.warning("phoenix_routes not found")

    try:
        from routes.homepage_routes import homepage_bp

        app.register_blueprint(homepage_bp)
    except ImportError:
        app.logger.warning("homepage_routes not found")
    try:
        from routes.background_routes import background_bp

        app.register_blueprint(background_bp)
    except ImportError:
        app.logger.warning("background_routes not found")

    # Register main routes
    register_routes(app)

    # Register error handlers
    register_error_handlers(app)

    # Start background AI explanation processor for non-direct execution
    global _background_processor_started
    if config_name != "testing" and not _background_processor_started:
        try:
            from functions.background_processor import start_background_processor
            start_background_processor()
            _background_processor_started = True
            app.logger.info("Background AI explanation processor started")
            print("Background AI explanation processor started")
        except ImportError:
            app.logger.warning("Background processor not available")
            print("Warning: Background processor not available")
        except Exception as e:
            app.logger.error(f"Error starting background processor: {e}")
            print(f"Error starting background processor: {e}")

    return app


def register_routes(app):
    """Register main application routes."""

    @app.route("/")
    def serve_index():
        index_path = os.path.join(app.static_folder, "index.html")
        if os.path.exists(index_path):
            return send_file(index_path)
        else:
            abort(404)

    @app.route("/api/health")
    def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": (
                str(subprocess.check_output(["date"], text=True).strip())
                if os.name != "nt"
                else "timestamp"
            ),
        }


def register_error_handlers(app):
    """Register error handlers."""

    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Not found"}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {"error": "Internal server error"}, 500

    @app.errorhandler(400)
    def bad_request(error):
        return {"error": "Bad request"}, 400


# For direct execution (backward compatibility)
def build_frontend():
    """Build frontend if needed."""
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


# Create app instance for direct execution
app = create_app()

if __name__ == "__main__":
    # Start background AI explanation processor
    try:
        from functions.background_processor import start_background_processor
        start_background_processor()
        print("Background AI explanation processor started")
    except ImportError:
        print("Warning: Background processor not available")
    except Exception as e:
        print(f"Error starting background processor: {e}")

    # The build_frontend function is not called here because the Dockerfile handles the build.
    try:
        app.run(debug=True, host="0.0.0.0", port=80)
    finally:
        # Stop background processor on shutdown
        try:
            from functions.background_processor import stop_background_processor
            stop_background_processor()
            print("Background AI explanation processor stopped")
        except ImportError:
            pass
        except Exception as e:
            print(f"Error stopping background processor: {e}")
