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
REPAIR_SYSTEM_PROMPT = '''You are an expert data quality analyst who helps business users understand and fix data issues. Your primary goal is to translate complex technical validation results into simple, business-oriented explanations and actionable suggestions. You will also generate the technical code needed to fix the issue.

You will be given a technical description of a data quality violation. Your task is to return a single, valid JSON object with the following structure.

**IMPORTANT:** The `explanation_natural_language` and `suggestion_natural_language` fields MUST be written for a non-technical business audience.
- DO NOT use technical jargon like 'node', 'property', 'literal', 'URI', 'SHACL', or 'SPARQL' in these fields.
- For `explanation_natural_language`: Frame the explanation around the business rule that was violated. Instead of 'node', use 'data record' or 'item'. Instead of 'property', use 'attribute' or 'field'.
    - Example: 'This data record is incomplete. Business rules require that every person must have a name, but this record is missing one.'
- For `suggestion_natural_language`: Suggest the clear, business action required to correct the data.
    - Example: 'Provide the missing name for this person\'s record.'

The `proposed_repair` field is for the system and MUST contain a technically correct SPARQL query.
- Based on the violation\'s 'sourceConstraintComponent', generate the correct type of SPARQL query:
    - 'MinCountConstraintComponent' (missing a value) -> SPARQL INSERT query.
    - 'MaxCountConstraintComponent' (has too many values) -> SPARQL DELETE query.
    - 'DatatypeConstraintComponent' (value has wrong datatype) -> SPARQL DELETE/INSERT query. For this, the INSERT clause MUST explicitly type the new value using the correct datatype from the violation context (e.g., `"42"^^xsd:integer`).
- For MinCount, use the placeholder `$user_provided_value` WITHOUT quotes. For MaxCount or Datatype, use the actual violating value from the input in the DELETE clause.

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
'''

class SuggestionRepairGenerator:
    """
    Generates a structured repair object, including a formal SPARQL query, using an LLM.
    This is the core of the PHOENIX framework's "actionability" feature.
    """

    def __init__(self, vkg: ViolationKnowledgeGraph, model_name: str = config.SRG_MODEL):
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
            
            accepted_queries = [f"- This query was previously accepted by a user:\n{item['query']}" for item in feedback if item['action'] == 'AcceptFix']
            rejected_queries = [f"- This query was previously rejected by a user:\n{item['query']}" for item in feedback if item['action'] == 'RejectFix']

            if accepted_queries:
                feedback_summary += "\nPreviously Accepted Solutions:\n" + "\n".join(accepted_queries)
            if rejected_queries:
                feedback_summary += "\nPreviously Rejected Solutions:\n" + "\n".join(rejected_queries)
            
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
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,  # Lower temperature for more consistent responses (except GPT-5)
            )
            # --- END UNIFIED CALL ---

            end_time = time.perf_counter()
            logger.info(f"LLM call took {end_time - start_time:.4f} seconds.")

            response_content = response['choices'][0]['message']['content']
            logger.info(f"Raw response content from LLM: {response_content}")

            # Clean the response content - remove extra whitespace between characters
            def clean_text(text):
                if not text:
                    return text
                import re
                # Replace literal \n and normalize whitespace
                cleaned = re.sub(r'\\n\s*', '', text)
                # Normalize all whitespace to single spaces
                cleaned = ' '.join(cleaned.split())
                return cleaned.strip()

            # Parse and clean the JSON response
            repair_object = json.loads(response_content)

            # Clean text fields to remove weird spacing
            if 'explanation_natural_language' in repair_object:
                repair_object['explanation_natural_language'] = clean_text(repair_object['explanation_natural_language'])
            if 'suggestion_natural_language' in repair_object:
                repair_object['suggestion_natural_language'] = clean_text(repair_object['suggestion_natural_language'])
            
            # Simple validation to ensure the response has the expected keys
            required_keys = ["explanation_natural_language", "suggestion_natural_language", "proposed_repair"]
            if not all(key in repair_object for key in required_keys):
                logger.error(f"LLM response missing required keys: {response_content}")
                return None
            
            # --- Create and store ExplanationOutput ---
            self.last_explanation_output = ExplanationOutput(
                natural_language_explanation=repair_object["explanation_natural_language"],
                correction_suggestions=[repair_object["suggestion_natural_language"]],
                violation=violation,
                justification_tree=justification_tree,
                retrieved_context=context,
                provided_by_model=self.model_name,
                proposed_repair_query=repair_object.get("proposed_repair", {}).get("query")
            )
            
            return repair_object

        except Exception as e:
            logger.error(f"LiteLLM API error during repair generation: {e}", exc_info=True)
            return None
