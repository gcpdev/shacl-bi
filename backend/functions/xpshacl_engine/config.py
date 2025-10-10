import os

# File paths for the Violation Knowledge Graph
VIOLATION_KG_ONTOLOGY_PATH = "data/xpshacl_ontology.ttl"
VIOLATION_KG_PATH = "data/phoenix_violation_kg.ttl"

# LLM Configuration
# The model is now read from the .env file, with a default fallback.
SRG_MODEL = os.environ.get("SRG_MODEL", "gpt-5-2025-08-07")
