# simple_routes.py - Simple API endpoints without xpshacl dependencies
from flask import Blueprint, jsonify, request
from functions.logging_config import get_logger
from functions import virtuoso_service
from functions.phoenix_service import explanation_cache, load_vkg_from_virtuoso
from functions.xpshacl_engine.violation_signature_factory import (
    create_violation_signature,
)
from functions.xpshacl_engine.repair_engine import SuggestionRepairGenerator
import re
from datetime import datetime
import exrex

simple_bp = Blueprint("simple", __name__)
logger = get_logger(__name__)


@simple_bp.route("/api/violations", methods=["GET"])
def get_violations():
    """
    Get violations from Virtuoso with session-specific tenant isolation
    Returns violations from session-specific named graphs in Virtuoso
    """
    try:
        # Check for session_id parameter for tenant isolation
        session_id = request.args.get("session_id")
        if session_id:
            validation_graph_uri = (
                f"http://ex.org/ValidationReport/Session_{session_id}"
            )
        else:
            # Fallback to default graph for backward compatibility
            validation_graph_uri = "http://ex.org/ValidationReport"

        logger.info(f"Querying violations from database: {validation_graph_uri}")

        # Use the same virtuoso_service that the dashboard uses

        # Use the exact same query that works in our testing
        query = f"""
        SELECT ?violation ?focusNode ?resultMessage ?resultPath ?resultSeverity ?sourceConstraintComponent ?value ?sourceShape
        FROM <{validation_graph_uri}>
        WHERE {{
            ?violation a <http://www.w3.org/ns/shacl#ValidationResult> .
            OPTIONAL {{ ?violation <http://www.w3.org/ns/shacl#focusNode> ?focusNode . }}
            OPTIONAL {{ ?violation <http://www.w3.org/ns/shacl#resultMessage> ?resultMessage . }}
            OPTIONAL {{ ?violation <http://www.w3.org/ns/shacl#resultPath> ?resultPath . }}
            OPTIONAL {{ ?violation <http://www.w3.org/ns/shacl#resultSeverity> ?resultSeverity . }}
            OPTIONAL {{ ?violation <http://www.w3.org/ns/shacl#sourceConstraintComponent> ?sourceConstraintComponent . }}
            OPTIONAL {{ ?violation <http://www.w3.org/ns/shacl#value> ?value . }}
            OPTIONAL {{ ?violation <http://www.w3.org/ns/shacl#sourceShape> ?sourceShape . }}
        }}
        """

        results = virtuoso_service.execute_sparql_query(query)
        violations_data = []

        for result in results["results"]["bindings"]:
            # Extract basic violation info
            violation = {
                "focus_node": result.get("focusNode", {}).get("value", ""),
                "message": result.get("resultMessage", {}).get("value", ""),
                "property_path": result.get("resultPath", {}).get("value", ""),
                "severity": result.get("resultSeverity", {}).get("value", ""),
                "constraint_id": result.get("sourceConstraintComponent", {}).get(
                    "value", ""
                ),
                "value": result.get("value", {}).get("value", ""),
                "shape_id": result.get("sourceShape", {}).get("value", ""),
                "violation_type": "other",
            }

            # Add PHOENIX-style context information
            violation["context"] = _get_violation_context(violation, session_id)

            violations_data.append(violation)

        logger.info(f"Database query returned {len(violations_data)} violations")

        # Standard prefixes for common namespaces
        prefixes = {
            "sh": "http://www.w3.org/ns/shacl#",
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "ex": "http://example.org/",
        }

        return (
            jsonify(
                {
                    "violations": violations_data,
                    "prefixes": prefixes,
                    "session_id": session_id,
                    "validation_graph_uri": validation_graph_uri,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting violations: {str(e)}")
        return jsonify({"error": f"Failed to retrieve violations: {str(e)}"}), 500


@simple_bp.route("/api/explanations/<session_id>", methods=["GET"])
def get_explanations(session_id):
    """
    Get enhanced explanations for violations in a session
    Returns AI-generated explanations if available, otherwise basic ones
    """
    try:

        # Check if we have enhanced explanations in the cache
        if session_id in explanation_cache:
            explanations = explanation_cache[session_id]
            logger.info(
                f"Found {len(explanations)} cached explanations for session {session_id}"
            )
            return (
                jsonify(
                    {
                        "explanations": explanations,
                        "session_id": session_id,
                        "has_enhanced": True,
                    }
                ),
                200,
            )

        # If no enhanced explanations available, return empty
        return (
            jsonify(
                {
                    "explanations": [],
                    "session_id": session_id,
                    "has_enhanced": False,
                    "message": "No enhanced explanations available yet",
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting explanations: {str(e)}")
        return jsonify({"error": f"Failed to retrieve explanations: {str(e)}"}), 500


@simple_bp.route("/api/explanation", methods=["POST"])
def generate_explanation():
    """
    Generate explanation for a specific violation
    """
    logger.info(f"🚨 EXPLANATION API CALLED - FUNCTION STARTED")
    try:
        data = request.get_json()
        violation = data.get("violation", {})
        session_id = data.get("session_id")

        if not violation:
            return jsonify({"error": "Violation data is required"}), 400

        logger.info(f"Generating explanation for violation: {violation}")

        # Try to use PHOENIX if available, but fallback to basic explanation
        try:
            logger.info(f"🚀 Starting PHOENIX enhanced explanation generation")
            # Try to import and use PHOENIX service

            # Convert dict to violation-like object
            class ViolationObj:
                def __init__(self, **kwargs):
                    for key, value in kwargs.items():
                        setattr(self, key, value)

            logger.info(f"🔧 Creating violation object from: {violation}")
            v_obj = ViolationObj(**violation)
            v_obj.constraint_id = violation.get("constraint_id")
            v_obj.property_path = violation.get("property_path")
            v_obj.violation_type = violation.get("violation_type")
            v_obj.context = violation.get(
                "context", {}
            )  # Ensure context attribute exists
            logger.info(f"✅ Violation object created successfully")

            # Try to generate enhanced explanation
            logger.info(f"🔍 Loading VKG from Virtuoso...")
            vkg = load_vkg_from_virtuoso()
            logger.info(f"🔍 VKG loading result: {'SUCCESS' if vkg else 'FAILED'} - loaded {len(vkg.graph) if vkg and hasattr(vkg, 'graph') else 'unknown'} triples")

            if vkg:
                logger.info(f"🔧 Creating SuggestionRepairGenerator...")
                srg = SuggestionRepairGenerator(vkg=vkg)
                logger.info(f"✅ SuggestionRepairGenerator created successfully")

                logger.info(f"🔍 Creating violation signature...")
                signature = create_violation_signature(v_obj)
                logger.info(f"🔍 Looking up cached explanation for signature: {signature}")

                logger.info(f"🔍 Calling vkg.get_explanation()...")
                cached_explanation = vkg.get_explanation(signature)
                logger.info(f"🔍 VKG lookup result: {'FOUND' if cached_explanation else 'NOT FOUND'} for signature {signature}")

                if cached_explanation:
                    logger.info(f"🎉 FOUND cached explanation! Returning enhanced response...")
                    # Get real metadata from VKG using the signature

                if cached_explanation:
                    # Get real metadata from VKG using the signature
                    vkg_metadata = vkg.get_model_metadata(signature)

                    repair_object = {
                        "explanation_natural_language": cached_explanation.natural_language_explanation,
                        "suggestion_natural_language": "\n".join(
                            cached_explanation.correction_suggestions or []
                        ),
                        "proposed_repair": {
                            "query": cached_explanation.proposed_repair_query
                        },
                        "has_enhanced": True,
                        "metadata": {
                            "generated_by": vkg_metadata.get(
                                "model_name", "PHOENIX Violation Knowledge Graph"
                            ),
                            "model_version": vkg_metadata.get(
                                "model_version", "VKG-1.0"
                            ),
                            "source_vkg_graph": "http://ex.org/ViolationKnowledgeGraph",
                            "vkg_triples_count": vkg_metadata.get(
                                "vkg_triples_count",
                                len(vkg.graph) if hasattr(vkg, "graph") else "Unknown",
                            ),
                            "explanation_signature": signature,
                            "generated_timestamp": vkg_metadata.get(
                                "generated_at", datetime.now().isoformat()
                            ),
                            "confidence_level": _calculate_confidence(
                                cached_explanation, v_obj
                            ),
                            "constraint_signature": f"{constraint_id}:{property_path}",
                            "focus_node": focus_node,
                            "extraction_method": "cached_lookup",
                            "created_date": vkg_metadata.get("created_date", ""),
                            "modified_date": vkg_metadata.get("modified_date", ""),
                        },
                    }
                    logger.info(
                        f"Generated enhanced explanation with VKG metadata (providedByModel): {repair_object}"
                    )
                    return jsonify(repair_object), 200

        except ImportError as ie:
            logger.error(f"🚫 PHOENIX modules not available: {ie}")
            logger.error(f"🚫 Full exception traceback:", exc_info=True)
        except Exception as e:
            logger.error(f"🚫 Enhanced explanation generation failed: {e}")
            logger.error(f"🚫 Full exception traceback:", exc_info=True)

        # Fallback to basic explanation with enhanced context
        focus_node = violation.get("focus_node", "Unknown resource")
        constraint_id = violation.get("constraint_id", "Unknown constraint")
        message = violation.get("message", "Constraint violation detected")
        property_path = violation.get("property_path", "Unknown property")
        value = violation.get("value", "Unknown value")

        # Generate contextual information like PHOENIX does
        constraint_info = _get_constraint_info(
            constraint_id, property_path, value, session_id
        )

        # Generate more specific basic explanation based on constraint type
        constraint_name = (
            constraint_id.split("#")[-1]
            if "#" in constraint_id
            else constraint_id.split("/")[-1]
        )

        # Add metadata for fallback explanations
        basic_metadata = {
            "generated_by": "SHACL-BI Basic Explanation Engine",
            "model_version": "Basic-1.0",
            "extraction_method": "rule_based_generation",
            "generated_timestamp": datetime.now().isoformat(),
            "confidence_level": "Medium (rule-based inference)",
            "constraint_signature": f"{constraint_id}:{property_path}",
            "focus_node": focus_node,
            "constraint_type": constraint_name,
        }

        # More specific constraint detection - check for exact matches first
        if "mincount" in constraint_name.lower() and "count" in constraint_name.lower():
            explanation = f"This data record is incomplete. The '{property_path}' attribute is required but missing from '{focus_node}'."
            suggestion = f"Add a value for the '{property_path}' attribute to '{focus_node}' to complete the record."
            query = _generate_mincount_query(focus_node, property_path, session_id)
        elif (
            "maxcount" in constraint_name.lower() and "count" in constraint_name.lower()
        ):
            explanation = f"This data record has too many values. The '{property_path}' attribute for '{focus_node}' exceeds the maximum allowed number of values."
            suggestion = f"Remove extra values from the '{property_path}' attribute for '{focus_node}' to comply with the constraint."
            query = _generate_maxcount_query(
                focus_node, property_path, value, session_id
            )
        elif "datatype" in constraint_name.lower():
            explanation = f"This data record has an incorrect data type. The '{property_path}' attribute for '{focus_node}' should be a different data type than '{value}'."
            suggestion = f"Change the value of '{property_path}' for '{focus_node}' to the correct data type."
            query = _generate_datatype_query(
                focus_node, property_path, value, session_id
            )
        elif (
            "pattern" in constraint_name.lower()
            and "constraintcomponent" in constraint_name.lower()
        ):
            pattern = constraint_info.get("pattern", "")
            example = constraint_info.get("exampleValue", "")
            if pattern:
                explanation = f"The value '{value}' for '{property_path}' doesn't match the required pattern '{pattern}'."
                if example:
                    suggestion = f"Change the value to match the pattern. Example of a valid value: '{example}'."
                else:
                    suggestion = (
                        f"Change the value to match the required pattern '{pattern}'."
                    )
            else:
                explanation = f"The value for '{property_path}' doesn't match the required format."
                suggestion = f"Change the value to match the required format."
            query = _generate_pattern_query(
                focus_node, property_path, value, session_id, example
            )
        elif "inconstraintcomponent" in constraint_name.lower():
            allowed_values = constraint_info.get("allowedValues", [])
            if allowed_values:
                explanation = f"The value '{value}' for '{property_path}' is not in the list of allowed values."
                suggestion = f"Change the value to one of the allowed options: {', '.join(allowed_values)}."
            else:
                explanation = (
                    f"The value for '{property_path}' is not in the allowed list."
                )
                suggestion = f"Change the value to one of the allowed options."
            query = _generate_in_query(
                focus_node,
                property_path,
                value,
                session_id,
                allowed_values[0] if allowed_values else "CORRECT_VALUE",
            )
        elif "maxinclusive" in constraint_name.lower():
            max_value = constraint_info.get("maxValue", "")
            if max_value:
                explanation = f"The value '{value}' for '{property_path}' exceeds the maximum allowed value of {max_value}."
                suggestion = (
                    f"Change the value to be less than or equal to {max_value}."
                )
            else:
                explanation = f"The value '{value}' for '{property_path}' exceeds the maximum allowed value."
                suggestion = f"Change the value to be less than or equal to the maximum allowed value."
            query = _generate_maxcount_query(
                focus_node, property_path, value, session_id
            )
        elif "mininclusive" in constraint_name.lower():
            min_value = constraint_info.get("minValue", "")
            if min_value:
                explanation = f"The value '{value}' for '{property_path}' is below the minimum allowed value of {min_value}."
                suggestion = (
                    f"Change the value to be greater than or equal to {min_value}."
                )
            else:
                explanation = f"The value '{value}' for '{property_path}' is below the minimum allowed value."
                suggestion = f"Change the value to be greater than or equal to the minimum allowed value."
            query = _generate_mincount_query(focus_node, property_path, session_id)
        elif "lessthanorequals" in constraint_name.lower():
            explanation = f"The value '{value}' for '{property_path}' violates the less-than-or-equals constraint."
            suggestion = (
                f"Change the value to be less than or equal to the required value."
            )
            query = _generate_maxcount_query(
                focus_node, property_path, value, session_id
            )
        else:
            explanation = f"The data record '{focus_node}' violates a quality constraint. The '{property_path}' attribute with value '{value}' doesn't meet requirements."
            suggestion = f"Review and correct the '{property_path}' value for '{focus_node}' to ensure data quality."
            # Don't provide a broken query - let the user handle it manually or through the interface
            query = None

        basic_explanation = {
            "explanation_natural_language": explanation,
            "suggestion_natural_language": suggestion,
            "proposed_repair": {"query": query.strip() if query else None},
            "has_enhanced": False,
            "constraint_info": constraint_info,  # Add contextual information
            "metadata": basic_metadata,
        }

        logger.info(f"Generated basic explanation: {basic_explanation}")
        return jsonify(basic_explanation), 200

    except Exception as e:
        logger.error(f"Error generating explanation: {str(e)}")
        return jsonify({"error": f"Failed to generate explanation: {str(e)}"}), 500


@simple_bp.route("/api/repair", methods=["POST"])
def apply_repair():
    """
    Apply a repair suggestion to fix a violation
    """
    try:
        data = request.get_json()
        repair_query = data.get("repair_query", "")
        session_id = data.get("session_id")

        if not repair_query:
            return jsonify({"error": "Repair query is required"}), 400

        if not session_id:
            return (
                jsonify({"error": "Session ID is required for applying repairs"}),
                400,
            )

        # Use virtuoso_service to execute the repair

        # Execute the repair query
        result = virtuoso_service.execute_sparql_update(repair_query)

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Repair applied successfully",
                    "affected_triples": (
                        result.get("affected_triples", 0)
                        if isinstance(result, dict)
                        else 0
                    ),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error applying repair: {str(e)}")
        return (
            jsonify({"success": False, "error": f"Failed to apply repair: {str(e)}"}),
            500,
        )


# Helper functions for enhanced contextual explanations (similar to PHOENIX approach)
def _get_constraint_info(constraint_id, property_path, value, session_id):
    """
    Generate contextual information for constraints, similar to how PHOENIX provides regex examples
    """
    constraint_info = {
        "constraint_type": constraint_id,
        "property_path": property_path,
        "current_value": value,
    }

    constraint_name = (
        constraint_id.split("#")[-1]
        if "#" in constraint_id
        else constraint_id.split("/")[-1]
    )

    # Handle pattern constraints with exrex-like functionality
    if "pattern" in constraint_name.lower():
        # Try to extract pattern from shapes graph if available
        try:

            pattern_query = f"""
            SELECT ?pattern
            FROM <http://ex.org/ShapesGraph>
            WHERE {{
                ?shape <http://www.w3.org/ns/shacl#pattern> ?pattern .
                ?shape <http://www.w3.org/ns/shacl#path> <{property_path}> .
            }}
            LIMIT 1
            """
            results = virtuoso_service.execute_sparql_query(pattern_query)
            if results["results"]["bindings"]:
                pattern = results["results"]["bindings"][0]["pattern"]["value"]
                constraint_info["pattern"] = pattern

                # Generate example value (similar to exrex.getone())
                example_value = _generate_pattern_example(pattern)
                if example_value:
                    constraint_info["exampleValue"] = example_value
        except Exception as e:
            logger.warning(f"Could not extract pattern info: {e}")

    # Handle minInclusive constraints with range information
    elif "mininclusive" in constraint_name.lower():
        try:

            min_query = f"""
            SELECT ?minValue
            FROM <http://ex.org/ShapesGraph>
            WHERE {{
                ?shape <http://www.w3.org/ns/shacl#minInclusive> ?minValue .
                ?shape <http://www.w3.org/ns/shacl#path> <{property_path}> .
            }}
            LIMIT 1
            """
            results = virtuoso_service.execute_sparql_query(min_query)
            if results["results"]["bindings"]:
                min_value_str = results["results"]["bindings"][0]["minValue"]["value"]
                constraint_info["minValue"] = min_value_str

                # Generate a range of reasonable values above the minimum
                try:
                    # Try to parse as integer or decimal
                    if "." in min_value_str:
                        min_num = float(min_value_str)
                        allowed_values = [str(min_num + i * 0.5) for i in range(1, 6)]
                    else:
                        min_num = int(min_value_str)
                        allowed_values = [str(min_num + i) for i in range(1, 6)]

                    constraint_info["allowedValues"] = allowed_values
                    constraint_info["constraintType"] = "minInclusive"
                except ValueError:
                    logger.warning(
                        f"Could not parse minInclusive value as number: {min_value_str}"
                    )
        except Exception as e:
            logger.warning(f"Could not extract minInclusive info: {e}")

    # Handle maxInclusive constraints with range information
    elif "maxinclusive" in constraint_name.lower():
        try:

            max_query = f"""
            SELECT ?maxValue
            FROM <http://ex.org/ShapesGraph>
            WHERE {{
                ?shape <http://www.w3.org/ns/shacl#maxInclusive> ?maxValue .
                ?shape <http://www.w3.org/ns/shacl#path> <{property_path}> .
            }}
            LIMIT 1
            """
            results = virtuoso_service.execute_sparql_query(max_query)
            if results["results"]["bindings"]:
                max_value_str = results["results"]["bindings"][0]["maxValue"]["value"]
                constraint_info["maxValue"] = max_value_str

                # Generate a range of reasonable values below the maximum
                try:
                    # Try to parse as integer or decimal
                    if "." in max_value_str:
                        max_num = float(max_value_str)
                        allowed_values = [str(max_num - i * 0.5) for i in range(1, 6)]
                    else:
                        max_num = int(max_value_str)
                        allowed_values = [str(max_num - i) for i in range(1, 6)]

                    constraint_info["allowedValues"] = allowed_values
                    constraint_info["constraintType"] = "maxInclusive"
                except ValueError:
                    logger.warning(
                        f"Could not parse maxInclusive value as number: {max_value_str}"
                    )
        except Exception as e:
            logger.warning(f"Could not extract maxInclusive info: {e}")
    # Handle in constraints
    elif "in" in constraint_name.lower():
        try:

            # Use session-specific shapes graph
            shapes_graph_uri = (
                f"http://ex.org/Shapes/Session_{session_id}"
                if session_id
                else "http://ex.org/ShapesGraph"
            )
            logger.info(
                f"Querying sh:in constraints from shapes graph: {shapes_graph_uri}"
            )

            # Query sh:in constraints to find allowed values

            in_query = f"""
            SELECT ?allowedValue
            FROM <{shapes_graph_uri}>
            WHERE {{
                ?shape <http://www.w3.org/ns/shacl#in> ?inList .
                ?inList rdf:rest*/rdf:first ?allowedValue .
                ?shape <http://www.w3.org/ns/shacl#path> ?path .
                FILTER (STR(?path) = STR(<{property_path}>))
            }}
            """
            logger.info(f"Executing SPARQL query for sh:in constraint: {in_query}")
            results = virtuoso_service.execute_sparql_query(in_query)
            logger.info(f"SPARQL results: {results}")
            # SPARQL returns clean literal values directly, no string manipulation needed
            allowed_values = [
                binding["allowedValue"]["value"]
                for binding in results["results"]["bindings"]
            ]

            if allowed_values:
                constraint_info["allowedValues"] = allowed_values
                logger.debug(
                    f"Successfully extracted {len(allowed_values)} allowed values for sh:in constraint: {allowed_values}"
                )
            else:
                logger.warning(
                    f"No allowed values found for sh:in constraint on property {property_path}"
                )
        except Exception as e:
            logger.warning(f"Could not extract in constraint info: {e}")

    return constraint_info


def _generate_pattern_example(pattern):
    """
    Generate an example value that matches a regex pattern (simplified exrex functionality)
    """
    try:

        # Simple pattern replacements for common cases
        if pattern == r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$":
            return "example@domain.com"
        elif pattern == r"^\d{4}-\d{2}-\d{2}$":
            return "2024-01-01"
        elif pattern == r"^\d+$":
            return "123"
        elif pattern == r"^[A-Za-z]+$":
            return "Example"
        elif pattern.startswith("^") and pattern.endswith("$"):
            # Try to generate a simple example
            body = pattern[1:-1]
            if "\\d" in body and "{" in body:
                return "0" * body.count("\\d")
            elif "[A-Za-z]" in body:
                return "A" * body.count("[A-Za-z]")

        return "EXAMPLE_VALUE"
    except Exception:
        return "EXAMPLE_VALUE"


def _generate_mincount_query(focus_node, property_path, session_id):
    """Generate INSERT query for missing values with $user_provided_value placeholder (PHOENIX approach)"""
    return f"""
INSERT DATA {{
  GRAPH <http://ex.org/ValidationReport/Session_{session_id or 'UNKNOWN'}> {{
    <{focus_node}> <{property_path}> $user_provided_value .
  }}
}}"""


def _generate_maxcount_query(focus_node, property_path, value, session_id):
    """Generate DELETE query for too many values"""
    return f"""
DELETE WHERE {{
  GRAPH <http://ex.org/ValidationReport/Session_{session_id or 'UNKNOWN'}> {{
    <{focus_node}> <{property_path}> "{value}" .
  }}
}}"""


def _generate_datatype_query(focus_node, property_path, value, session_id):
    """Generate DELETE/INSERT query for datatype corrections (PHOENIX approach)"""
    corrected_value = _get_corrected_datatype(value, property_path)
    return f"""
DELETE WHERE {{
  GRAPH <http://ex.org/ValidationReport/Session_{session_id or 'UNKNOWN'}> {{
    <{focus_node}> <{property_path}> "{value}" .
  }}
}};
INSERT DATA {{
  GRAPH <http://ex.org/ValidationReport/Session_{session_id or 'UNKNOWN'}> {{
    <{focus_node}> <{property_path}> {corrected_value} .
  }}
}}"""


def _generate_pattern_query(
    focus_node, property_path, value, session_id, example_value
):
    """Generate DELETE/INSERT query for pattern violations (PHOENIX approach)"""
    return f"""
DELETE WHERE {{
  GRAPH <http://ex.org/ValidationReport/Session_{session_id or 'UNKNOWN'}> {{
    <{focus_node}> <{property_path}> "{value}" .
  }}
}};
INSERT DATA {{
  GRAPH <http://ex.org/ValidationReport/Session_{session_id or 'UNKNOWN'}> {{
    <{focus_node}> <{property_path}> $user_provided_value .
  }}
}}"""


def _generate_in_query(focus_node, property_path, value, session_id, allowed_value):
    """Generate DELETE/INSERT query for in constraint violations"""
    return f"""
DELETE WHERE {{
  GRAPH <http://ex.org/ValidationReport/Session_{session_id or 'UNKNOWN'}> {{
    <{focus_node}> <{property_path}> "{value}" .
  }}
}};
INSERT DATA {{
  GRAPH <http://ex.org/ValidationReport/Session_{session_id or 'UNKNOWN'}> {{
    <{focus_node}> <{property_path}> "{allowed_value}" .
  }}
}}"""


def _get_default_for_property(property_path):
    """Generate sensible default values based on property name (like PHOENIX)"""
    if not property_path:
        return '""'

    lower_path = property_path.lower()

    if any(keyword in lower_path for keyword in ["name", "label", "title"]):
        return '"Unknown Name"'
    elif any(keyword in lower_path for keyword in ["email", "mail"]):
        return '"unknown@example.com"'
    elif any(keyword in lower_path for keyword in ["date", "created", "modified"]):

        return f'"{datetime.now().strftime("%Y-%m-%d")}"^^xsd:date'
    elif any(keyword in lower_path for keyword in ["age", "count", "number"]):
        return '"0"^^xsd:integer'
    elif any(keyword in lower_path for keyword in ["description", "comment", "text"]):
        return '""'
    elif any(keyword in lower_path for keyword in ["url", "link", "uri"]):
        return '"http://example.org"'
    else:
        return '""'


def _get_corrected_datatype(value, property_path):
    """Fix datatype for a value based on property context (PHOENIX approach)"""
    if not value:
        return '""'

    lower_path = property_path.lower() if property_path else ""

    # Handle date conversions (like "March 1st, 2023" → "2023-03-01")
    if any(
        keyword in lower_path
        for keyword in ["date", "created", "modified", "hire", "start", "end"]
    ):
        converted_date = _convert_to_iso_date(value)
        if converted_date:
            return f'"{converted_date}"^^xsd:date'

    # Try to determine if it should be numeric
    try:
        int(value)
        if any(keyword in lower_path for keyword in ["age", "count", "number", "id"]):
            return f'"{value}"^^xsd:integer'
    except ValueError:
        pass

    try:
        float(value)
        if any(keyword in lower_path for keyword in ["price", "amount", "salary"]):
            return f'"{value}"^^xsd:decimal'
    except ValueError:
        pass

    # Check for email pattern
    if "@" in value and any(keyword in lower_path for keyword in ["email", "mail"]):
        return f'"{value}"'

    # Check for URL/URI
    if value.startswith(("http://", "https://", "ftp://")) or any(
        keyword in lower_path for keyword in ["url", "uri", "link"]
    ):
        return f'"{value}"'

    # Default to string
    return f'"{value}"'


def _convert_to_iso_date(date_str):
    """Convert various date formats to ISO format (YYYY-MM-DD)"""
    import re
    from datetime import datetime

    # Handle formats like "March 1st, 2023" or "Mar 1, 2023"
    month_patterns = {
        "january": "01",
        "jan": "01",
        "february": "02",
        "feb": "02",
        "march": "03",
        "mar": "03",
        "april": "04",
        "apr": "04",
        "may": "05",
        "june": "06",
        "jun": "06",
        "july": "07",
        "jul": "07",
        "august": "08",
        "aug": "08",
        "september": "09",
        "sep": "09",
        "sept": "09",
        "october": "10",
        "oct": "10",
        "november": "11",
        "nov": "11",
        "december": "12",
        "dec": "12",
    }

    # Pattern 1: "March 1st, 2023" or "Mar 1st, 2023"
    pattern1 = r"(\w+)\s+(\d+)(?:st|nd|rd|th)?,?\s*(\d{4})"
    match1 = re.match(pattern1, date_str, re.IGNORECASE)
    if match1:
        month_name, day, year = match1.groups()
        month = month_patterns.get(month_name.lower(), month_name.lower())
        if month and month.isdigit():
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    # Pattern 2: "2023-03-01" or "2023/03/01"
    pattern2 = r"(\d{4})[-/](\d{2})[-/](\d{2})"
    match2 = re.match(pattern2, date_str)
    if match2:
        return f"{match2.group(1)}-{match2.group(2)}-{match2.group(3)}"

    # Pattern 3: "01/03/2023" (DD/MM/YYYY)
    pattern3 = r"(\d{2})[-/](\d{2})[-/](\d{4})"
    match3 = re.match(pattern3, date_str)
    if match3:
        return f"{match3.group(3)}-{match3.group(2)}-{match3.group(1)}"

    # Pattern 4: "03/01/2023" (MM/DD/YYYY)
    pattern4 = r"(\d{2})[-/](\d{2})[-/](\d{4})"
    match4 = re.match(pattern4, date_str)
    if match4:
        # This will match the same as pattern3, we need to differentiate
        # Assume MM/DD/YYYY if month is 12 or less
        month = int(match4.group(1))
        if month <= 12:
            return f"{match4.group(3)}-{match4.group(1).zfill(2)}-{match4.group(2).zfill(2)}"

    return None


def _get_violation_context(violation, session_id):
    """
    Get PHOENIX-style context information for violations, including example values
    """
    context = {}
    constraint_id = violation.get("constraint_id", "")
    constraint_name = (
        constraint_id.split("#")[-1]
        if "#" in constraint_id
        else constraint_id.split("/")[-1]
    )

    # Pattern constraint context with example values
    if "pattern" in constraint_name.lower():
        try:

            pattern_query = f"""
            SELECT ?pattern ?message
            FROM <http://ex.org/ShapesGraph>
            WHERE {{
                ?shape <http://www.w3.org/ns/shacl#pattern> ?pattern .
                ?shape <http://www.w3.org/ns/shacl#path> <{violation.get('property_path', '')}> .
                OPTIONAL {{ ?shape <http://www.w3.org/ns/shacl#message> ?message . }}
            }}
            LIMIT 1
            """
            results = virtuoso_service.execute_sparql_query(pattern_query)
            if results["results"]["bindings"]:
                binding = results["results"]["bindings"][0]
                pattern = binding["pattern"]["value"]
                context["pattern"] = pattern

                # Generate example value using exrex (just like PHOENIX)
                try:

                    context["exampleValue"] = exrex.getone(pattern)
                except Exception as e:
                    logger.warning(
                        f"Could not generate example for pattern '{pattern}': {e}"
                    )

                if "message" in binding:
                    context["message"] = binding["message"]["value"]
        except Exception as e:
            logger.warning(f"Could not extract pattern info: {e}")

    # MaxCount constraint context
    elif "maxcount" in constraint_name.lower():
        try:

            maxcount_query = f"""
            SELECT ?maxCount
            FROM <http://ex.org/ShapesGraph>
            WHERE {{
                ?shape <http://www.w3.org/ns/shacl#maxCount> ?maxCount .
                ?shape <http://www.w3.org/ns/shacl#path> <{violation.get('property_path', '')}> .
            }}
            LIMIT 1
            """
            results = virtuoso_service.execute_sparql_query(maxcount_query)
            if results["results"]["bindings"]:
                max_count = int(results["results"]["bindings"][0]["maxCount"]["value"])
                context["maxCount"] = max_count

                # Get actual values from data graph
                actual_values_query = f"""
                SELECT ?value
                FROM <http://ex.org/DataGraph>
                WHERE {{
                    <{violation.get('focus_node', '')}> <{violation.get('property_path', '')}> ?value .
                }}
                """
                actual_results = virtuoso_service.execute_sparql_query(
                    actual_values_query
                )
                actual_values = [
                    binding["value"]["value"]
                    for binding in actual_results["results"]["bindings"]
                ]
                context["actualValues"] = actual_values
        except Exception as e:
            logger.warning(f"Could not extract maxCount info: {e}")

    # InConstraint context
    elif "in" in constraint_name.lower():
        try:

            # Use session-specific shapes graph
            shapes_graph_uri = (
                f"http://ex.org/Shapes/Session_{session_id}"
                if session_id
                else "http://ex.org/ShapesGraph"
            )
            logger.debug(
                f"Querying sh:in constraints from shapes graph: {shapes_graph_uri}"
            )

            in_query = f"""
            SELECT ?allowedValue
            FROM <{shapes_graph_uri}>
            WHERE {{
                ?shape <http://www.w3.org/ns/shacl#in> ?inList .
                ?inList rdf:rest*/rdf:first ?allowedValue .
                ?shape <http://www.w3.org/ns/shacl#path> <{violation.get('property_path', '')}> .
            }}
            """
            results = virtuoso_service.execute_sparql_query(in_query)
            # SPARQL returns clean literal values directly, no string manipulation needed
            allowed_values = [
                binding["allowedValue"]["value"]
                for binding in results["results"]["bindings"]
            ]
            if allowed_values:
                context["allowedValues"] = allowed_values
        except Exception as e:
            logger.warning(f"Could not extract in constraint info: {e}")

    return context


def _calculate_confidence(cached_explanation, violation_obj):
    """
    Calculate confidence level for an explanation based on VKG data and violation characteristics
    """
    try:
        confidence_score = 0.5  # Base confidence

        # Factor 1: Quality of natural language explanation
        if cached_explanation.natural_language_explanation:
            explanation_length = len(
                cached_explanation.natural_language_explanation.split()
            )
            if explanation_length > 10:
                confidence_score += 0.1
            if explanation_length > 20:
                confidence_score += 0.1

        # Factor 2: Presence of correction suggestions
        if (
            cached_explanation.correction_suggestions
            and len(cached_explanation.correction_suggestions) > 0
        ):
            confidence_score += 0.1
            if len(cached_explanation.correction_suggestions) > 1:
                confidence_score += 0.1

        # Factor 3: Presence of repair query
        if cached_explanation.proposed_repair_query:
            confidence_score += 0.1

        # Factor 4: Constraint complexity (well-known constraints get higher confidence)
        constraint_name = (
            violation_obj.constraint_id.split("#")[-1]
            if "#" in violation_obj.constraint_id
            else violation_obj.constraint_id.split("/")[-1]
        )
        common_constraints = [
            "mincount",
            "maxcount",
            "datatype",
            "class",
            "pattern",
            "in",
            "maxinclusive",
            "mininclusive",
        ]
        if any(common in constraint_name.lower() for common in common_constraints):
            confidence_score += 0.1

        # Convert to descriptive level
        if confidence_score >= 0.9:
            return "Very High (comprehensive VKG match)"
        elif confidence_score >= 0.7:
            return "High (strong VKG pattern match)"
        elif confidence_score >= 0.5:
            return "Medium (partial VKG match)"
        else:
            return "Low (limited VKG data)"

    except Exception as e:
        logger.warning(f"Error calculating confidence: {e}")
        return "Medium (default confidence)"
