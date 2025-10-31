# violation_signature_factory.py
from typing import Dict
from .xpshacl_architecture import ConstraintViolation
from .violation_signature import ViolationSignature


def _extract_constraint_params(violation: ConstraintViolation) -> Dict[str, str]:
    """
    Extracts known SHACL parameters from the violation's context
    to create a more specific but still generalizable signature.
    """
    params: Dict[str, str] = {}
    # This is a simple example. A more robust implementation would inspect
    # the violation's constraint_id and decide which params to look for.
    if violation.context:
        for key, value in violation.context.items():
            # Generalize by ignoring node-specific values and focusing on the rules.
            if key in [
                "sh:minCount",
                "sh:maxCount",
                "sh:pattern",
                "sh:flags",
                "sh:class",
                "sh:datatype",
                "sh:nodeKind",
            ]:
                params[key] = str(value)
    return params


def _normalize_constraint_id(constraint_id: str) -> str:
    """
    Normalize constraint IDs to consistent prefixed form.
    Converts full URIs to prefixed form for consistency.
    """
    if not constraint_id:
        return constraint_id

    # Define common SHACL namespace mappings
    namespace_mappings = {
        "http://www.w3.org/ns/shacl#": "sh:",
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf:",
        "http://www.w3.org/2000/01/rdf-schema#": "rdfs:",
        "http://www.w3.org/2001/XMLSchema#": "xsd:",
        "http://www.w3.org/2002/07/owl#": "owl:",
    }

    # Convert full URI to prefixed form
    for uri, prefix in namespace_mappings.items():
        if constraint_id.startswith(uri):
            return constraint_id.replace(uri, prefix)

    # If no mapping found, return as-is
    return constraint_id


def _normalize_property_path(property_path: str) -> str:
    """
    Normalize property paths to consistent format.
    Handles empty values and ensures consistent formatting.
    """
    if not property_path or property_path.strip() == "":
        return None
    return property_path.strip()


def _normalize_violation_type(violation_type) -> str:
    """
    Normalize violation types to consistent format.
    Handle enum values and None cases.
    """
    if violation_type is None:
        return None
    if hasattr(violation_type, "value"):
        return violation_type.value
    return str(violation_type)


def create_violation_signature(violation: ConstraintViolation) -> ViolationSignature:
    """
    Creates a signature for a violation, attempting to generalize from the specific
    instance to the underlying rule.
    """
    # Normalize constraint ID to prefixed form for consistency
    constraint_id = _normalize_constraint_id(violation.constraint_id)

    # Normalize property path
    property_path = _normalize_property_path(violation.property_path)

    # A more advanced implementation could normalize these values further.
    # For example, removing shape-specific identifiers if they are not relevant.

    constraint_params = _extract_constraint_params(violation)

    # Normalize violation type
    violation_type_value = _normalize_violation_type(violation.violation_type)

    return ViolationSignature(
        constraint_id=constraint_id,
        property_path=property_path,
        violation_type=violation_type_value,
        constraint_params=constraint_params,
    )
