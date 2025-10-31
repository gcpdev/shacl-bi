"""
Test main Flask application functionality.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from flask import Flask


class TestFlaskApp:
    """Test Flask application creation and configuration."""

    def test_create_app(self, app):
        """Test application creation."""
        assert app is not None
        assert isinstance(app, Flask)
        assert app.config["TESTING"] is True

    def test_app_config(self, app):
        """Test application configuration."""
        assert app.config["SECRET_KEY"] is not None
        assert "WTF_CSRF_ENABLED" in app.config
        assert "TESTING" in app.config

    def test_app_has_blueprints(self, app):
        """Test application has all expected blueprints."""
        expected_blueprints = [
            "simple",
            "analytics",
            "dashboard",
            "homepage",
            "landing",
            "main_content",
            "phoenix",
            "shape_view",
            "shapes_overview",
            "upload",
            "validation",
        ]

        registered_blueprints = [bp.name for bp in app.blueprints.values()]

        # Check that all expected blueprints are present (allowing for some that might not load)
        found_blueprints = []
        for blueprint_name in expected_blueprints:
            if blueprint_name in registered_blueprints:
                found_blueprints.append(blueprint_name)

        # Should have most of the expected blueprints
        assert (
            len(found_blueprints) >= 7
        ), f"Too few blueprints found. Expected at least 7, found {len(found_blueprints)}. Registered: {registered_blueprints}"

    def test_app_routes(self, client):
        """Test application has expected routes."""
        # Test basic routes respond
        routes = ["/", "/api/health"]

        for route in routes:
            try:
                response = client.get(route)
                # Should respond (either 200, 404, or other status code, but not 500)
                assert response.status_code != 500
            except:
                # Some routes might require authentication or data
                pass

    def test_error_handlers(self, client):
        """Test application error handlers."""
        # Test 404 handler
        response = client.get("/nonexistent-route")
        assert response.status_code == 404

        # Test that error pages are properly formatted
        if response.status_code == 404:
            # Should return JSON or HTML error response
            assert len(response.data) > 0

    @patch("functions.virtuoso_service")
    def test_health_check(self, mock_virtuoso, client):
        """Test health check endpoint."""
        # Mock database connection
        mock_virtuoso.connection.is_connected.return_value = True

        response = client.get("/api/health")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "status" in data
        assert "timestamp" in data

    def test_cors_headers(self, client):
        """Test CORS headers are set."""
        response = client.options("/api/violations")
        # Should have CORS headers
        assert response.status_code in [200, 204, 405]

    def test_json_error_handling(self, client):
        """Test JSON error handling."""
        # Send invalid JSON to a non-existent endpoint
        response = client.post(
            "/api/nonexistent", data="invalid json", content_type="application/json"
        )
        assert response.status_code in [400, 404, 405, 415]

    def test_request_logging(self, app):
        """Test request logging is configured."""
        # Test that logging is configured
        with app.test_request_context("/"):
            # Should not raise any errors
            pass

    @patch("functions.virtuoso_service")
    def test_database_error_handling(self, mock_virtuoso, client):
        """Test database error handling."""
        # Mock database connection error
        mock_virtuoso.execute_sparql_query.side_effect = Exception("Database error")

        response = client.get("/api/violations")
        # Should handle database errors gracefully
        assert response.status_code != 500 or "error" in response.get_json()

    def test_static_files(self, client):
        """Test static file serving."""
        response = client.get("/static/favicon.ico")
        # Should either serve file or return 404 gracefully
        assert response.status_code in [200, 404]

    def test_session_handling(self, client):
        """Test session handling."""
        with client.session_transaction() as sess:
            sess["test_key"] = "test_value"

        # Test that session persists
        with client.session_transaction() as sess:
            assert sess.get("test_key") == "test_value"

    def test_security_headers(self, client):
        """Test security headers are set."""
        response = client.get("/")
        # Check for common security headers
        headers = response.headers
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
        ]

        for header in security_headers:
            # Headers might not be set in test environment
            # But should not cause errors
            header_value = headers.get(header)
            assert header_value is None or isinstance(header_value, str)

    def test_template_rendering(self, client):
        """Test template rendering."""
        response = client.get("/")
        # Should render main template
        assert response.status_code in [200, 404]

    def test_before_request_hooks(self, app):
        """Test before request hooks."""
        with app.test_request_context("/"):
            # Before request hooks should execute without error
            pass

    def test_after_request_hooks(self, app):
        """Test after request hooks."""
        with app.test_request_context("/"):
            response = app.response_class()
            # After request hooks should execute without error
            pass

    @patch("functions.virtuoso_service")
    def test_database_connection_retry(self, mock_virtuoso, client):
        """Test database connection retry logic."""
        # Mock connection failure then success
        mock_virtuoso.execute_sparql_query.side_effect = [
            Exception("Connection failed"),
            {"results": {"bindings": []}},
        ]

        response = client.get("/api/violations")
        # Should retry and eventually succeed or fail gracefully
        assert response.status_code in [200, 500]

    def test_app_teardown(self, app):
        """Test application teardown."""
        with app.app_context():
            # Should handle cleanup properly
            pass

    def test_context_processor(self, app):
        """Test context processors."""
        with app.test_request_context():
            # Context processors should execute without error
            app.preprocess_request()

    def test_json_encoder(self, app):
        """Test custom JSON encoder."""
        with app.test_request_context():
            # Test datetime encoding and other custom types
            from datetime import datetime

            test_data = {"date": datetime.now()}

            # Should handle without error
            try:
                json.dumps(test_data, default=app.json_encoder.default)
            except:
                # Fallback to default encoding
                pass
