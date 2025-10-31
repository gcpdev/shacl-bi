import os
import json
import tempfile
import subprocess
import logging
import time
from typing import Dict, List, Optional
from rdflib import Graph
from pyshacl import validate

from .repair_engine import SuggestionRepairGenerator


# Alias for compatibility with tests
class RepairEngine(SuggestionRepairGenerator):
    """RepairEngine with method alias for test compatibility"""

    def generate_repair(self, violation, justification_tree, context, language="en"):
        """Alias for generate_repair_object to maintain test compatibility"""
        return self.generate_repair_object(
            violation, justification_tree, context, language
        )


from .extended_shacl_validator import ExtendedShaclValidator
from .justification_tree_builder import JustificationTreeBuilder
from .context_retriever import ContextRetriever
from .knowledge_graph import ViolationKnowledgeGraph
from .violation_signature_factory import create_violation_signature
from .explanation_generator import ExplanationGenerator as BaseExplanationGenerator
from .xpshacl_architecture import (
    ConstraintViolation,
    JustificationTree,
    DomainContext,
    ExplanationOutput,
)


# Alias for compatibility with tests
class ExplanationGenerator(BaseExplanationGenerator):
    """ExplanationGenerator with method alias for test compatibility"""

    def generate_explanation(self, violation, justification_tree, context):
        """Alias for generate_explanation_output to maintain test compatibility"""
        return self.generate_explanation_output(
            violation, justification_tree, context, ["en"]
        )


# Configure logging
log_level = os.environ.get("FLASK_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class XPSHACLEngine:
    """
    Main XPSHACL engine orchestrator that combines validation, explanation generation,
    and repair functionality for comprehensive SHACL violation analysis.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the XPSHACL engine with optional configuration.

        Args:
            config: Dictionary containing engine configuration options
        """
        self.config = config or {}

        # Initialize core components
        self.validator = None  # Will be initialized when shapes graph is provided
        self.explanation_generator = None  # Will be initialized when needed
        self.repair_engine = None  # Will be initialized when needed
        self.knowledge_graph = ViolationKnowledgeGraph()

        # Statistics tracking
        self._statistics = {
            "validations_performed": 0,
            "violations_detected": 0,
            "explanations_generated": 0,
            "repairs_generated": 0,
        }

        # Performance metrics
        self._performance_metrics = {
            "last_validation_time": 0.0,
            "total_validation_time": 0.0,
            "average_validation_time": 0.0,
        }

        # Caching
        self._cache = {} if self.config.get("enable_caching", False) else None

        logger.info("XPSHACL Engine initialized")

    def validate_dataset(
        self, shapes_graph: Graph, data_graph: Graph
    ) -> List[ConstraintViolation]:
        """
        Validate a dataset against shapes and return violations.

        Args:
            shapes_graph: Graph containing SHACL shapes
            data_graph: Graph containing data to validate

        Returns:
            List of constraint violations
        """
        if not isinstance(shapes_graph, Graph) or not isinstance(data_graph, Graph):
            raise TypeError(
                "Both shapes_graph and data_graph must be rdflib.Graph objects"
            )

        # Check cache if enabled
        cache_key = None
        if self._cache is not None:
            cache_key = (hash(shapes_graph.serialize()), hash(data_graph.serialize()))
            if cache_key in self._cache:
                logger.debug("Using cached validation results")
                return self._cache[cache_key]

        # Initialize validator if needed
        if self.validator is None:
            self.validator = ExtendedShaclValidator(shapes_graph)

        # Perform validation with performance timing
        start_time = time.perf_counter()
        violations = self.validator.validate(data_graph)
        end_time = time.perf_counter()

        # Update statistics
        self._statistics["validations_performed"] += 1
        self._statistics["violations_detected"] += len(violations)

        # Update performance metrics
        validation_time = end_time - start_time
        self._performance_metrics["last_validation_time"] = validation_time
        self._performance_metrics["total_validation_time"] += validation_time
        self._performance_metrics["average_validation_time"] = (
            self._performance_metrics["total_validation_time"]
            / self._statistics["validations_performed"]
        )

        # Cache results if enabled
        if self._cache is not None and cache_key is not None:
            self._cache[cache_key] = violations

        logger.info(
            f"Validation completed in {validation_time:.4f}s, found {len(violations)} violations"
        )
        return violations

    def generate_explanations(
        self, shapes_graph: Graph, data_graph: Graph
    ) -> List[ExplanationOutput]:
        """
        Generate explanations for all violations in a dataset.

        Args:
            shapes_graph: Graph containing SHACL shapes
            data_graph: Graph containing data to validate

        Returns:
            List of explanation outputs
        """
        violations = self.validate_dataset(shapes_graph, data_graph)
        if not violations:
            return []

        # Initialize explanation generator if needed
        if self.explanation_generator is None:
            model_name = self.config.get("model", "gpt-4o-mini-2024-07-18")
            self.explanation_generator = ExplanationGenerator(model_name=model_name)

        explanations = []
        for violation in violations:
            # Build justification tree
            tree_builder = JustificationTreeBuilder(data_graph, shapes_graph)
            justification_tree = tree_builder.build_justification_tree(violation)

            # Retrieve context
            context_retriever = ContextRetriever(data_graph, shapes_graph)
            context = context_retriever.retrieve_context(violation)

            # Generate explanation using the generator
            # Use the alias method that tests expect
            explanation_result = self.explanation_generator.generate_explanation(
                violation, justification_tree, context
            )

            # If the result is already an ExplanationOutput (mocked case), use it directly
            if hasattr(explanation_result, "natural_language_explanation"):
                explanation_output = explanation_result
            else:
                # Real case: convert from dictionary to ExplanationOutput
                if "en" in explanation_result:
                    explanation_text, suggestions = explanation_result["en"]
                    explanation_output = ExplanationOutput(
                        violation=violation,
                        justification_tree=justification_tree,
                        retrieved_context=context,
                        natural_language_explanation=explanation_text,
                        correction_suggestions=(
                            [suggestions]
                            if isinstance(suggestions, str)
                            else suggestions
                        ),
                        provided_by_model=self.explanation_generator.model_name,
                    )
                else:
                    continue

            explanations.append(explanation_output)

        self._statistics["explanations_generated"] += len(explanations)
        return explanations

    def generate_repairs(self, shapes_graph: Graph, data_graph: Graph) -> List[Dict]:
        """
        Generate repair suggestions for all violations in a dataset.

        Args:
            shapes_graph: Graph containing SHACL shapes
            data_graph: Graph containing data to validate

        Returns:
            List of repair objects
        """
        violations = self.validate_dataset(shapes_graph, data_graph)
        if not violations:
            return []

        # Initialize repair engine if needed
        if self.repair_engine is None:
            self.repair_engine = RepairEngine(vkg=self.knowledge_graph)

        repairs = []
        for violation in violations:
            # Build justification tree
            tree_builder = JustificationTreeBuilder(data_graph, shapes_graph)
            justification_tree = tree_builder.build_justification_tree(violation)

            # Retrieve context
            context_retriever = ContextRetriever(data_graph, shapes_graph)
            context = context_retriever.retrieve_context(violation)

            # Generate repair using the alias method that tests expect
            repair = self.repair_engine.generate_repair(
                violation, justification_tree, context
            )
            if repair:
                repairs.append(repair)

        self._statistics["repairs_generated"] += len(repairs)
        return repairs

    def batch_validate(
        self, shapes_graph: Graph, data_graphs: List[Graph]
    ) -> List[List[ConstraintViolation]]:
        """
        Validate multiple datasets against the same shapes.

        Args:
            shapes_graph: Graph containing SHACL shapes
            data_graphs: List of graphs containing data to validate

        Returns:
            List of violation lists, one for each dataset
        """
        results = []
        for data_graph in data_graphs:
            violations = self.validate_dataset(shapes_graph, data_graph)
            results.append(violations)

        return results

    def get_statistics(self) -> Dict:
        """
        Get engine statistics.

        Returns:
            Dictionary containing engine statistics
        """
        return self._statistics.copy()

    def get_performance_metrics(self) -> Dict:
        """
        Get performance metrics.

        Returns:
            Dictionary containing performance metrics
        """
        return self._performance_metrics.copy()

    def clear_caches(self):
        """Clear internal caches."""
        if self._cache is not None:
            self._cache.clear()
        logger.info("Engine caches cleared")

    def free_memory(self):
        """Free memory by clearing caches and resetting components."""
        self.clear_caches()
        self.validator = None
        self.explanation_generator = None
        self.repair_engine = None
        logger.info("Engine memory freed")

    def serialize_state(self) -> Dict:
        """
        Serialize engine state for persistence.

        Returns:
            Dictionary containing serializable engine state
        """
        return {
            "config": self.config,
            "statistics": self._statistics,
            "performance_metrics": self._performance_metrics,
        }

    def restore_state(self, state: Dict):
        """
        Restore engine state from serialized data.

        Args:
            state: Dictionary containing engine state
        """
        self.config = state.get("config", {})
        self._statistics = state.get("statistics", self._statistics)
        self._performance_metrics = state.get(
            "performance_metrics", self._performance_metrics
        )
        logger.info("Engine state restored")


def edit_repair_object(repair_json: dict) -> dict:
    """Saves the repair object to a temp file and opens it in a system editor."""
    editor = os.environ.get(
        "EDITOR", "vim"
    )  # Defaults to vim if no default editor is set

    with tempfile.NamedTemporaryFile(
        suffix=".json", mode="w+", delete=False, encoding="utf-8"
    ) as tf:
        tf.write(json.dumps(repair_json, indent=2))
        temp_file_name = tf.name

    logger.info(
        f"Opening repair object in '{editor}'. Please save and close the editor when done."
    )

    try:
        subprocess.run([editor, temp_file_name], check=True)
    except FileNotFoundError:
        logger.error(
            f"Editor '{editor}' not found. Please set the EDITOR environment variable."
        )
        return repair_json  # Return original object if editor fails
    except subprocess.CalledProcessError as e:
        logger.error(f"Editor exited with an error: {e}")
        return repair_json

    with open(temp_file_name, "r", encoding="utf-8") as f:
        edited_content = f.read()

    os.remove(temp_file_name)

    try:
        return json.loads(edited_content)
    except json.JSONDecodeError:
        logger.error(
            "Failed to parse the edited JSON. Returning the original repair object."
        )
        return repair_json


def verify_and_execute_repair(
    main_graph: Graph, focus_node_uri: str, repair_query: str
) -> bool:
    """
    The Verification & Execution Engine (VEE).
    Performs a 'dry run' of the repair and executes it only if successful.
    """
    logger.info("--- Starting Verification (Dry Run) ---")

    # 1. Create a temporary copy of the graph for the dry run
    temp_graph = Graph()
    temp_graph += main_graph

    # 2. Apply the repair to the temporary graph
    try:
        temp_graph.update(repair_query)
        logger.info("Dry run update applied successfully.")
    except Exception as e:
        logger.error(f"SPARQL query failed during dry run: {e}")
        return False

    # 3. Re-validate the focus node against all shapes in the temporary graph
    # Note: For simplicity, we re-validate the whole graph.
    # For performance, we can pass focus_nodes=[rdflib.URIRef(focus_node_uri)]
    r = validate(temp_graph, shacl_graph=temp_graph)
    conforms, _, _ = r

    if conforms:
        logger.info(
            "✅ Verification successful! The fix is correct and introduces no new violations."
        )
        # 4. If verification passes, execute on the main graph
        main_graph.update(repair_query)
        logger.info("--- Executing repair on main graph ---")
        return True
    else:
        logger.error(
            "❌ Verification failed! The proposed fix does not resolve the violation or introduces a new one."
        )
        return False


def main():
    # --- Setup ---
    data_graph_file = "data/sample_data.ttl"
    shapes_graph_file = "data/sample_shapes.ttl"
    kg_path = "data/phoenix_violation_kg.ttl"
    ontology_path = "data/xpshacl_ontology.ttl"

    # --- Load Graphs ---
    data_graph = Graph().parse(data_graph_file, format="turtle")
    shapes_graph = Graph().parse(shapes_graph_file, format="turtle")

    # --- Instantiate Components ---
    validator = ExtendedShaclValidator(shapes_graph)
    violations = validator.validate(data_graph)

    if not violations:
        logger.info("🎉 No SHACL violations found.")
        return

    logger.info(f"Found {len(violations)} violations. Starting remediation workflow...")

    vkg = ViolationKnowledgeGraph(ontology_path=ontology_path, kg_path=kg_path)
    srg = SuggestionRepairGenerator(vkg=vkg)

    # --- Main Remediation Loop ---
    for violation in violations:
        logger.info(
            f"\n{'='*20}\nProcessing violation for focus node: {violation.focus_node}\n{'='*20}"
        )

        # --- Signature and Cache Check ---
        signature = create_violation_signature(violation)
        cached_explanation = vkg.get_explanation(signature)

        if cached_explanation:
            logger.info("Found cached explanation for this violation type.")
            # Reconstruct repair_object from cached_explanation
            repair_object = {
                "explanation_natural_language": cached_explanation.natural_language_explanation,
                "suggestion_natural_language": "\n".join(
                    cached_explanation.correction_suggestions or []
                ),
                "proposed_repair": {"query": cached_explanation.proposed_repair_query},
            }
        else:
            logger.info("No cached explanation found. Generating new suggestion...")
            tree_builder = JustificationTreeBuilder(data_graph, shapes_graph)
            justification_tree = tree_builder.build_justification_tree(violation)
            context_retriever = ContextRetriever(data_graph, shapes_graph)
            context = context_retriever.retrieve_context(violation)

            repair_object = srg.generate_repair_object(
                violation, justification_tree, context
            )

            if repair_object:
                # Add to cache for this run
                vkg.add_violation(signature, srg.last_explanation_output)
            else:
                logger.error("Could not generate a repair suggestion. Skipping.")
                continue

        if not repair_object or not repair_object.get("proposed_repair", {}).get(
            "query"
        ):
            logger.error(
                "Could not generate or retrieve a repair suggestion. Skipping."
            )
            continue

        print("\n--- 💡 PHOENIX SUGGESTION ---")
        print(f"Explanation: {repair_object['explanation_natural_language']}")
        print(f"Suggestion: {repair_object['suggestion_natural_language']}")
        print(f"Proposed Query:\n{repair_object['proposed_repair']['query']}")
        print("--------------------------\n")

        # --- IRI ---
        while True:
            choice = input(
                "Choose an action: [A]ccept, [E]dit, [R]eject, [S]kip suggestion? "
            ).lower()
            if choice in ["a", "e", "r", "s"]:
                break
            print("Invalid choice. Please try again.")

        # --- Handle user choice and log feedback ---
        user_action = "Skipped"
        if choice == "r":
            user_action = "Rejected"
            vkg.add_remediation_feedback(
                signature, repair_object["proposed_repair"]["query"], user_action
            )
            logger.info("Suggestion rejected and feedback logged.")
            continue
        elif choice == "s":
            logger.info("Suggestion skipped.")
            continue

        final_repair_object = repair_object
        if choice == "e":
            user_action = "Edited"
            final_repair_object = edit_repair_object(repair_object)
        elif choice == "a":
            user_action = "Accepted"

        # --- VEE ---
        repair_query = final_repair_object["proposed_repair"]["query"]
        was_successful = verify_and_execute_repair(
            data_graph, violation.focus_node, repair_query
        )

        if was_successful:
            logger.info("Repair successfully applied.")
            vkg.add_remediation_feedback(signature, repair_query, user_action)
        else:
            logger.error("Repair failed verification. Graph not modified.")
            vkg.add_remediation_feedback(signature, repair_query, "VerificationFailed")

    # --- Save ---
    data_graph.serialize(destination="data/repaired_data.ttl", format="turtle")
    logger.info("\nRemediation process complete. Repaired graph saved.")


def process_uploaded_files(data_path: str, shapes_path: str, ai_config: dict) -> dict:
    """
    Process uploaded data and shapes files for validation.
    Uses backend AI configuration for processing.
    """
    try:
        logger.info(f"Processing uploaded files: {data_path} and {shapes_path}")

        # Load graphs from uploaded files
        data_graph = Graph().parse(data_path, format="turtle")
        shapes_graph = Graph().parse(shapes_path, format="turtle")

        # Validate data against shapes
        conforms, results_graph, results_text = validate(
            data_graph, shacl_graph=shapes_graph
        )

        violations = []
        if not conforms:
            # Parse validation results to extract violations
            for result in results_graph.objects(None, None):
                # Extract violation information from the results graph
                # This is a simplified version - you may need to expand this based on your validation report format
                violations.append({"severity": "violation", "result": str(result)})

        logger.info(f"Validation completed. Found {len(violations)} violations.")

        return {
            "conforms": conforms,
            "violations_count": len(violations),
            "violations": violations,
            "ai_config_used": {
                "model": ai_config["model"],
                "api_configured": bool(ai_config["api_key"]),
            },
        }

    except Exception as e:
        logger.error(f"Error processing uploaded files: {str(e)}")
        raise


def get_explanation_and_suggestion(violation: dict) -> tuple[str, str]:
    """
    Gets the explanation and suggestion for a violation.
    Simplified version that provides basic feedback without full PHOENIX infrastructure.
    """
    try:
        logger.info(f"Processing violation details for: {violation}")

        # Extract basic information from the violation
        focus_node = violation.get("focus_node", violation.get("focusNode", "Unknown"))
        message = violation.get(
            "message", violation.get("error_message", "Constraint violation")
        )
        constraint_id = violation.get(
            "constraint_id", violation.get("constraintComponent", "Unknown")
        )

        # Generate a simple explanation based on the violation type
        explanation = f"This violation occurs because the data for '{focus_node}' does not conform to the constraint '{constraint_id}'. "
        explanation += f"The system reports: {message}"

        # Generate a basic suggestion
        suggestion = f"To fix this violation, please review the data associated with '{focus_node}' and ensure it complies with the constraint requirements. "
        suggestion += "You may need to update the value, add missing properties, or correct the data format."

        logger.info(f"Generated explanation for violation at {focus_node}")

        return explanation, suggestion

    except Exception as e:
        logger.error(f"Error generating explanation and suggestion: {str(e)}")
        return "Error generating explanation", "Error generating suggestion"


if __name__ == "__main__":
    main()
