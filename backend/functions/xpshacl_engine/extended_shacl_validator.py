# src/extended_shacl_validator.py

import logging
from rdflib import Graph, URIRef
from rdflib.namespace import RDF
from pyshacl import validate
from typing import List
import time
import exrex

from .xpshacl_architecture import ConstraintViolation, ViolationType
from .context_retriever import _serialize_focus_node

# SHACL namespace
SH = "http://www.w3.org/ns/shacl#"
logger = logging.getLogger(__name__)

class ExtendedShaclValidator:
    """
    A wrapper for pyshacl that extracts detailed information about each
    constraint violation from the validation report graph.
    """

    def __init__(self, shapes_graph: Graph):
        if not isinstance(shapes_graph, Graph):
            raise TypeError("shapes_graph must be an rdflib.Graph object")
        self.shapes_graph = shapes_graph
        self.results_graph = None

    def _get_violation_(self, constraint_component: URIRef) -> ViolationType:
        """Categorizes the violation based on the SHACL constraint component."""
        # CORRECTED: This map now only uses enum members that are confirmed to exist.
        component_map = {
            "MinCountConstraintComponent": ViolationType.CARDINALITY,
            "MaxCountConstraintComponent": ViolationType.CARDINALITY,
        }
        component_name = str(constraint_component).split('#')[-1]
        # Return the specific type if mapped, otherwise default to OTHER
        return component_map.get(component_name, ViolationType.OTHER)

    def validate(self, data_graph: Graph) -> List[ConstraintViolation]:
        """
        Validates the data graph against the shapes graph and returns a list
        of structured ConstraintViolation objects.
        """
        if not isinstance(data_graph, Graph):
            raise TypeError("data_graph must be an rdflib.Graph object")

        # --- PERFORMANCE LOGGING ---
        start_time = time.perf_counter()
        
        conforms, results_graph, _ = validate(
            data_graph, shacl_graph=self.shapes_graph, inference="none", abort_on_first=False
        )
        self.results_graph = results_graph
        
        end_time = time.perf_counter()
        logger.debug(f"pyshacl validation took {end_time - start_time:.4f} seconds.")
        # --- END PERFORMANCE LOGGING ---

        if conforms:
            return []

        return self._extract_violations_from_graph(results_graph, data_graph)

    def _extract_violations_from_graph(self, results_graph: Graph, data_graph: Graph) -> List[ConstraintViolation]:
        """Extracts ConstraintViolation objects from a validation report graph."""
        violations = []
        # Query the results graph to find all validation results
        validation_results = results_graph.subjects(
            predicate=RDF.type, object=URIRef(SH + "ValidationResult")
        )

        for result_node in validation_results:
            # Using .value() can return None, so we handle that gracefully
            focus_node_obj = results_graph.value(subject=result_node, predicate=URIRef(SH + "focusNode"))
            source_shape_obj = results_graph.value(subject=result_node, predicate=URIRef(SH + "sourceShape"))
            constraint_component_obj = results_graph.value(
                    subject=result_node, predicate=URIRef(SH + "sourceConstraintComponent")
                )
            result_path_obj = results_graph.value(subject=result_node, predicate=URIRef(SH + "resultPath"))
            value_obj = results_graph.value(subject=result_node, predicate=URIRef(SH + "value"))

            violation = ConstraintViolation(
                focus_node=str(focus_node_obj) if focus_node_obj else "",
                shape_id=str(source_shape_obj) if source_shape_obj else "",
                constraint_id=str(constraint_component_obj) if constraint_component_obj else "",
                violation_type=self._get_violation_(constraint_component_obj),
                property_path=str(result_path_obj) if result_path_obj else "",
                value=str(value_obj) if value_obj else None
            )

            # --- PHOENIX CONTEXT ENRICHMENT ---
            if "MaxCountConstraintComponent" in violation.constraint_id and violation.focus_node and violation.property_path:
                # Find the maxCount value from the shapes graph
                max_count = self.shapes_graph.value(subject=source_shape_obj, predicate=URIRef(SH + "maxCount"))
                if max_count:
                    violation.context["maxCount"] = int(max_count)

                # Find all actual values from the data graph
                actual_values = [
                    str(o) for o in data_graph.objects(
                        subject=URIRef(violation.focus_node),
                        predicate=URIRef(violation.property_path)
                    )
                ]
                violation.context["actualValues"] = actual_values
            
            # --- PHOENIX CONTEXT ENRICHMENT FOR PATTERNS ---
            if "PatternConstraintComponent" in violation.constraint_id:
                pattern = self.shapes_graph.value(subject=source_shape_obj, predicate=URIRef(SH + "pattern"))
                if pattern:
                    violation.context["pattern"] = str(pattern)
                    try:
                        # Generate an example that matches the pattern
                        violation.context["exampleValue"] = exrex.getone(str(pattern))
                    except Exception as e:
                        logger.warning(f"Could not generate example for pattern '{pattern}': {e}")

                message = self.shapes_graph.value(subject=source_shape_obj, predicate=URIRef(SH + "message"))
                if message:
                    violation.context["message"] = str(message)

            # --- END ENRICHMENT ---

            logger.debug(f"Processing violation with constraint ID: {violation.constraint_id}")
            # --- PHOENIX CONTEXT ENRICHMENT FOR SH:IN ---
            if "InConstraintComponent" in violation.constraint_id:
                logger.debug(f"Found InConstraintComponent. Extracting values for shape {source_shape_obj}")
                # The sh:in property points to an RDF list in the shapes graph
                in_list_head = self.shapes_graph.value(subject=source_shape_obj, predicate=URIRef(SH + "in"))
                if in_list_head:
                    allowed_values = []
                    # Traverse the RDF list (which is a linked list of nodes)
                    while in_list_head and in_list_head != RDF.nil:
                        # Get the first item in the current list node
                        item = self.shapes_graph.value(subject=in_list_head, predicate=RDF.first)
                        if item:
                            allowed_values.append(str(item))
                        # Move to the rest of the list
                        in_list_head = self.shapes_graph.value(subject=in_list_head, predicate=RDF.rest)
                    violation.allowed_values = allowed_values
                    logger.debug(f"Extracted allowed values: {violation.allowed_values}")

            violations.append(violation)

            # --- PHOENIX CONTEXT ENRICHMENT FOR FOCUS NODE DEFINITION ---
            if violation.focus_node:
                try:
                    violation.context["focusNodeDefinition"] = _serialize_focus_node(
                        URIRef(violation.focus_node), data_graph
                    )
                except Exception as e:
                    logger.warning(f"Could not serialize focus node {violation.focus_node}: {e}")
            # --- END ENRICHMENT ---

        return violations