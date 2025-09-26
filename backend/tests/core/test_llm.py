import pytest
from unittest.mock import patch, MagicMock
from backend.core.llm import generate_explanation, generate_severity

@patch('openai.ChatCompletion.create')
def test_generate_explanation(mock_create):
    mock_choice = MagicMock()
    mock_choice.message.content = "This is an explanation."
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_create.return_value = mock_response

    explanation = generate_explanation("violation details")
    assert explanation == "This is an explanation."

@patch('openai.ChatCompletion.create')
def test_generate_severity(mock_create):
    mock_choice = MagicMock()
    mock_choice.message.content = "High"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_create.return_value = mock_response

    severity = generate_severity("violation details")
    assert severity == "High"
