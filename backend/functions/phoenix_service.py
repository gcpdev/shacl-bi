import os
import logging
import threading
import time
from typing import List, Dict, Any, Optional
from rdflib import Graph, RDF
from rdflib.namespace import Namespace

# SHACL namespace
SHACL = Namespace("http://www.w3.org/ns/shacl#")
from functions.xpshacl_engine.extended_shacl_validator import ExtendedShaclValidator
from functions.xpshacl_engine.justification_tree_builder import JustificationTreeBuilder
from functions.xpshacl_engine.context_retriever import ContextRetriever
from functions.xpshacl_engine.repair_engine import SuggestionRepairGenerator
from functions.xpshacl_engine.knowledge_graph import ViolationKnowledgeGraph
from functions.xpshacl_engine.violation_signature_factory import (
    create_violation_signature,
)
from .xpshacl_engine.xpshacl_architecture import ConstraintViolation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global cache for background explanations
explanation_cache = {}


def load_vkg_from_virtuoso():
    """
    Load ViolationKnowledgeGraph from Virtuoso database using SPARQL queries.
    This replaces the file-based loading with Virtuoso database access.
    """
    try:
        from .virtuoso_service import execute_sparql_query
        import config

        # Create empty VKG that will be populated from Virtuoso
        vkg = ViolationKnowledgeGraph()

        # Define the VKG graph URI from config
        vkg_graph_uri = getattr(
            config, "VIOLATION_KG_GRAPH", "http://ex.org/ViolationKnowledgeGraph"
        )

        logger.info(f"Loading VKG from Virtuoso database at graph: {vkg_graph_uri}")

        # First, try to use a CONSTRUCT query with SPARQLWrapper directly
        try:
            from SPARQLWrapper import SPARQLWrapper, DIGEST, TURTLE

            sparql = SPARQLWrapper(
                getattr(config, "ENDPOINT_URL", "http://localhost:8890/sparql")
            )
            if getattr(config, "AUTH_REQUIRED", False):
                sparql.setCredentials(
                    getattr(config, "USERNAME", ""), getattr(config, "PASSWORD", "")
                )
            sparql.setHTTPAuth(DIGEST)

            # Query to load all triples from the VKG graph
            query = f"""
            CONSTRUCT {{
                ?s ?p ?o .
            }}
            FROM <{vkg_graph_uri}>
            WHERE {{
                ?s ?p ?o .
            }}
            """

            sparql.setQuery(query)
            sparql.setReturnFormat(TURTLE)
            results = sparql.query().convert()

            if results:
                vkg.graph.parse(data=results, format="turtle")
                logger.info(
                    f"Successfully loaded VKG with {len(vkg.graph)} triples from Virtuoso"
                )
                return vkg
            else:
                logger.warning(f"No data found in VKG graph {vkg_graph_uri}")

        except Exception as construct_error:
            logger.warning(f"CONSTRUCT query failed: {construct_error}")

        # Fallback: Try to load ontology from local file
        ontology_path = getattr(
            config, "VIOLATION_KG_ONTOLOGY_PATH", "backend/data/violation_kg.ttl"
        )
        if os.path.exists(ontology_path):
            vkg.graph.parse(ontology_path, format="turtle")
            logger.info(f"Loaded ontology from local file: {ontology_path}")
            logger.info(f"VKG initialized with {len(vkg.graph)} triples from ontology")
            return vkg
        else:
            logger.warning(f"Ontology file not found: {ontology_path}")

        # If we reach here, create a minimal VKG with just the basic structure
        logger.info("Creating minimal VKG with basic structure")
        return vkg

    except Exception as e:
        logger.error(f"Error loading VKG from Virtuoso: {str(e)}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


def clean_llm_text(text):
    """
    Clean text from LLM responses to remove weird formatting
    """
    if not text:
        return text

    import re

    # Replace literal \n between characters
    cleaned = re.sub(r"\\n\s*", " ", text)

    # Remove unusual unicode characters that might cause issues
    cleaned = re.sub(r"[\u200b-\u200f\u2028-\u202f\ufeff]", "", cleaned)

    # Fix obvious case of single spaces between single letters (like "A n d r e w")
    # Pattern: single space between single character words
    cleaned = re.sub(r"(?<=\b\w)\s(?=\w\b)(?=\s*\w\b)", "", cleaned)

    # Normalize multiple spaces to single spaces, but be careful about word boundaries
    cleaned = re.sub(r"  +", " ", cleaned)

    # Remove leading/trailing whitespace
    return cleaned.strip()


def get_cached_explanation(violation: ConstraintViolation):
    """Get cached explanation for a violation."""
    try:
        signature = create_violation_signature(violation)
        cached_explanation = explanation_cache.get(str(signature))
        return cached_explanation
    except Exception as e:
        logger.error(f"Error getting cached explanation: {str(e)}")
        return None


def generate_enhanced_explanation(
    violation: ConstraintViolation,
) -> Optional[Dict[str, Any]]:
    """Generate enhanced explanation for a violation."""
    try:
        logger.info(f"🔍 [PHOENIX] generate_enhanced_explanation called with violation: {violation}")
        vkg = load_vkg_from_virtuoso()
        if not vkg:
            logger.warning("VKG not available for enhanced explanation generation")
            return None

        signature = create_violation_signature(violation)
        logger.info(f"🔍 [PHOENIX] Generated signature: {signature}")
        logger.info(f"🔍 [PHOENIX] Signature details - constraint_id: {signature.constraint_id}, property_path: {signature.property_path}, violation_type: {signature.violation_type}, params: {signature.constraint_params}")
        cached_explanation = vkg.get_explanation(signature)

        if cached_explanation:
            return {
                "natural_language_explanation": clean_llm_text(
                    cached_explanation.natural_language_explanation
                ),
                "correction_suggestions": [
                    clean_llm_text(s)
                    for s in (cached_explanation.correction_suggestions or [])
                ],
                "proposed_repair_query": cached_explanation.proposed_repair_query,
                "confidence": getattr(cached_explanation, "confidence", 0.8),
            }
        else:
            # Generate new explanation
            tree_builder = JustificationTreeBuilder(Graph(), Graph())
            justification_tree = tree_builder.build_justification_tree(violation)
            context_retriever = ContextRetriever(Graph(), Graph())
            context = context_retriever.retrieve_context(violation)

            srg = SuggestionRepairGenerator(vkg=vkg)
            repair_object = srg.generate_repair_object(
                violation, justification_tree, context
            )

            if repair_object:
                vkg.add_violation(signature, srg.last_explanation_output)
                return {
                    "natural_language_explanation": clean_llm_text(
                        repair_object.get("explanation_natural_language", "")
                    ),
                    "correction_suggestions": [
                        clean_llm_text(
                            repair_object.get("suggestion_natural_language", "")
                        )
                    ],
                    "proposed_repair_query": repair_object.get(
                        "proposed_repair", {}
                    ).get("query", ""),
                    "confidence": 0.7,
                }

        return None

    except Exception as e:
        logger.error(f"Error generating enhanced explanation: {str(e)}")
        return None


def cache_explanation(violation: ConstraintViolation, explanation: Dict[str, Any]):
    """Cache an explanation for a violation."""
    try:
        signature = create_violation_signature(violation)
        explanation_cache[str(signature)] = explanation
        logger.info(f"Cached explanation for signature: {signature}")
    except Exception as e:
        logger.error(f"Error caching explanation: {str(e)}")


def clear_explanation_cache():
    """Clear the explanation cache."""
    global explanation_cache
    explanation_cache = {}
    logger.info("Explanation cache cleared")


def batch_generate_explanations(
    violations: List[ConstraintViolation],
) -> List[Optional[Dict[str, Any]]]:
    """Generate explanations for multiple violations."""
    explanations = []
    for violation in violations:
        explanation = generate_enhanced_explanation(violation)
        explanations.append(explanation)
    return explanations


def get_constraint_statistics() -> Dict[str, Any]:
    """Get constraint violation statistics."""
    try:
        vkg = load_vkg_from_virtuoso()
        if not vkg:
            return {"total_violations": 0, "constraint_types": {}}

        return vkg.get_statistics()
    except Exception as e:
        logger.error(f"Error getting constraint statistics: {str(e)}")
        return {"total_violations": 0, "constraint_types": {}}


def get_explanation_by_type(constraint_type: str) -> List[Dict[str, Any]]:
    """Get explanations by constraint type."""
    try:
        vkg = load_vkg_from_virtuoso()
        if not vkg:
            return []

        explanations = vkg.get_explanations_by_type(constraint_type)
        return [
            {
                "constraint_type": exp.constraint_type,
                "explanation": exp.natural_language_explanation,
                "suggestions": exp.correction_suggestions,
            }
            for exp in explanations
        ]
    except Exception as e:
        logger.error(f"Error getting explanations by type: {str(e)}")
        return []


def violation_to_dict(violation: ConstraintViolation) -> Dict[str, Any]:
    """Convert violation object to dictionary."""
    return violation.to_dict()


def dict_to_violation(violation_dict: Dict[str, Any]) -> ConstraintViolation:
    """Convert dictionary to violation object."""
    return ConstraintViolation.from_dict(violation_dict)


def get_explanation_confidence_score(violation: ConstraintViolation) -> float:
    """Get confidence score for explanation."""
    try:
        vkg = load_vkg_from_virtuoso()
        if not vkg:
            return 0.5  # Default confidence

        signature = create_violation_signature(violation)
        return vkg.get_confidence_score(signature)
    except Exception as e:
        logger.error(f"Error getting confidence score: {str(e)}")
        return 0.5


def persist_vkg_to_virtuoso(vkg) -> bool:
    """
    Persist the ViolationKnowledgeGraph to Virtuoso database.
    This saves the VKG with all its explanations back to the Virtuoso triple store.
    """
    try:
        from . import virtuoso_service
        import config

        # Get the VKG graph URI from config
        vkg_graph_uri = getattr(config, "VIOLATION_KG_GRAPH", "http://ex.org/ViolationKnowledgeGraph")

        logger.info(f"Persisting VKG to Virtuoso graph: {vkg_graph_uri}")

        # Clear the existing VKG graph first
        clear_query = f"CLEAR GRAPH <{vkg_graph_uri}>"
        virtuoso_service.execute_sparql_update(clear_query)

        # Get all triples from the VKG graph, filtering out prefix declarations
        triples = []
        for s, p, o in vkg.graph:
            # Convert to SPARQL format first
            s_str = str(s)
            p_str = str(p)
            o_str = str(o)

            # Skip prefix declarations - they contain @prefix or are meta-statements about prefixes
            if ("@prefix" in s_str or "@prefix" in p_str or "@prefix" in o_str or
                "http://www.w3.org/2000/01/rdf-schema#subClassOf" in p_str or
                "http://www.w3.org/2000/01/rdf-schema#subPropertyOf" in p_str or
                "http://www.w3.org/2002/07/owl#equivalentClass" in p_str or
                "http://www.w3.org/2002/07/owl#equivalentProperty" in p_str):
                logger.debug(f"Skipping prefix/ontology triple: {s_str} {p_str} {o_str}")
                continue

            # Skip schema definition triples that don't have instance-like subjects
            if (p_str in ["http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
                          "http://www.w3.org/2000/01/rdf-schema#label",
                          "http://www.w3.org/2000/01/rdf-schema#comment",
                          "http://www.w3.org/2000/01/rdf-schema#domain",
                          "http://www.w3.org/2000/01/rdf-schema#range"] and
                not any(instance_marker in s_str for instance_marker in ["sig_", "explanation_", "feedback_", "http://xpshacl.org/sig_"])):
                logger.debug(f"Skipping schema triple: {s_str} {p_str} {o_str}")
                continue

            # Convert to proper SPARQL format
            s_formatted = f"<{s}>" if isinstance(s, str) and not s.startswith('"') else s.n3()
            p_formatted = f"<{p}>" if isinstance(p, str) and not p.startswith('"') else p.n3()
            o_formatted = f"<{o}>" if isinstance(o, str) and not o.startswith('"') and not o.startswith("<") else o.n3()
            if isinstance(o, str) and not o.startswith('"') and not o.startswith("<") and ":" not in o:
                o_formatted = f'"{o}"'

            triples.append(f"{s_formatted} {p_formatted} {o_formatted} .")

        if not triples:
            logger.warning("VKG graph is empty, nothing to persist")
            return True

        # Create INSERT query with individual triples
        insert_query = f"""
        INSERT DATA {{
            GRAPH <{vkg_graph_uri}> {{
                {chr(10).join(triples)}
            }}
        }}
        """

        virtuoso_service.execute_sparql_update(insert_query)

        logger.info(f"Successfully persisted VKG with {len(triples)} triples to Virtuoso")
        return True

    except Exception as e:
        logger.error(f"Error persisting VKG to Virtuoso: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


def filter_explanations(
    explanations: List[Dict[str, Any]],
    min_confidence: float = 0.0,
    constraint_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filter explanations by confidence and/or constraint type."""
    filtered = explanations

    if min_confidence > 0.0:
        filtered = [
            exp for exp in filtered if exp.get("confidence", 0) >= min_confidence
        ]

    if constraint_type:
        filtered = [
            exp for exp in filtered if exp.get("constraint_type") == constraint_type
        ]

    return filtered


def cache_explanation_with_ttl(
    violation: ConstraintViolation, explanation: Dict[str, Any], ttl: int = 3600
):
    """Cache explanation with time-to-live."""
    try:
        signature = create_violation_signature(violation)
        explanation_data = {"explanation": explanation, "expires_at": time.time() + ttl}
        explanation_cache[str(signature)] = explanation_data
        logger.info(f"Cached explanation with TTL {ttl}s for signature: {signature}")
    except Exception as e:
        logger.error(f"Error caching explanation with TTL: {str(e)}")


def clean_expired_cache():
    """Remove expired entries from cache."""
    current_time = time.time()
    expired_keys = []

    for key, value in explanation_cache.items():
        if isinstance(value, dict) and "expires_at" in value:
            if value["expires_at"] <= current_time:
                expired_keys.append(key)

    for key in expired_keys:
        del explanation_cache[key]

    if expired_keys:
        logger.info(f"Cleaned {len(expired_keys)} expired cache entries")


def get_cache_hit_rate() -> float:
    """Calculate cache hit rate."""
    # This is a simplified implementation
    # In practice, you'd track hits and misses separately
    total_entries = len(explanation_cache)
    if total_entries == 0:
        return 0.0
    return min(1.0, total_entries / 100.0)  # Simple heuristic


def validate_with_phoenix(data_file_path, shapes_file_path):
    """Main validation function with Phoenix explanations."""
    try:
        logger.info(
            f"Starting validation with data file: {data_file_path}, shapes file: {shapes_file_path}"
        )

        # Parse the input files
        data_graph = Graph().parse(data_file_path, format="turtle")
        shapes_graph = Graph().parse(shapes_file_path, format="turtle")

        logger.info("Files parsed successfully")

        validator = ExtendedShaclValidator(shapes_graph)
        violations = validator.validate(data_graph)
        conforms = not violations

        logger.info(
            f"Validation completed. Conforms: {conforms}, Violations count: {len(violations) if violations else 0}"
        )

        # Generate unique session ID for this validation
        session_id = f"validation_{int(time.time())}_{hash(str(violations))}"

        # Return basic explanations immediately for fast response
        explanations = []
        if violations:
            logger.info(
                f"Starting background processing for {len(violations)} violations"
            )

            # Generate basic explanations for immediate response
            violation_explanations = []
            for i, violation in enumerate(violations):
                # Generate basic explanations for immediate response (no LLM calls here!)
                focus_node = getattr(violation, "focus_node", "Unknown resource")
                constraint_id = getattr(
                    violation, "constraint_id", "Unknown constraint"
                )
                message = getattr(violation, "message", "Constraint violation detected")
                property_path = getattr(violation, "property_path", "Unknown property")

                basic_explanation = {
                    "explanation_natural_language": f"The resource '{focus_node}' violates the constraint '{constraint_id}' on property '{property_path}'. {message}",
                    "suggestion_natural_language": f"To fix this violation, please review the data for '{focus_node}' and ensure the value of '{property_path}' complies with the constraint requirements.",
                    "proposed_repair": {"query": ""},
                    "session_id": session_id,
                    "is_basic": True,  # Mark as basic explanation
                }

                # Use the basic explanation for immediate response
                violation_explanations.append(basic_explanation)

            explanations = violation_explanations

        report_graph_json = (
            validator.results_graph.serialize(format="json-ld")
            if validator.results_graph
            else "[]"
        )
        report_text = "Validation report"

        # Process violations for frontend
        violations_data = []
        if violations:
            for i, v in enumerate(violations):
                violation_data = {
                    "id": i,
                    "focusNode": getattr(v, "focus_node", "Unknown"),
                    "resultPath": getattr(v, "property_path", "Unknown"),
                    "value": getattr(v, "value", "Unknown"),
                    "message": getattr(v, "message", "Constraint violation"),
                    "propertyShape": getattr(v, "shape_id", "Unknown"),
                    "severity": getattr(v, "severity", "Violation"),
                    "nodeShape": getattr(v, "shape_id", "Unknown"),
                    "constraintComponent": getattr(v, "constraint_id", "Unknown"),
                    "targetClass": "",
                    "targetNode": "",
                    "targetSubjectsOf": "",
                    "targetObjectsOf": "",
                    "shapes": {
                        "shape": getattr(v, "shape_id", "Unknown"),
                        "type": "sh:NodeShape",
                        "targetClass": "",
                        "properties": (
                            [
                                {
                                    "predicate": "http://www.w3.org/ns/shacl#path",
                                    "object": getattr(v, "property_path", "Unknown"),
                                },
                                {
                                    "predicate": "http://www.w3.org/ns/shacl#severity",
                                    "object": getattr(v, "severity", "Violation"),
                                },
                            ]
                            if getattr(v, "property_path", None)
                            else []
                        ),
                    },
                    "explanation": explanations[i] if i < len(explanations) else None,
                    "session_id": session_id,
                }
                violations_data.append(violation_data)

        constraints_map = {}
        if violations:
            for v in violations:
                constraint = getattr(v, "constraint_id", "Unknown")
                if constraint is None:
                    logger.warning(
                        f"Warning: constraint_id not found in violation object. Violation: {v}"
                    )
                    constraint = "Unknown"
                constraint = str(constraint)
                if constraint not in constraints_map:
                    constraints_map[constraint] = {"name": constraint, "violations": 0}
                constraints_map[constraint]["violations"] += 1

        constraints_data = list(constraints_map.values())

        logger.info(
            f"Returning validation results: {len(violations_data) if violations_data else 0} violations, {len(constraints_data) if constraints_data else 0} constraints"
        )
        return (
            conforms,
            report_graph_json,
            report_text,
            explanations,
            violations_data,
            constraints_data,
        )

    except Exception as e:
        import traceback

        logger.error(f"Error during validation: {str(e)}")
        logger.error(f"Validation error traceback: {traceback.format_exc()}")
        # Return a basic error response that won't break the frontend
        return False, "[]", f"Validation error: {str(e)}", [], [], []
