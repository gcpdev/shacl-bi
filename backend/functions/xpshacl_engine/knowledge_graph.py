import os
import json
import logging
import hashlib
from typing import Dict, Set, Optional, List

from dataclasses import dataclass, field
from .xpshacl_architecture import (
    ExplanationOutput,
    ConstraintViolation,
    JustificationTree,
    DomainContext,
    JustificationNode,
)

import rdflib
from rdflib import Namespace, Graph, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD

from .violation_signature import ViolationSignature

logger = logging.getLogger("phoenix.vkg")

# Define Namespaces
XSH = Namespace("http://xpshacl.org/#")
PHOENIX = Namespace("http://www.w3.org/ns/phoenix#") # Namespace for PHOENIX feedback

# Define the separator used for joining/splitting suggestions
SUGGESTION_SEPARATOR = "\n\n"

class ViolationKnowledgeGraph:
    def __init__(
        self,
        ontology_path: str = "data/xpshacl_ontology.ttl",
        kg_path: str = "data/validation_kg.ttl",
    ):
        self.ontology_path = ontology_path
        self.kg_path = kg_path
        self.graph = rdflib.Graph()
        self.graph.bind("xsh", XSH)
        self.graph.bind("phoenix", PHOENIX) # Bind the new namespace

        # Load ontology definitions
        try:
            if os.path.exists(self.ontology_path):
                self.graph.parse(self.ontology_path, format="turtle")
            else:
                logger.warning(f"Ontology file not found at {self.ontology_path}, skipping load.")
        except Exception as e:
            logger.error(f"Error parsing ontology file {self.ontology_path}: {e}")

        # Load existing instance data
        try:
            if os.path.exists(self.kg_path):
                self.graph.parse(self.kg_path, format="turtle")
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.error(f"Error parsing KG file {self.kg_path}: {e}")

    def save_kg(self):
        """Serialize the instance data."""
        try:
            os.makedirs(os.path.dirname(self.kg_path), exist_ok=True)
            self.graph.serialize(destination=self.kg_path, format="turtle")
        except Exception as e:
            logger.error(f"Failed to save KG to {self.kg_path}: {e}")

    def signature_to_uri(self, sig: ViolationSignature) -> URIRef:
        """Create a stable URIRef for a given signature. (Using existing logic)"""
        params = sig.constraint_params if sig.constraint_params else {}
        sorted_params = sorted(params.items())
        property_path_str = str(sig.property_path) if sig.property_path else "None"
        violation_type_str = str(sig.violation_type) if sig.violation_type else "None"

        signature_string = (
            f"{sig.constraint_id}|{property_path_str}|{violation_type_str}|{sorted_params}"
        )
        hex_digest = hashlib.md5(signature_string.encode("utf-8")).hexdigest()
        return XSH[f"sig_{hex_digest}"]

    # --- NEW METHOD FOR PHOENIX FEEDBACK ---
    def add_remediation_feedback(self, signature: ViolationSignature, repair_query: str, action: str):
        """
        Adds feedback about a remediation action to the Violation KG.
        """
        if action not in ["Accepted", "Edited", "Rejected"]:
            logger.warning(f"Invalid feedback action '{action}' provided. Skipping.")
            return

        sig_uri = self.signature_to_uri(signature)
        # Create a unique node for this specific feedback instance
        feedback_hash_input = str(sig_uri) + repair_query + action + str(os.urandom(8))
        feedback_node = PHOENIX[hashlib.md5(feedback_hash_input.encode()).hexdigest()]

        self.graph.add((feedback_node, RDF.type, PHOENIX.RemediationFeedback))
        self.graph.add((feedback_node, PHOENIX.hasTargetSignature, sig_uri))
        self.graph.add((feedback_node, PHOENIX.userAction, Literal(action)))
        self.graph.add((feedback_node, PHOENIX.usedRepairQuery, Literal(repair_query, datatype=XSD.string)))

        logger.info(f"Feedback '{action}' for violation signature stored in KG.")
        self.save_kg() # Save after adding feedback

    def get_feedback_for_signature(self, sig: ViolationSignature) -> List[Dict[str, str]]:
        """
        Retrieves all feedback entries for a given violation signature.
        Returns a list of dictionaries, each containing the action and the query.
        """
        sig_uri = self.signature_to_uri(sig)
        feedback_list = []

        query = """
        PREFIX phoenix: <http://www.w3.org/ns/phoenix#>
        SELECT ?action ?query
        WHERE {
            ?feedback a phoenix:RemediationFeedback .
            ?feedback phoenix:hasTargetSignature ?sig_uri .
            ?feedback phoenix:userAction ?action .
            ?feedback phoenix:usedRepairQuery ?query .
        }
        """
        
        results = self.graph.query(query, initBindings={'sig_uri': sig_uri})
        
        for row in results:
            feedback_list.append({
                "action": str(row.action),
                "query": str(row.query)
            })
            
        logger.debug(f"Found {len(feedback_list)} feedback entries for signature {sig_uri}")
        return feedback_list

    
    def load_kg(self):
        """Load the RDF graph from the TTL file (if it exists). Clears existing graph."""
        self.graph = rdflib.Graph()
        self.graph.bind("xsh", XSH)
        try:
            if os.path.exists(self.ontology_path):
                self.graph.parse(self.ontology_path, format="turtle")
        except Exception as e:
             logger.error(f"Error parsing ontology file {self.ontology_path} during load_kg: {e}")

        # Load KG data
        try:
            if os.path.exists(self.kg_path):
                self.graph.parse(self.kg_path, format="turtle")
        except FileNotFoundError:
            pass # It's okay if the KG file doesn't exist yet
        except Exception as e:
             logger.error(f"Error parsing KG file {self.kg_path} during load_kg: {e}")



    def has_violation(self, sig: ViolationSignature, language: str = "en") -> bool:
        """Check if a node in the KG exists with the same signature and language."""
        sig_uri = self.signature_to_uri(sig)

        # Check if the signature node itself exists
        if not (sig_uri, RDF.type, XSH.ViolationSignature) in self.graph:
            return False

        # Find the linked Explanation node
        expl_uri = self.graph.value(subject=sig_uri, predicate=XSH.hasExplanation)
        if not expl_uri:
            return False # Signature exists, but no linked explanation

        # Check for the specific language explanation text by iterating
        for obj in self.graph.objects(subject=expl_uri, predicate=XSH.naturalLanguageText):
            if isinstance(obj, Literal) and obj.language == language:
                return True # Found an explanation in the target language

        return False # No explanation found for this specific language

    def get_explanation(self, sig: ViolationSignature, language: str = "en") -> Optional[ExplanationOutput]:
        """
        Retrieve the explanation from the KG for a given signature and language.
        Assumes suggestions are stored as a single combined literal per language.
        """
        sig_uri = self.signature_to_uri(sig)

        # Find the linked Explanation node
        expl_uri = self.graph.value(subject=sig_uri, predicate=XSH.hasExplanation)
        if expl_uri is None:
             logger.debug(f"No explanation URI found for signature {sig_uri}")
             return None

        # Find language-specific natural language text by iterating
        nlt_literal = None
        for obj in self.graph.objects(subject=expl_uri, predicate=XSH.naturalLanguageText):
             if isinstance(obj, Literal) and obj.language == language:
                 nlt_literal = obj
                 break # Found the one for the specific language

        # Find language-specific correction suggestions (single literal) by iterating
        cs_list: Optional[List[str]] = None
        for obj in self.graph.objects(subject=expl_uri, predicate=XSH.correctionSuggestions):
            if isinstance(obj, Literal) and obj.language == language:
                 cs_combined = str(obj)
                 cs_list = cs_combined.split(SUGGESTION_SEPARATOR)
                 break # Found the combined suggestions for the specific language

        # Retrieve the repair query
        repair_query_literal = self.graph.value(subject=expl_uri, predicate=PHOENIX.hasRepairQuery)
        repair_query = str(repair_query_literal) if repair_query_literal else None

        # If no natural language text was found for the specific language, consider it "not found"
        if nlt_literal is None:
            logger.debug(f"No natural language text found for lang='{language}' for explanation {expl_uri}")
            return None

        # Retrieve other potentially language-independent data
        provided_by_model = self.graph.value(subject=expl_uri, predicate=XSH.providedByModel)
        violation_data = self.graph.value(subject=expl_uri, predicate=XSH.violation)
        justification_tree_data = self.graph.value(subject=expl_uri, predicate=XSH.justificationTree)
        retrieved_context_data = self.graph.value(subject=expl_uri, predicate=XSH.retrievedContext)

        # Attempt to deserialize complex objects with error handling
        violation = None
        if violation_data:
             try:
                 violation = ConstraintViolation.from_dict(json.loads(str(violation_data)))
             except Exception as e:
                 logger.error(f"Failed to decode/instantiate ConstraintViolation for {expl_uri}: {e}")

        justification_tree = None
        if justification_tree_data:
             try:
                 justification_tree_dict = json.loads(str(justification_tree_data))
                 temp_violation_for_tree = violation
                 if not temp_violation_for_tree and "violation" in justification_tree_dict:
                      try:
                          temp_violation_for_tree = ConstraintViolation.from_dict(justification_tree_dict["violation"])
                      except Exception: pass # Ignore if embedded violation fails

                 if "justification" in justification_tree_dict and temp_violation_for_tree:
                     root_node = JustificationNode.from_dict(justification_tree_dict["justification"])
                     justification_tree = JustificationTree(root=root_node, violation=temp_violation_for_tree)
                 else:
                      logger.warning(f"Could not reconstruct JustificationTree for {expl_uri}: Missing 'justification' key or associated violation.")
             except Exception as e:
                  logger.error(f"Failed to decode/instantiate JustificationTree for {expl_uri}: {e}")

        retrieved_context = None
        if retrieved_context_data:
             try:
                 # Assuming DomainContext.from_dict can handle the serialized format
                 retrieved_context = DomainContext.from_dict(json.loads(str(retrieved_context_data)))
             except Exception as e:
                 logger.error(f"Failed to decode/instantiate DomainContext for {expl_uri}: {e}")

        return ExplanationOutput(
            natural_language_explanation=str(nlt_literal),
            correction_suggestions=cs_list, # Return the list of strings
            violation=violation,
            justification_tree=justification_tree,
            retrieved_context=retrieved_context,
            provided_by_model=str(provided_by_model) if provided_by_model else None,
            proposed_repair_query=repair_query
        )

    def add_violation(self, sig: ViolationSignature, explanation: ExplanationOutput, language: str = "en"):
        """
        Add a new violation signature and explanation to the KG with a language tag.
        Combines correction suggestions into a single literal per language.
        Prevents adding duplicate language-tagged text/suggestions.
        """
        sig_uri = self.signature_to_uri(sig)

        # Check if an explanation node exists for this signature, create if not
        expl_uri = self.graph.value(subject=sig_uri, predicate=XSH.hasExplanation)
        new_explanation_node = False
        if not expl_uri:
            new_explanation_node = True
            expl_uri = URIRef(str(sig_uri) + "_explanation") # Use a more predictable URI if needed
            self.graph.add((sig_uri, RDF.type, XSH.ViolationSignature))
            self.graph.add((expl_uri, RDF.type, XSH.Explanation))
            self.graph.add((sig_uri, XSH.hasExplanation, expl_uri))
            # Add signature components only when creating the signature node
            self.graph.add((sig_uri, XSH.constraintComponent, Literal(sig.constraint_id)))
            if sig.property_path:
                self.graph.add((sig_uri, XSH.propertyPath, Literal(sig.property_path)))
            if sig.violation_type:
                self.graph.add((sig_uri, XSH.violationType, Literal(str(sig.violation_type))))
            if sig.constraint_params:
                try:
                    json_params = json.dumps(sig.constraint_params, sort_keys=True, default=str)
                    self.graph.add((sig_uri, XSH.constraintParams, Literal(json_params)))
                except TypeError as e:
                    logger.error(f"Failed to serialize constraint_params for {sig_uri}: {e}")

        # --- Store natural language text (preventing duplicates for same lang) ---
        has_existing_nlt = any(
            isinstance(obj, Literal) and obj.language == language
            for obj in self.graph.objects(expl_uri, XSH.naturalLanguageText)
        )
        if not has_existing_nlt and explanation.natural_language_explanation:
            self.graph.add((expl_uri, XSH.naturalLanguageText, Literal(explanation.natural_language_explanation, lang=language)))

        # --- Store correction suggestions (COMBINED, preventing duplicates for same lang) ---
        has_existing_suggestions_for_lang = any(
            isinstance(obj, Literal) and obj.language == language
            for obj in self.graph.objects(expl_uri, XSH.correctionSuggestions)
        )
        if explanation.correction_suggestions and not has_existing_suggestions_for_lang:
            suggestion_string_to_add = SUGGESTION_SEPARATOR.join(explanation.correction_suggestions)
            self.graph.add((expl_uri, XSH.correctionSuggestions, Literal(suggestion_string_to_add, lang=language)))

        # --- Store the proposed repair query (language-independent) ---
        if explanation.proposed_repair_query and not self.graph.value(expl_uri, PHOENIX.hasRepairQuery):
            self.graph.add((expl_uri, PHOENIX.hasRepairQuery, Literal(explanation.proposed_repair_query)))

        # Add model info (overwriting previous value if necessary)
        if explanation.provided_by_model:
            self.graph.remove((expl_uri, XSH.providedByModel, None))
            self.graph.add((expl_uri, XSH.providedByModel, Literal(explanation.provided_by_model)))

        # Store the complex data as JSON only when creating the explanation node for the first time
        if new_explanation_node:
             # Helper to add JSON literal safely
             def add_json_literal(predicate, data_object):
                 if data_object and not self.graph.value(expl_uri, predicate):
                     try:
                         json_str = json.dumps(data_object.to_dict(), default=str)
                         self.graph.add((expl_uri, predicate, Literal(json_str)))
                     except AttributeError: logger.error(f"Object for {predicate} missing .to_dict() for {expl_uri}")
                     except TypeError as e: logger.error(f"Failed to serialize {predicate} for {expl_uri}: {e}")
                     except Exception as e: logger.error(f"Unexpected error serializing {predicate} for {expl_uri}: {e}")


             add_json_literal(XSH.violation, explanation.violation)
             add_json_literal(XSH.justificationTree, explanation.justification_tree)
             add_json_literal(XSH.retrievedContext, explanation.retrieved_context)

    def clear(self):
        """Deletes the KG file and clears the in-memory graph."""
        try:
            if os.path.exists(self.kg_path):
                os.remove(self.kg_path)
                logger.info(f"Cache file deleted: {self.kg_path}")
            self.graph = rdflib.Graph()
            self.graph.bind("xsh", XSH)
            self.graph.bind("phoenix", PHOENIX)
        except Exception as e:
            logger.error(f"Error clearing cache: {e}", exc_info=True)
            raise

    def size(self) -> int:
        """Return the number of triples in the graph."""
        return len(self.graph)
