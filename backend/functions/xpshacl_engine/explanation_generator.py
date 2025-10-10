import os
import json
import logging
from typing import List, Dict, Tuple, Optional
import ollama
import openai
from dotenv import load_dotenv

from rdflib import Graph

from .xpshacl_architecture import (
    ConstraintViolation,
    JustificationTree,
    DomainContext,
    ExplanationOutput,
    ViolationType,
)
from .context_retriever import ContextRetriever
from .extended_shacl_validator import ExtendedShaclValidator
from .justification_tree_builder import JustificationTreeBuilder

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("xpshacl")

# --- LLM Integration for Natural Language Generation ---

explanations_prompt = """INSTRUCTIONS:
Your audience is a business expert, not a technical user. Explain the data quality issue in simple, business-oriented language.
- DO NOT use technical jargon like 'node', 'property', 'literal', 'URI', or 'SHACL'.
- Instead of 'node' or 'focus node', use a general term like 'data record', 'item', or 'entry'. If the type is known (e.g., a 'Person', 'Product'), use that specific term.
- Instead of 'property', use 'attribute', 'field', or 'characteristic'.
- Frame the explanation around the business rule that was violated.
- Be concise and clear. Get straight to the point.

Example:
- INSTEAD OF: 'The focus node violates the MinCountConstraintComponent for the property foaf:name because it has 0 values instead of the required 1.'
- SAY: 'This data record is incomplete. According to our business rules, every person must have a name, but this record is missing one.'

Provide only the explanation, with no introductory phrases.
"""

suggestions_prompt = """INSTRUCTIONS:
Your audience is a business expert. Suggest clear, actionable steps to fix the data quality issue.
- Use simple, non-technical language. Avoid jargon like 'SPARQL', 'SHACL', 'URI', etc.
- The suggestions should describe the business action required to correct the data.
- Focus on fixing the data, not the underlying technical rules. If the rule itself might be wrong, you can gently suggest a review.

Example:
- INSTEAD OF: 'Change the negative value to a positive one for the property ex:age or change the sh:minInclusive rule.'
- SAY: 'Correct the age attribute for this record. The value should be a positive number. If our business rules for age have changed, the data quality standard may need to be updated.'

Provide only the suggested corrections, with no introductory phrases.
"""


class ExplanationGenerator:
    """Generates natural language explanations using an LLM"""

    def __init__(self, model_name: str = "gpt-4o-mini-2024-07-18"):
        self.model_name = model_name
        if "gpt" in model_name:
            openai.api_key = os.getenv("OPENAI_API_KEY")
            openai.base_url = "https://api.openai.com/v1/"
            if not openai.api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set.")
        elif "gemini" in model_name:
            openai.api_key = os.getenv("GEMINI_API_KEY")
            openai.base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
            if not openai.api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set.")
        elif "claude" in model_name:
            openai.api_key = os.getenv("ANTHROPIC_API_KEY")
            openai.base_url = "https://api.anthropic.com/v1/"
            if not openai.api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set.")

    def _generate_explanation_text(
        self,
        violation: ConstraintViolation,
        justification_tree: JustificationTree,
        context: DomainContext,
        language: str = "en",
    ) -> str:
        """
        Internal helper that calls the OpenAI Chat Completion and returns a raw string.
        """
        prompt = f"Explain the following SHACL violation in {language} (ISO 639-1 code): {violation.message or 'Unknown violation'}. "
        prompt += f"Justification: {json.dumps(justification_tree.to_dict(), indent=2, default=str)}. "
        prompt += (
            f"Relevant context: {json.dumps(context.__dict__, indent=2, default=str)}. "
        )
        prompt += explanations_prompt

        try:
            response = openai.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"Error generating explanation in {language}: {e}"

    def _generate_correction_suggestions_text(
        self, violation: ConstraintViolation, context: DomainContext, language: str = "en"
    ) -> str: # Return a single string
        """
        Internal helper that calls the LLM for suggestions and returns
        a single combined string.
        """
        SUGGESTION_SEPARATOR = "\n\n" # Define separator consistently

        prompt = f"Consider the following SHACL violation (context language is {language}, ISO 639-1 code): {violation.message or 'Unknown violation'}.\n"
        prompt += f"Relevant context: {json.dumps(context.__dict__, indent=2, default=str)}.\n\n"
        prompt += f"Provide possible correction suggestions for this violation IN THE LANGUAGE '{language.upper()}' (ISO 639-1 code: {language}). Combine all suggestions into a single response, perhaps using numbered points or distinct paragraphs.\n\n"
        prompt += suggestions_prompt # Append the original detailed instructions

        try:
            response = openai.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            response_content = response.choices[0].message.content.strip()

            # --- Combine into single string ---
            # Although we ask the LLM for a single block, if it happens to use
            # newlines strictly for separation, joining them ensures a single string.
            # If the response is already a single block, split/join won't hurt.
            suggestions_lines = [s.strip() for s in response_content.split('\n') if s.strip()]
            if not suggestions_lines:
                 return "No suggestions generated." # Return empty or placeholder string

            # Join lines using the chosen separator to form the single string
            combined_suggestions = SUGGESTION_SEPARATOR.join(suggestions_lines)
            return combined_suggestions
            # --- End combination ---

        except (openai.APIError, Exception) as e:
            logger.error(f"OpenAI API error during suggestion generation: {e}")
            # Return the error message as a plain string
            return f"Error generating correction suggestions in {language}: {e}"

    def generate_explanation_output(
        self,
        violation: ConstraintViolation,
        justification_tree: JustificationTree,
        context: DomainContext,
        languages: List[str] = ["en"],
    ) -> Dict[str, Tuple[str, str]]:
        """
        Generates a dictionary where keys are language codes and values are
        tuples containing the (natural_language_explanation, combined_correction_suggestions)
        strings for that language.
        """
        output: Dict[str, Tuple[str, str]] = {}

        for lang in languages:
            # Generate text and suggestions for the current language
            explanation_text = self._generate_explanation_text(
                violation, justification_tree, context, lang
            )
            # _generate_correction_suggestions_text and returns a single string
            suggestions_string = self._generate_correction_suggestions_text(
                violation, context, lang
            )

            # Assign the tuple of two strings
            output[lang] = (explanation_text, suggestions_string)

        return output


class ExplainableShaclSystem:
    """Combines all components to provide explainable SHACL validation"""

    def __init__(
        self,
        data_graph: Graph,
        shapes_graph: Graph,
        inference: str = "none",
        model: str = "gpt-4o-mini-2024-07-18",
    ):
        self.validator = ExtendedShaclValidator(shapes_graph, inference)
        self.justification_builder = JustificationTreeBuilder(data_graph, shapes_graph)
        self.context_retriever = ContextRetriever(data_graph, shapes_graph)
        self.explanation_generator = ExplanationGenerator(model_name=model)

    def explain_validation(self, data_graph: Graph) -> List[ExplanationOutput]:
        """Validates a data graph and generates explanations for violations"""
        is_valid, validation_graph, violations = self.validator.validate(data_graph)
        explanations = []

        for violation in violations:
            justification_tree = self.justification_builder.build_tree(violation)
            retrieved_context = self.context_retriever.retrieve_context(violation)
            explanation_text = (
                self.explanation_generator._generate_explanation_text(
                    violation, justification_tree, retrieved_context
                )
            )
            correction_suggestions = (
                self.explanation_generator._generate_correction_suggestions_text(
                    violation, retrieved_context
                )
            )

            explanation_output = ExplanationOutput(
                violation=violation,
                justification_tree=justification_tree,
                retrieved_context=retrieved_context,
                natural_language_explanation=explanation_text,
                correction_suggestions=correction_suggestions,
                provided_by_model=self.explanation_generator.model_name,
            )
            explanations.append(explanation_output)

        return explanations


class LocalExplanationGenerator:
    """Generates natural language explanations using Ollama"""

    def __init__(self, model_name: str = "gemma:2b"):
        self.model_name = model_name

    def generate_explanation_output(
        self,
        violation: ConstraintViolation,
        justification_tree: JustificationTree,
        context: DomainContext,
        languages: List[str] = ["en"],
    ) -> Dict[str, Tuple[str, List[str]]]:
        """Generates natural language explanations for a violation using Ollama for multiple languages"""
        output = {}
        for lang in languages:
            prompt_explanation = f"Explain the following SHACL violation in {lang}: {violation.message or 'Unknown violation'}. "
            prompt_explanation += f"Justification: {json.dumps(justification_tree.to_dict(), indent=2, default=str)}. "
            prompt_explanation += (
                f"Relevant context: {json.dumps(context.__dict__, indent=2, default=str)}. "
            )
            prompt_explanation += explanations_prompt

            response_explanation = ollama.chat(
                model=self.model_name, messages=[{"role": "user", "content": prompt_explanation}]
            )
            explanation_content = response_explanation["message"]["content"].strip()
            if self.model_name == "gemma:2b" and explanation_content.startswith(" "):
                explanation_content = explanation_content[1:]

            prompt_suggestions = f"Given the following SHACL violation in {lang}: {violation.message or 'Unknown violation'}. "
            prompt_suggestions += (
                f"Relevant context: {json.dumps(context.__dict__, indent=2, default=str)}. "
            )
            prompt_suggestions += suggestions_prompt

            response_suggestions = ollama.chat(
                model=self.model_name, messages=[{"role": "user", "content": prompt_suggestions}]
            )
            suggestions_content = [response_suggestions["message"]["content"].strip()]
            if self.model_name == "gemma:2b" and suggestions_content[0].startswith(" "):
                suggestions_content[0] = suggestions_content[0][1:]

            output[lang] = (explanation_content, suggestions_content)
        return output

    def generate_correction_suggestions(
        self, violation: ConstraintViolation, context: DomainContext, language: str = "en"
    ) -> List[str]:
        """Generates correction suggestions for a violation using Ollama for a specific language"""
        prompt = f"Given the following SHACL violation in {language} (ISO 639-1 code): {violation.message or 'Unknown violation'}. "
        prompt += (
            f"Relevant context: {json.dumps(context.__dict__, indent=2, default=str)}. "
        )
        prompt += suggestions_prompt

        response = ollama.chat(
            model=self.model_name, messages=[{"role": "user", "content": prompt}]
        )
        suggestion_content = response["message"]["content"].strip()
        if self.model_name == "gemma:2b" and suggestion_content.startswith(" "):
            suggestion_content = suggestion_content[1:]
        return [suggestion_content]