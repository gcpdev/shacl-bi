import pytest
from unittest.mock import patch, MagicMock
from backend.core.database import get_db, execute_query, load_ontology, insert_validation_report, create_violation_instances, get_violation_by_id, get_violations_count, get_all_violations

@patch('backend.core.database.SPARQLWrapper')
def test_get_db(mock_sparql_wrapper):
    get_db()
    mock_sparql_wrapper.assert_called_once()

@patch('backend.core.database.get_db')
def test_execute_query(mock_get_db):
    mock_sparql = MagicMock()
    mock_get_db.return_value = mock_sparql
    execute_query("SELECT * WHERE {?s ?p ?o}")
    mock_sparql.setQuery.assert_called_once_with("SELECT * WHERE {?s ?p ?o}")
    mock_sparql.query.assert_called_once()

@patch('builtins.open', new_callable=MagicMock)
@patch('backend.core.database.execute_query')
def test_load_ontology(mock_execute_query, mock_open):
    load_ontology("ontology.ttl", "http://example.com/graph")
    mock_open.assert_called_once_with("ontology.ttl", "r")
    mock_execute_query.assert_called_once()

@patch('backend.core.database.execute_query')
def test_insert_validation_report(mock_execute_query):
    mock_graph = MagicMock()
    mock_graph.serialize.return_value = "report_data"
    insert_validation_report(mock_graph, "http://example.com/graph")
    mock_execute_query.assert_called_once()

@patch('backend.core.database.execute_query')
@patch('backend.core.llm.generate_severity')
def test_create_violation_instances(mock_generate_severity, mock_execute_query):
    mock_execute_query.return_value = {
        'results': {
            'bindings': [
                {
                    'validationResult': {'value': 'http://example.com/vr1'}
                }
            ]
        }
    }
    mock_generate_severity.return_value = "High"
    create_violation_instances("http://example.com/val-graph", "http://example.com/vio-graph")
    assert mock_execute_query.call_count == 2

@patch('backend.core.database.execute_query')
def test_get_violation_by_id(mock_execute_query):
    mock_execute_query.return_value = {
        'results': {
            'bindings': [
                {
                    'p': {'value': 'http://ex.com/p1'},
                    'o': {'value': 'o1'}
                }
            ]
        }
    }
    get_violation_by_id("123", "http://example.com/vio-graph")
    mock_execute_query.assert_called_once()

@patch('backend.core.database.execute_query')
def test_get_violations_count(mock_execute_query):
    mock_execute_query.return_value = {
        'results': {
            'bindings': [
                {
                    'count': {'value': '5'}
                }
            ]
        }
    }
    count = get_violations_count("http://example.com/vio-graph")
    assert count == 5

@patch('backend.core.database.execute_query')
def test_get_all_violations(mock_execute_query):
    mock_execute_query.return_value = {
        'results': {
            'bindings': [
                {
                    'violation': {'value': 'http://ex.com/v1'},
                    'severity': {'value': 'High'}
                }
            ]
        }
    }
    violations = get_all_violations("http://example.com/vio-graph")
    assert len(violations) == 1
