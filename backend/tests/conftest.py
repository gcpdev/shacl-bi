"""
Pytest configuration and fixtures for SHACL-BI backend tests.
Provides common test setup, mocking, and utilities.
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch
from flask import Flask

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture(scope="session")
def app():
    """Create test Flask application."""
    from app import create_app
    app = create_app(config_name='testing')
    return app

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create CLI test runner."""
    return app.test_cli_runner()

@pytest.fixture
def mock_virtuoso_service():
    """Mock virtuoso service for database operations."""
    with patch('functions.virtuoso_service') as mock:
        # Mock execute_sparql_query
        mock.execute_sparql_query.return_value = {
            "results": {
                "bindings": []
            }
        }

        # Mock execute_sparql_update
        mock.execute_sparql_update.return_value = {"affected_triples": 1}

        # Mock connection
        mock.connection = Mock()
        mock.connection.is_connected.return_value = True

        yield mock

@pytest.fixture
def mock_phoenix_service():
    """Mock phoenix service for enhanced explanations."""
    with patch('functions.phoenix_service') as mock:
        # Mock explanation cache
        mock.explanation_cache = {}

        # Mock VKG operations
        mock.load_vkg_from_virtuoso.return_value = None
        mock.create_violation_signature.return_value = "test_signature"

        yield mock

@pytest.fixture
def sample_violation():
    """Sample violation data for testing."""
    return {
        "focus_node": "http://example.org/resource1",
        "resultPath": "http://example.org/ns#name",
        "value": "invalid_value",
        "resultMessage": "Constraint violation",
        "sourceConstraintComponent": "http://www.w3.org/ns/shacl#PatternConstraintComponent",
        "sourceShape": "http://example.org/shapes/PersonShape",
        "severity": "http://www.w3.org/ns/shacl#Violation",
        "context": {
            "pattern": "^[A-Z][a-z]+$",
            "exampleValue": "Example"
        }
    }

@pytest.fixture
def sample_session_data():
    """Sample session data for testing."""
    return {
        "session_id": "test_session_123",
        "validation_graph_uri": "http://ex.org/ValidationReport/Session_test_session_123",
        "shapes_graph_uri": "http://ex.org/ShapesGraph",
        "data_graph_uri": "http://ex.org/DataGraph"
    }

@pytest.fixture
def sample_shapes_ttl():
    """Sample SHACL shapes data in TTL format."""
    return """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.org/ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:PersonShape a sh:NodeShape ;
    sh:targetClass ex:Person ;
    sh:property [
        sh:path ex:name ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path ex:email ;
        sh:pattern "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\\\.[a-zA-Z]{2,}$" ;
    ] ;
    sh:property [
        sh:path ex:age ;
        sh:datatype xsd:integer ;
        sh:minInclusive 0 ;
        sh:maxInclusive 150 ;
    ] ;
    sh:property [
        sh:path ex:status ;
        sh:in ("Active" "Inactive" "Pending") ;
    ] .
    """

@pytest.fixture
def sample_data_ttl():
    """Sample RDF data in TTL format."""
    return """
@prefix ex: <http://example.org/ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:person1 a ex:Person ;
    ex:name "John Doe" ;
    ex:email "john@example.com" ;
    ex:age 30 ;
    ex:status "Active" .

ex:person2 a ex:Person ;
    ex:name "" ;
    ex:email "invalid-email" ;
    ex:age -5 ;
    ex:status "Unknown" .
    """

@pytest.fixture
def mock_graph():
    """Mock RDF graph for testing."""
    from rdflib import Graph, Literal, URIRef, Namespace
    import rdflib

    g = Graph()
    ex = Namespace("http://example.org/ns#")
    sh = Namespace("http://www.w3.org/ns/shacl#")
    xsd = Namespace("http://www.w3.org/2001/XMLSchema#")

    # Add some sample triples
    g.add((ex.person1, rdflib.RDF.type, ex.Person))
    g.add((ex.person1, ex.name, Literal("John Doe")))
    g.add((ex.person1, ex.age, Literal(30, datatype=xsd.integer)))

    return g

@pytest.fixture
def mock_constraint_violation():
    """Mock constraint violation object."""
    class MockConstraintViolation:
        def __init__(self):
            self.focus_node = "http://example.org/person1"
            self.shape_id = "http://example.org/shapes/PersonShape"
            self.constraint_id = "http://www.w3.org/ns/shacl#MinCountConstraintComponent"
            self.violation_type = "CARDINALITY"
            self.property_path = "http://example.org/ns#name"
            self.value = None
            self.context = {}

    return MockConstraintViolation()

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("DATABASE_URL", "mock://localhost:1111")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")

@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    file_path = tmp_path / "test_file.ttl"
    file_path.write_text("@prefix ex: <http://example.org/> . ex:test ex:property 'value' .")
    return str(file_path)

@pytest.fixture
def multipart_file_data():
    """Sample multipart file data for upload testing."""
    return {
        'file': ('test.ttl', '@prefix ex: <http://example.org/> . ex:test ex:property "value" .', 'text/turtle')
    }

# Helper functions for tests
def create_mock_query_result(bindings=None):
    """Create mock SPARQL query result."""
    if bindings is None:
        bindings = []

    return {
        "results": {
            "bindings": bindings
        }
    }

def create_mock_binding(**kwargs):
    """Create mock SPARQL result binding."""
    return {
        key: {"value": value} for key, value in kwargs.items()
    }

# Coverage configuration
def pytest_configure(config):
    """Configure pytest for coverage."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )