# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class BaseConfig:
    """Base configuration."""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    WTF_CSRF_ENABLED = True

    # Database configuration
    VIRTUOSO_ENDPOINT = os.environ.get('VIRTUOSO_ENDPOINT', 'http://localhost:8890/sparql')
    SHAPES_GRAPH = os.environ.get('SHAPES_GRAPH', 'http://ex.org/ShapesGraph')
    VALIDATION_GRAPH = os.environ.get('VALIDATION_GRAPH', 'http://ex.org/ValidationReport')
    VIOLATION_KG_GRAPH = os.environ.get('VIOLATION_KG_GRAPH', 'http://ex.org/ViolationKnowledgeGraph')
    DATABASE_URL = VIRTUOSO_ENDPOINT

    # CORS settings
    CORS_ORIGINS = ["*"]
    CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS = ["Content-Type", "Authorization"]

    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'

    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'app.log'

class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(BaseConfig):
    """Production configuration."""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

class TestingConfig(BaseConfig):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'

    # Use test endpoints
    VIRTUOSO_ENDPOINT = 'http://localhost:8890/sparql'

    # Disable logging during tests
    LOG_LEVEL = 'ERROR'

# Configuration mapping
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Core Configuration
VIRTUOSO_ENDPOINT = os.environ.get('VIRTUOSO_ENDPOINT', 'http://localhost:8890/sparql')
SHAPES_GRAPH = os.environ.get('SHAPES_GRAPH', 'http://ex.org/ShapesGraph')
VALIDATION_GRAPH = os.environ.get('VALIDATION_GRAPH', 'http://ex.org/ValidationReport')
VIOLATION_KG_GRAPH = os.environ.get('VIOLATION_KG_GRAPH', 'http://ex.org/ViolationKnowledgeGraph')

# SPARQL endpoint configuration
ENDPOINT_URL = VIRTUOSO_ENDPOINT

# Authentication settings (if needed)
USERNAME = os.environ.get('VIRTUOSO_USER')
PASSWORD = os.environ.get('VIRTUOSO_PASSWORD')
AUTH_REQUIRED = USERNAME is not None and PASSWORD is not None

# Triple store type - used to handle store-specific operations
TRIPLE_STORE_TYPE = "virtuoso"  # Options: "virtuoso", "fuseki", "stardog", etc.

# Graph URIs
SHAPES_GRAPH_URI = SHAPES_GRAPH
VALIDATION_REPORT_URI = VALIDATION_GRAPH

# Application Settings
DEFAULT_AI_MODEL = os.environ.get('DEFAULT_AI_MODEL', 'openai/gpt-4')
FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
ENABLE_XPSHACL_FEATURES = os.environ.get('ENABLE_XPSHACL_FEATURES', 'true').lower() == 'true'
ENABLE_DASHBOARD_FEATURES = os.environ.get('ENABLE_DASHBOARD_FEATURES', 'true').lower() == 'true'

# LLM Configuration
SRG_MODEL = os.environ.get("SRG_MODEL", DEFAULT_AI_MODEL)

# Providers Key - should be configured in a .env file only
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# File paths for the Violation Knowledge Graph
VIOLATION_KG_ONTOLOGY_PATH = "data/xpshacl_ontology.ttl"
VIOLATION_KG_PATH = "data/phoenix_violation_kg.ttl"

# SHACL Constraints and Features
SHACL_FEATURES = [
    "http://www.w3.org/ns/shacl#class",
    "http://www.w3.org/ns/shacl#datatype",
    "http://www.w3.org/ns/shacl#NodeKind",
    "http://www.w3.org/ns/shacl#minCount",
    "http://www.w3.org/ns/shacl#maxCount",
    "http://www.w3.org/ns/shacl#minExclusive",
    "http://www.w3.org/ns/shacl#minInclusive",
    "http://www.w3.org/ns/shacl#maxExclusive",
    "http://www.w3.org/ns/shacl#maxInclusive",
    "http://www.w3.org/ns/shacl#minLength",
    "http://www.w3.org/ns/shacl#maxLength",
    "http://www.w3.org/ns/shacl#pattern",
    "http://www.w3.org/ns/shacl#languageIn",
    "http://www.w3.org/ns/shacl#uniqueLang",
    "http://www.w3.org/ns/shacl#equals",
    "http://www.w3.org/ns/shacl#disjoint",
    "http://www.w3.org/ns/shacl#lessThan",
    "http://www.w3.org/ns/shacl#lessThanOrEquals",
    "http://www.w3.org/ns/shacl#not",
    "http://www.w3.org/ns/shacl#and",
    "http://www.w3.org/ns/shacl#or",
    "http://www.w3.org/ns/shacl#xone",
    "http://www.w3.org/ns/shacl#node",
    "http://www.w3.org/ns/shacl#qualifiedMinCount",
    "http://www.w3.org/ns/shacl#qualifiedMaxCount",
    "http://www.w3.org/ns/shacl#closed",
    "http://www.w3.org/ns/shacl#hasValue",
    "http://www.w3.org/ns/shacl#in"
]

# Docker-related settings (for Virtuoso)
DATA_DIR_IN_DOCKER = "/data"  # Directory in Docker container
DOCKER_CONTAINER_NAME = "virtuoso"  # Name of the Docker container

# Store-specific configuration
STORE_CONFIG = {
    "virtuoso": {
        "isql_path": "/usr/local/virtuoso-opensource/bin/isql",  # Only needed for Virtuoso
        "isql_port": 1111,
        "bulk_load_enabled": True,
    },
    "fuseki": {
        "admin_endpoint": "http://localhost:3030/$/",  # Example for Fuseki
        "bulk_load_enabled": False,
    },
    "stardog": {
        "admin_endpoint": "http://localhost:5820",  # Example for Stardog
        "database": "shacldb",
        "bulk_load_enabled": True,
    }
}


def update_graphs(shapes_graph_name, validation_report_name):
    global SHAPES_GRAPH_URI, VALIDATION_REPORT_URI
    if shapes_graph_name:
        SHAPES_GRAPH_URI = shapes_graph_name
    if validation_report_name:
        VALIDATION_REPORT_URI = validation_report_name