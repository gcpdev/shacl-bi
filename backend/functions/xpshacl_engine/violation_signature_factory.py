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


def create_violation_signature(violation: ConstraintViolation) -> ViolationSignature:
    """
    Creates a signature for a violation, attempting to generalize from the specific
    instance to the underlying rule.
    """
    # By default, the signature is based on the constraint component and property path
    constraint_id = violation.constraint_id
    property_path = violation.property_path

    # A more advanced implementation could normalize these values further.
    # For example, removing shape-specific identifiers if they are not relevant.

    constraint_params = _extract_constraint_params(violation)

    return ViolationSignature(
        constraint_id=constraint_id,
        property_path=property_path,
        violation_type=violation.violation_type.value,
        constraint_params=constraint_params,
    )