import os
import logging
import threading
import time
from rdflib import Graph, RDF
from rdflib.namespace import SHACL
from functions.xpshacl_engine.extended_shacl_validator import ExtendedShaclValidator
from functions.xpshacl_engine.justification_tree_builder import JustificationTreeBuilder
from functions.xpshacl_engine.context_retriever import ContextRetriever
from functions.xpshacl_engine.repair_engine import SuggestionRepairGenerator
from functions.xpshacl_engine.knowledge_graph import ViolationKnowledgeGraph
from functions.xpshacl_engine.violation_signature_factory import create_violation_signature

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
        from .xpshacl_engine.knowledge_graph import ViolationKnowledgeGraph
        import config

        # Create empty VKG that will be populated from Virtuoso
        vkg = ViolationKnowledgeGraph()

        # Define the VKG graph URI from config
        vkg_graph_uri = config.VIOLATION_KG_GRAPH

        logger.info(f"Loading VKG from Virtuoso database at graph: {vkg_graph_uri}")

        # First, try to use a CONSTRUCT query with SPARQLWrapper directly
        try:
            from SPARQLWrapper import SPARQLWrapper, DIGEST, TURTLE
            sparql = SPARQLWrapper(config.ENDPOINT_URL)
            if config.AUTH_REQUIRED:
                sparql.setCredentials(config.USERNAME, config.PASSWORD)
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
                vkg.graph.parse(data=results, format='turtle')
                logger.info(f"Successfully loaded VKG with {len(vkg.graph)} triples from Virtuoso")
                return vkg
            else:
                logger.warning(f"No data found in VKG graph {vkg_graph_uri}")

        except Exception as construct_error:
            logger.warning(f"CONSTRUCT query failed: {construct_error}")

        # Fallback: Try to load ontology from local file
        ontology_path = config.VIOLATION_KG_ONTOLOGY_PATH
        if os.path.exists(ontology_path):
            vkg.graph.parse(ontology_path, format='turtle')
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
    # Replace literal \n between characters and normalize whitespace
    cleaned = re.sub(r'\\n\s*', '', text)
    # Remove extra spaces between characters (like "A n d r e w")
    cleaned = re.sub(r'(?<=\w)\s+(?=\w)', '', cleaned)
    # Normalize all whitespace to single spaces
    cleaned = ' '.join(cleaned.split())
    return cleaned.strip()

def process_explanations_background(violations, session_id, data_file_path, shapes_file_path):
    """
    Background task to process LLM explanations for violations.
    This function will also clean up the temporary files after processing.
    """
    logger.info(f"Background thread started for session {session_id} with {len(violations)} violations")
    try:
        logger.info(f"Starting background explanation processing for session {session_id}")

        # NOTE: Timeout handling removed as signal module only works in main thread
        # Background processing will run without artificial timeout limits
        # The individual LLM calls have their own timeout configurations

        # Load VKG from Virtuoso database instead of local files
        vkg = load_vkg_from_virtuoso()
        if vkg:
            srg = SuggestionRepairGenerator(vkg=vkg)
            logger.info(f"[{session_id}] Successfully loaded VKG from Virtuoso")
        else:
            vkg = None
            srg = None
            logger.info(f"[{session_id}] Failed to load VKG from Virtuoso, will use basic explanations")

        explanations = []
        if violations:
            logger.info(f"[{session_id}] Starting to loop through {len(violations)} violations.")
            for i, v in enumerate(violations):
                try:
                    logger.info(f"[{session_id}] Processing violation #{i+1}")
                    if vkg:
                        signature = create_violation_signature(v)
                        logger.info(f"[{session_id}] Created signature: {signature}")
                        cached_explanation = vkg.get_explanation(signature)

                        if cached_explanation:
                            logger.info(f"[{session_id}] Found cached explanation for signature.")
                            repair_object = {
                                "explanation_natural_language": clean_llm_text(cached_explanation.natural_language_explanation),
                                "suggestion_natural_language": clean_llm_text("\n".join(cached_explanation.correction_suggestions or [])),
                                "proposed_repair": {"query": cached_explanation.proposed_repair_query}
                            }
                            explanations.append(repair_object)
                            logger.info(f"[{session_id}] Appended cached explanation. Total explanations: {len(explanations)}")
                        else:
                            logger.info(f"[{session_id}] No cached explanation found. Generating new one.")
                            tree_builder = JustificationTreeBuilder(Graph(), Graph())
                            justification_tree = tree_builder.build_justification_tree(v)
                            context_retriever = ContextRetriever(Graph(), Graph())
                            context = context_retriever.retrieve_context(v)

                            repair_object = srg.generate_repair_object(v, justification_tree, context)
                            logger.info(f"[{session_id}] Generated repair object: {'Yes' if repair_object else 'No'}")

                            if repair_object:
                                vkg.add_violation(signature, srg.last_explanation_output)
                                explanations.append(repair_object)
                                logger.info(f"[{session_id}] Appended new explanation. Total explanations: {len(explanations)}")
                    else:
                        logger.info(f"[{session_id}] VKG not available. Generating basic explanation.")
                        # Basic explanation without AI features
                        focus_node = getattr(v, 'focus_node', 'Unknown resource')
                        constraint_id = getattr(v, 'constraint_id', 'Unknown constraint')
                        message = getattr(v, 'message', 'Constraint violation detected')
                        property_path = getattr(v, 'property_path', 'Unknown property')

                        repair_object = {
                            "explanation_natural_language": f"The resource '{focus_node}' violates the constraint '{constraint_id}' on property '{property_path}'. {message}",
                            "suggestion_natural_language": f"To fix this violation, please review the data for '{focus_node}' and ensure the value of '{property_path}' complies with the constraint requirements. You may need to update the value, add missing properties, or correct the data format.",
                            "proposed_repair": {"query": ""}
                        }

                        explanations.append(repair_object)
                        logger.info(f"[{session_id}] Appended basic explanation. Total explanations: {len(explanations)}")

                except Exception as e:
                    logger.error(f"Error processing explanation for violation {i}: {str(e)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    explanations.append({
                        "explanation_natural_language": f"Error generating explanation: {str(e)}",
                        "suggestion_natural_language": "Please review this violation manually",
                        "proposed_repair": {"query": ""}
                    })

        # Store in cache
        explanation_cache[session_id] = explanations
        logger.info(f"Background explanation processing completed for session {session_id}. Generated {len(explanations)} explanations.")

    except Exception as e:
        import traceback
        logger.error(f"Error in background explanation processing: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        explanation_cache[session_id] = []
    finally:
        # --- FINAL CLEANUP ---
        # Always remove the temporary files when the background task is done
        logger.info(f"[{session_id}] Cleaning up temporary files: {data_file_path}, {shapes_file_path}")
        try:
            os.remove(data_file_path)
            os.remove(shapes_file_path)
            logger.info(f"[{session_id}] Temporary files cleaned up successfully.")
        except OSError as e:
            logger.error(f"[{session_id}] Error cleaning up temporary files: {e}")

def validate_with_phoenix(data_file_path, shapes_file_path):
    try:
        logger.info(f"Starting validation with data file: {data_file_path}, shapes file: {shapes_file_path}")

        # Parse the input files
        data_graph = Graph().parse(data_file_path, format='turtle')
        shapes_graph = Graph().parse(shapes_file_path, format='turtle')

        logger.info("Files parsed successfully")

        validator = ExtendedShaclValidator(shapes_graph)
        violations = validator.validate(data_graph)
        conforms = not violations

        logger.info(f"Validation completed. Conforms: {conforms}, Violations count: {len(violations) if violations else 0}")

        # Generate unique session ID for this validation
        session_id = f"validation_{int(time.time())}_{hash(str(violations))}"

        # Return basic explanations immediately for fast response
        explanations = []
        if violations:
            # Copy files to new paths for background processing so they don't get deleted before validation completes
            import shutil
            temp_copy_dir = 'temp_copy'
            os.makedirs(temp_copy_dir, exist_ok=True)

            data_copy_path = os.path.join(temp_copy_dir, f"data_copy_{session_id}.ttl")
            shapes_copy_path = os.path.join(temp_copy_dir, f"shapes_copy_{session_id}.ttl")

            shutil.copy2(data_file_path, data_copy_path)
            shutil.copy2(shapes_file_path, shapes_copy_path)

            logger.info(f"Starting background processing for {len(violations)} violations")
            # Start background processing with improved error handling
            try:
                thread = threading.Thread(
                    target=process_explanations_background,
                    args=(violations, session_id, data_copy_path, shapes_copy_path),
                    daemon=True
                )
                thread.start()
                logger.info(f"Started background explanation processing for session {session_id}")
                logger.info(f"Background thread started successfully: {thread.is_alive()}")
            except Exception as e:
                logger.error(f"Failed to start background thread: {str(e)}")
                import traceback
                logger.error(f"Thread start error traceback: {traceback.format_exc()}")
                # Don't fail the main validation if background processing fails

            
            # Generate basic explanations for immediate response
            violation_explanations = []
            for i, violation in enumerate(violations):
                # Generate basic explanations for immediate response (no LLM calls here!)
                focus_node = getattr(violation, 'focus_node', 'Unknown resource')
                constraint_id = getattr(violation, 'constraint_id', 'Unknown constraint')
                message = getattr(violation, 'message', 'Constraint violation detected')
                property_path = getattr(violation, 'property_path', 'Unknown property')

                basic_explanation = {
                    "explanation_natural_language": f"The resource '{focus_node}' violates the constraint '{constraint_id}' on property '{property_path}'. {message}",
                    "suggestion_natural_language": f"To fix this violation, please review the data for '{focus_node}' and ensure the value of '{property_path}' complies with the constraint requirements.",
                    "proposed_repair": {"query": ""},
                    "session_id": session_id,
                    "is_basic": True  # Mark as basic explanation
                }

                # Use the basic explanation for immediate response
                violation_explanations.append(basic_explanation)

            explanations = violation_explanations

        report_graph_json = validator.results_graph.serialize(format='json-ld') if validator.results_graph else "[]"
        report_text = "Validation report" # Or build a more detailed one if needed

        # Process violations for frontend
        violations_data = []
        if violations:
            for i, v in enumerate(violations):
                violation_data = {
                    'id': i,
                    'focusNode': getattr(v, 'focus_node', 'Unknown'),
                    'resultPath': getattr(v, 'property_path', 'Unknown'),
                    'value': getattr(v, 'value', 'Unknown'),
                    'message': getattr(v, 'message', 'Constraint violation'),
                    'propertyShape': getattr(v, 'shape_id', 'Unknown'),
                    'severity': getattr(v, 'severity', 'Violation'),
                    'nodeShape': getattr(v, 'shape_id', 'Unknown'),
                    'constraintComponent': getattr(v, 'constraint_id', 'Unknown'),
                    'targetClass': '',
                    'targetNode': '',
                    'targetSubjectsOf': '',
                    'targetObjectsOf': '',
                    'shapes': {
                        'shape': getattr(v, 'shape_id', 'Unknown'),
                        'type': 'sh:NodeShape',
                        'targetClass': '',
                        'properties': [
                            {
                                'predicate': 'http://www.w3.org/ns/shacl#path',
                                'object': getattr(v, 'property_path', 'Unknown')
                            },
                            {
                                'predicate': 'http://www.w3.org/ns/shacl#severity',
                                'object': getattr(v, 'severity', 'Violation')
                            }
                        ] if getattr(v, 'property_path', None) else []
                    },
                    'explanation': explanations[i] if i < len(explanations) else None,
                    'session_id': session_id  # Include session_id for fetching enhanced explanations
                }
                violations_data.append(violation_data)

        constraints_map = {}
        if violations:
            for v in violations:
                constraint = getattr(v, 'constraint_id', 'Unknown')
                if constraint is None:
                    logger.warning(f"Warning: constraint_id not found in violation object. Violation: {v}")
                    constraint = "Unknown"
                constraint = str(constraint)
                if constraint not in constraints_map:
                    constraints_map[constraint] = {
                        'name': constraint,
                        'violations': 0
                    }
                constraints_map[constraint]['violations'] += 1

        constraints_data = list(constraints_map.values())

        logger.info(f"Returning validation results: {len(violations_data) if violations_data else 0} violations, {len(constraints_data) if constraints_data else 0} constraints")
        return conforms, report_graph_json, report_text, explanations, violations_data, constraints_data

    except Exception as e:
        import traceback
        logger.error(f"Error during validation: {str(e)}")
        logger.error(f"Validation error traceback: {traceback.format_exc()}")
        # Return a basic error response that won't break the frontend
        return False, "[]", f"Validation error: {str(e)}", [], [], []
