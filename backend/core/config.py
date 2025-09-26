"""Unified configuration management."""

import os

# Core Configuration
VIRTUOSO_ENDPOINT = os.environ.get('VIRTUOSO_ENDPOINT', 'http://localhost:8890/sparql')
SHAPES_GRAPH = os.environ.get('SHAPES_GRAPH', 'http://ex.org/ShapesGraph')
VALIDATION_GRAPH = os.environ.get('VALIDATION_GRAPH', 'http://ex.org/ValidationReport')
VIOLATION_KG_GRAPH = os.environ.get('VIOLATION_KG_GRAPH', 'http://ex.org/ViolationKnowledgeGraph')

# Application Settings
DEFAULT_AI_MODEL = os.environ.get('DEFAULT_AI_MODEL', 'openai/gpt-4')
FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
ENABLE_XPSHACL_FEATURES = os.environ.get('ENABLE_XPSHACL_FEATURES', 'true').lower() == 'true'
ENABLE_DASHBOARD_FEATURES = os.environ.get('ENABLE_DASHBOARD_FEATURES', 'true').lower() == 'true'
SECRET_KEY = os.environ.get('SECRET_KEY', 'my_precious_secret_key')

# Providers Key
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
