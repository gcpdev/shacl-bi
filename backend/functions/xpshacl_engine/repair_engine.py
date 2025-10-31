import os
import json
import logging
import time
from typing import Dict, Optional
from dotenv import load_dotenv
import litellm

from .xpshacl_architecture import (
    ConstraintViolation,
    JustificationTree,
    DomainContext,
    ExplanationOutput,
)
from .knowledge_graph import ViolationKnowledgeGraph
from .violation_signature_factory import create_violation_signature
import config

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("phoenix")

# --- UPDATED AND ENHANCED SYSTEM PROMPT ---
REPAIR_SYSTEM_PROMPT = """You are an expert data quality analyst who helps business users understand and fix data issues. Your primary goal is to translate complex technical validation results into simple, business-oriented explanations and actionable suggestions. You will also generate the technical code needed to fix the issue.

You will be given a technical description of a data quality violation. Your task is to return a single, valid JSON object with the following structure.

**IMPORTANT:** The `explanation_natural_language` and `suggestion_natural_language` fields MUST be written for a non-technical business audience.
- DO NOT use technical jargon like 'node', 'property', 'literal', 'URI', 'SHACL', or 'SPARQL' in these fields.
- For `explanation_natural_language`: Frame the explanation around the business rule that was violated. Instead of 'node', use 'data record' or 'item'. Instead of 'property', use 'attribute' or 'field'.
    - Example: 'This data record is incomplete. Business rules require that every person must have a name, but this record is missing one.'
- For `suggestion_natural_language`: Suggest the clear, business action required to correct the data.
    - Example: 'Provide the missing name for this person\'s record.'

The `proposed_repair` field is for the system and MUST contain a technically correct SPARQL query.
- Based on the violation's 'sourceConstraintComponent', generate the correct type of SPARQL query:
    - 'MinCountConstraintComponent' (a value is missing): Generate a SPARQL INSERT query. CRITICALLY, the value to be inserted MUST be the placeholder '$user_provided_value'. DO NOT use an empty string or any other value.
    - 'MaxCountConstraintConstraintComponent' (has too many values) -> SPARQL DELETE query with actual violating value in DELETE clause.
    - 'DatatypeConstraintComponent' (value has wrong datatype) -> SPARQL DELETE/INSERT query. For this, the INSERT clause MUST explicitly type the new value using the correct datatype from the violation context (e.g., "42"^^xsd:integer).
    - 'PatternConstraintComponent' (value doesn't match pattern) -> SPARQL DELETE/INSERT query with $user_provided_value placeholder.
    - 'InConstraintComponent' (value not in allowed list) -> SPARQL DELETE/INSERT query with actual violating value in DELETE clause and first allowed value in INSERT clause.
- For MinCount and Pattern constraints, use the placeholder `$user_provided_value` WITHOUT quotes. This will be replaced at runtime with user input.
- For MaxCount and Datatype constraints, use the actual violating value from the input in the DELETE clause.
- The INSERT clause should use intelligent defaults based on the property name and datatype requirements.

You MUST return ONLY the JSON object, with no other text before or after it.

JSON Structure:
{
  "violation_signature": "A unique identifier for the violation type, derived from the input.",
  "explanation_natural_language": "A clear, business-oriented explanation of the data quality problem.",
  "suggestion_natural_language": "A brief, actionable business suggestion for the user.",
  "proposed_repair": {
    "type": "SPARQL_UPDATE",
    "query": "A complete and syntactically correct SPARQL UPDATE query to fix the violation."
  }
}
"""


class SuggestionRepairGenerator:
    """
    Generates a structured repair object, including a formal SPARQL query, using an LLM.
    This is the core of the PHOENIX framework's "actionability" feature.
    """

    def __init__(
        self, vkg: ViolationKnowledgeGraph, model_name: str = config.SRG_MODEL
    ):
        self.vkg = vkg
        self.model_name = model_name
        self.last_explanation_output: Optional[ExplanationOutput] = None

    def generate_repair_object(
        self,
        violation: ConstraintViolation,
        justification_tree: JustificationTree,
        context: DomainContext,
        language: str = "en",
    ) -> Optional[Dict]:
        """
        Calls the LLM to generate a structured JSON repair object for a given violation.
        """
        prompt = f"Generate a structured repair object for the following SHACL violation in '{language}'.\n\n"
        prompt += f"Violation Details: {json.dumps(violation.to_dict(), indent=2, default=str)}\n\n"
        prompt += f"Justification Tree: {json.dumps(justification_tree.to_dict(), indent=2, default=str)}\n\n"
        prompt += f"Relevant Context: {json.dumps(context.to_dict(), indent=2, default=str)}\n\n"

        # --- PHOENIX FEEDBACK LOOP ---
        signature = create_violation_signature(violation)
        feedback = self.vkg.get_feedback_for_signature(signature)

        if feedback:
            feedback_summary = "\n\n--- Historical Feedback ---\n"
            feedback_summary += "Based on past user actions for this type of data issue, please consider the following:\n"

            accepted_queries = [
                f"- This query was previously accepted by a user:\n{item['query']}"
                for item in feedback
                if item["action"] == "AcceptFix"
            ]
            rejected_queries = [
                f"- This query was previously rejected by a user:\n{item['query']}"
                for item in feedback
                if item["action"] == "RejectFix"
            ]

            if accepted_queries:
                feedback_summary += "\nPreviously Accepted Solutions:\n" + "\n".join(
                    accepted_queries
                )
            if rejected_queries:
                feedback_summary += "\nPreviously Rejected Solutions:\n" + "\n".join(
                    rejected_queries
                )

            feedback_summary += "\nUse this historical feedback to generate a better, more likely to be accepted, repair query and explanation.\n"

            prompt += feedback_summary
        # --- END FEEDBACK LOOP ---

        logger.debug(f"Sending following prompt to LLM:\n{prompt}")

        try:
            start_time = time.perf_counter()

            # --- UNIFIED LLM CALL USING LITELLM ---
            # Automatically select the correct provider and API key
            model_name = self.model_name
            if "gemini" in model_name and not model_name.startswith("gemini/"):
                model_name = f"gemini/{model_name}"

            # GPT-5 models only support temperature=1
            temperature = 0.1 if "gpt-5" not in model_name else 1.0

            response = litellm.completion(
                model=model_name,
                messages=[
                    {"role": "system", "content": REPAIR_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,  # Lower temperature for more consistent responses (except GPT-5)
            )
            # --- END UNIFIED CALL ---

            end_time = time.perf_counter()
            logger.info(f"LLM call took {end_time - start_time:.4f} seconds.")

            response_content = response["choices"][0]["message"]["content"]
            logger.info(f"Raw response content from LLM: {response_content}")

            # Clean the response content - remove extra whitespace between characters
            def clean_text(text):
                if not text:
                    return text
                import re

                # Replace literal \n and normalize whitespace
                cleaned = re.sub(r"\\n\s*", "", text)
                # Normalize all whitespace to single spaces
                cleaned = " ".join(cleaned.split())
                return cleaned.strip()

            # Parse and clean the JSON response
            repair_object = json.loads(response_content)

            # Clean text fields to remove weird spacing
            if "explanation_natural_language" in repair_object:
                repair_object["explanation_natural_language"] = clean_text(
                    repair_object["explanation_natural_language"]
                )
            if "suggestion_natural_language" in repair_object:
                repair_object["suggestion_natural_language"] = clean_text(
                    repair_object["suggestion_natural_language"]
                )

            # Simple validation to ensure the response has the expected keys
            required_keys = [
                "explanation_natural_language",
                "suggestion_natural_language",
                "proposed_repair",
            ]
            if not all(key in repair_object for key in required_keys):
                logger.error(f"LLM response missing required keys: {response_content}")
                return None

            # --- Create and store ExplanationOutput ---
            self.last_explanation_output = ExplanationOutput(
                natural_language_explanation=repair_object[
                    "explanation_natural_language"
                ],
                correction_suggestions=[repair_object["suggestion_natural_language"]],
                violation=violation,
                justification_tree=justification_tree,
                retrieved_context=context,
                provided_by_model=self.model_name,
                proposed_repair_query=repair_object.get("proposed_repair", {}).get(
                    "query"
                ),
            )

            return repair_object

        except Exception as e:
            logger.error(
                f"LiteLLM API error during repair generation: {e}", exc_info=True
            )
            # Generate a fallback repair query
            return self._generate_fallback_repair(
                violation, justification_tree, context, language
            )

    def _generate_fallback_repair(
        self,
        violation: ConstraintViolation,
        justification_tree: JustificationTree,
        context: DomainContext,
        language: str = "en",
    ) -> Optional[Dict]:
        """
        Generate a fallback repair query when LLM fails
        """
        try:
            constraint_component = getattr(violation, "constraint_id", "")
            focus_node = getattr(violation, "focus_node", "")
            property_path = getattr(violation, "property_path", "")
            value = getattr(violation, "value", "")

            # Generate query based on constraint type
            if "MinCountConstraintComponent" in constraint_component:
                # Missing value - generate INSERT with reasonable default
                default_value = self._get_default_value_for_property(
                    property_path, context
                )
                sparql_query = f"""
INSERT DATA {{
  GRAPH <http://ex.org/ValidationReport/Session_UNKNOWN> {{
    <{focus_node}> <{property_path}> {default_value} .
  }}
}}
"""
                explanation = f"This data record is incomplete. The '{property_path}' attribute is required but missing."
                suggestion = f"Add a value for the '{property_path}' attribute to complete the record."

            elif "MaxCountConstraintComponent" in constraint_component:
                # Too many values - generate DELETE
                sparql_query = f"""
DELETE WHERE {{
  GRAPH <http://ex.org/ValidationReport/Session_UNKNOWN> {{
    <{focus_node}> <{property_path}> {value} .
  }}
}}
"""
                explanation = f"This data record has too many values for the '{property_path}' attribute."
                suggestion = f"Remove extra values from the '{property_path}' attribute to comply with the constraint."

            elif "DatatypeConstraintComponent" in constraint_component:
                # Wrong datatype - generate DELETE/INSERT with correct typing
                correct_value = self._fix_datatype_value(value, context)
                sparql_query = f"""
DELETE WHERE {{
  GRAPH <http://ex.org/ValidationReport/Session_UNKNOWN> {{
    <{focus_node}> <{property_path}> {value} .
  }}
}};
INSERT DATA {{
  GRAPH <http://ex.org/ValidationReport/Session_UNKNOWN> {{
    <{focus_node}> <{property_path}> {correct_value} .
  }}
}}
"""
                explanation = f"This data record has an incorrect data type for the '{property_path}' attribute."
                suggestion = (
                    f"Change the value of '{property_path}' to the correct data type."
                )

            else:
                # Generic constraint - provide a template
                sparql_query = f"""
# Modify this query based on the specific constraint requirements
DELETE WHERE {{
  GRAPH <http://ex.org/ValidationReport/Session_UNKNOWN> {{
    <{focus_node}> <{property_path}> {value} .
  }}
}};
INSERT DATA {{
  GRAPH <http://ex.org/ValidationReport/Session_UNKNOWN> {{
    <{focus_node}> <{property_path}> "CORRECTED_VALUE" .
  }}
}}
"""
                explanation = f"The data record violates a constraint on the '{property_path}' attribute."
                suggestion = f"Review and correct the '{property_path}' value according to the constraint requirements."

            # Create ExplanationOutput for storage
            self.last_explanation_output = ExplanationOutput(
                natural_language_explanation=explanation,
                correction_suggestions=[suggestion],
                violation=violation,
                justification_tree=justification_tree,
                retrieved_context=context,
                provided_by_model="fallback_generator",
                proposed_repair_query=sparql_query.strip(),
            )

            return {
                "violation_signature": f"fallback_{constraint_component}_{property_path}",
                "explanation_natural_language": explanation,
                "suggestion_natural_language": suggestion,
                "proposed_repair": {
                    "type": "SPARQL_UPDATE",
                    "query": sparql_query.strip(),
                },
            }

        except Exception as e:
            logger.error(f"Error generating fallback repair: {e}")
            return None

    def _get_default_value_for_property(
        self, property_path: str, context: DomainContext
    ) -> str:
        """
        Generate a sensible default value for a given property
        """
        property_lower = property_path.lower()

        if any(keyword in property_lower for keyword in ["name", "label", "title"]):
            return '"Unknown Name"'
        elif any(keyword in property_lower for keyword in ["email", "mail"]):
            return '"unknown@example.com"'
        elif any(
            keyword in property_lower for keyword in ["date", "created", "modified"]
        ):
            return f"\"{time.strftime('%Y-%m-%d')}\"^^xsd:date"
        elif any(
            keyword in property_lower
            for keyword in ["age", "count", "number", "quantity"]
        ):
            return '"0"^^xsd:integer'
        elif any(
            keyword in property_lower for keyword in ["description", "comment", "text"]
        ):
            return '""'
        elif any(keyword in property_lower for keyword in ["url", "link", "uri"]):
            return '"http://example.org"'
        else:
            return '""'  # Default to empty string

    def _fix_datatype_value(self, value: str, context: DomainContext) -> str:
        """
        Fix a value to have the correct datatype
        """
        # Try to determine if it should be numeric
        try:
            int(value)
            return f'"{value}"^^xsd:integer'
        except ValueError:
            pass

        try:
            float(value)
            return f'"{value}"^^xsd:decimal'
        except ValueError:
            pass

        # Check if it looks like a date
        if any(char in value for char in ["-", "/"]) and len(value) > 8:
            return f'"{value}"^^xsd:date'

        # Default to string
        return f'"{value}"'
