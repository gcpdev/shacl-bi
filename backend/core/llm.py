import openai
from . import config

openai.api_key = config.OPENAI_API_KEY

def generate_explanation(violation_details):
    """Generates an explanation for a SHACL violation using an LLM."""
    try:
        prompt = f"""Explain the following SHACL violation in simple terms:

{violation_details}

Explanation:"""

        response = openai.ChatCompletion.create(
            model=config.DEFAULT_AI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that explains SHACL violations."},
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating explanation: {e}")
        return "Could not generate explanation."

def generate_severity(violation_details):
    """Generates a severity level for a SHACL violation using an LLM."""
    try:
        prompt = f"""Based on the following SHACL violation, assign a severity level (High, Medium, or Low):

{violation_details}

Severity:"""

        response = openai.ChatCompletion.create(
            model=config.DEFAULT_AI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that assigns severity levels to SHACL violations."},
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating severity: {e}")
        return "Medium"
