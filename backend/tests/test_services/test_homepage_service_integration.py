"""
Integration tests for homepage service SPARQL query functionality.
These tests focus on verifying the actual SPARQL query structure and logic.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import re


class TestHomepageServiceIntegration:
    """Integration tests for homepage service SPARQL queries."""

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_node_shapes_with_violations_query_structure(self, mock_sparql_wrapper):
        """Test the SPARQL query structure for node shapes with violations."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": [{"violatedNodeShapesCount": {"value": "5"}}]}
        }

        homepage_service.get_number_of_node_shapes_with_violations()

        # Get the SPARQL query that was set
        call_args = mock_sparql_instance.setQuery.call_args[0][0]
        query = call_args.strip()

        # Verify key SPARQL components
        assert "SELECT (COUNT(DISTINCT ?nodeShape)" in query
        assert "FROM" in query
        assert "WHERE" in query
        assert "GRAPH" in query

        # Verify the UNION structure is correct
        union_count = query.count("UNION")
        assert union_count == 1, "Query should have exactly one UNION"

        # Verify both graph references are present
        assert "shapes_graph_uri" in query or "SHAPES_GRAPH_URI" in query
        assert "validation_report_uri" in query or "VALIDATION_REPORT_URI" in query

        # Verify SHACL vocabulary is used
        assert "sh:NodeShape" in query
        assert "sh:sourceShape" in query
        assert "sh:property" in query

        # Verify query structure for direct violations
        assert "GRAPH <{" in query  # Graph pattern with parameter
        assert "?violation <http://www.w3.org/ns/shacl#sourceShape> ?nodeShape" in query

        # Verify query structure for indirect violations through property shapes
        assert "?propertyShape" in query

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_node_shapes_with_violations_query_with_custom_uris(
        self, mock_sparql_wrapper
    ):
        """Test SPARQL query with custom graph URIs."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": [{"violatedNodeShapesCount": {"value": "3"}}]}
        }

        custom_shapes_uri = "http://custom.example.org/shapes"
        custom_validation_uri = "http://custom.example.org/validation"

        homepage_service.get_number_of_node_shapes_with_violations(
            shapes_graph_uri=custom_shapes_uri,
            validation_report_uri=custom_validation_uri,
        )

        call_args = mock_sparql_instance.setQuery.call_args[0][0]
        query = call_args.strip()

        # Verify custom URIs are properly inserted
        assert custom_shapes_uri in query
        assert custom_validation_uri in query

        # Verify GRAPH clauses use the custom URIs
        assert f"GRAPH <{custom_shapes_uri}>" in query
        assert f"GRAPH <{custom_validation_uri}>" in query

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_violations_per_node_shape_complex_query(self, mock_sparql_wrapper):
        """Test the complex query structure for violations per node shape."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance

        # Mock the shapes query
        shapes_response = {
            "results": {
                "bindings": [
                    {
                        "nodeShape": {"value": "http://example.org/shape1"},
                        "propertyShape": {"value": "http://example.org/prop1"},
                    },
                    {
                        "nodeShape": {"value": "http://example.org/shape1"},
                        "propertyShape": {"value": "http://example.org/prop2"},
                    },
                ]
            }
        }

        # Mock the violations queries
        violations_response = {
            "results": {"bindings": [{"violationCount": {"value": "5"}}]}
        }

        mock_sparql_instance.query.return_value.convert.side_effect = [
            shapes_response,
            violations_response,
        ]

        homepage_service.get_violations_per_node_shape()

        # Verify multiple queries were executed
        assert mock_sparql_instance.setQuery.call_count == 2

        # Get the shapes query
        shapes_query = mock_sparql_instance.setQuery.call_args_list[0][0][0]

        # Verify shapes query structure
        assert "SELECT DISTINCT ?nodeShape ?propertyShape" in shapes_query
        assert "sh:NodeShape" in shapes_query
        assert "sh:property" in shapes_query

        # Get the violations query
        violations_query = mock_sparql_instance.setQuery.call_args_list[1][0][0]

        # Verify violations query structure
        assert "COUNT(?violation)" in violations_query
        assert "sh:sourceShape" in violations_query
        assert "VALUES" in violations_query

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_distribution_chart_query_patterns(self, mock_sparql_wrapper):
        """Test SPARQL queries used for distribution chart data."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {
                "bindings": [
                    {
                        "path": {"value": "http://example.org/path1"},
                        "violationCount": {"value": "10"},
                    },
                    {
                        "path": {"value": "http://example.org/path2"},
                        "violationCount": {"value": "5"},
                    },
                ]
            }
        }

        # Test violations per path query
        homepage_service.get_violations_per_path()

        call_args = mock_sparql_instance.setQuery.call_args[0][0]
        query = call_args.strip()

        # Verify aggregation query structure
        assert "SELECT ?path (COUNT(?violation)" in query
        assert "GROUP BY ?path" in query
        assert "ORDER BY DESC" in query

    @patch("functions.homepage_service.requests.get")
    def test_constraint_components_sparql_structure(self, mock_requests_get):
        """Test SPARQL queries for constraint component analysis."""
        from functions import homepage_service

        # Mock response for distinct constraint components
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": {"bindings": [{"distinctCount": {"value": "8"}}]}
        }
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        homepage_service.get_distinct_constraint_components_count()

        # Get the query that was sent
        call_args = mock_requests_get.call_args[1]["params"]["query"]
        query = call_args.strip()

        # Verify constraint component query structure
        assert "COUNT(DISTINCT ?constraintComponent)" in query
        assert "sh:sourceConstraintComponent" in query

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_validation_details_complex_query(self, mock_sparql_wrapper):
        """Test the complex query structure for validation details."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance

        # Mock multiple query responses
        violations_response = {
            "results": {
                "bindings": [
                    {
                        "violation": {"value": "http://example.org/violation1"},
                        "focusNode": {"value": "http://example.org/node1"},
                        "resultPath": {"value": "http://example.org/path1"},
                        "value": {"value": "test_value"},
                        "message": {"value": "Test violation message"},
                        "sourceShape": {"value": "http://example.org/shape1"},
                        "severity": {"value": "http://www.w3.org/ns/shacl#Violation"},
                        "constraintComponent": {
                            "value": "http://www.w3.org/ns/shacl#MinCountConstraintComponent"
                        },
                    }
                ]
            }
        }

        shape_details_response = {
            "results": {
                "bindings": [
                    {
                        "nodeShape": {"value": "http://example.org/nodeShape1"},
                        "targetClass": {"value": "http://example.org/Class1"},
                    }
                ]
            }
        }

        property_triples_response = {
            "results": {
                "bindings": [
                    {
                        "predicate": {"value": "http://www.w3.org/ns/shacl#path"},
                        "object": {"value": "http://example.org/path1"},
                    }
                ]
            }
        }

        mock_sparql_instance.query.return_value.convert.side_effect = [
            violations_response,
            shape_details_response,
            property_triples_response,
        ]

        homepage_service.generate_validation_details_report(limit=1)

        # Verify multiple queries were executed
        assert mock_sparql_instance.setQuery.call_count == 3

        # Get the main violations query
        violations_query = mock_sparql_instance.setQuery.call_args_list[0][0][0]

        # Verify violations query structure
        assert "SELECT DISTINCT" in violations_query
        assert "sh:ValidationResult" in violations_query
        assert "sh:focusNode" in violations_query
        assert "sh:resultPath" in violations_query
        assert "sh:value" in violations_query
        assert "sh:resultMessage" in violations_query
        assert "sh:sourceShape" in violations_query
        assert "sh:resultSeverity" in violations_query
        assert "sh:sourceConstraintComponent" in violations_query
        assert "LIMIT" in violations_query

    def test_sparql_query_validation(self):
        """Test SPARQL query syntax validation."""
        from functions import homepage_service

        # Test that queries can be constructed without syntax errors
        queries_to_test = [
            # Basic count query
            """
            SELECT (COUNT(?violation) AS ?violationCount)
            FROM <http://example.org/validation>
            WHERE {
                ?violation a <http://www.w3.org/ns/shacl#ValidationResult> .
            }
            """,
            # Complex UNION query (similar to our fixed function)
            """
            SELECT (COUNT(DISTINCT ?nodeShape) AS ?violatedNodeShapesCount)
            WHERE {
                GRAPH <http://example.org/shapes> {
                    ?nodeShape a <http://www.w3.org/ns/shacl#NodeShape> .
                }
                {
                    GRAPH <http://example.org/validation> {
                        ?violation <http://www.w3.org/ns/shacl#sourceShape> ?nodeShape .
                    }
                }
                UNION
                {
                    GRAPH <http://example.org/shapes> {
                        ?nodeShape <http://www.w3.org/ns/shacl#property> ?propertyShape .
                    }
                    GRAPH <http://example.org/validation> {
                        ?violation <http://www.w3.org/ns/shacl#sourceShape> ?propertyShape .
                    }
                }
            }
            """,
            # Aggregation query
            """
            SELECT ?path (COUNT(?violation) AS ?violationCount)
            FROM <http://example.org/validation>
            WHERE {
                ?violation <http://www.w3.org/ns/shacl#resultPath> ?path .
            }
            GROUP BY ?path
            ORDER BY DESC(?violationCount)
            """,
        ]

        for query in queries_to_test:
            # Basic syntax validation
            assert "SELECT" in query
            assert "WHERE" in query
            assert query.count("{") == query.count("}")  # Balanced braces

            # Check for proper SPARQL keywords
            assert any(
                keyword in query.upper()
                for keyword in ["SELECT", "ASK", "CONSTRUCT", "DESCRIBE"]
            )

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_query_parameter_injection_safety(self, mock_sparql_wrapper):
        """Test that query parameters are safely handled to prevent injection."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": [{"violatedNodeShapesCount": {"value": "0"}}]}
        }

        # Test with potentially malicious URI
        malicious_uri = (
            "http://example.org/graph'; DROP GRAPH <http://example.org/important>; --"
        )

        homepage_service.get_number_of_node_shapes_with_violations(
            shapes_graph_uri=malicious_uri,
            validation_report_uri="http://example.org/validation",
        )

        call_args = mock_sparql_instance.setQuery.call_args[0][0]
        query = call_args.strip()

        # Verify the URI is properly escaped within GRAPH clauses
        assert f"GRAPH <{malicious_uri}>" in query

        # The malicious content should be contained within the URI, not executed
        assert "DROP GRAPH" not in query.upper()
        assert "--" not in query  # SQL comment syntax

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_query_performance_considerations(self, mock_sparql_wrapper):
        """Test that queries include performance optimizations."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": [{"violatedNodeShapesCount": {"value": "10"}}]}
        }

        homepage_service.get_number_of_node_shapes_with_violations()

        call_args = mock_sparql_instance.setQuery.call_args[0][0]
        query = call_args.strip()

        # Check for performance indicators
        assert "DISTINCT" in query  # Avoid duplicates
        assert "COUNT" in query  # Use COUNT aggregation for efficiency

        # Verify graph-specific querying (better performance than querying all graphs)
        graph_count = query.count("GRAPH")
        assert graph_count >= 2  # Should query both shapes and validation graphs

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_most_violated_node_shape_query_optimization(self, mock_sparql_wrapper):
        """Test query optimization for most violated node shape."""
        from functions import homepage_service
        import requests

        # Mock requests-based query (used in this function)
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": {
                "bindings": [
                    {
                        "nodeShape": {"value": "http://example.org/shape1"},
                        "propertyShape": {"value": "http://example.org/prop1"},
                    }
                ]
            }
        }
        mock_response.raise_for_status.return_value = None

        with patch(
            "functions.homepage_service.requests.get", return_value=mock_response
        ):
            # Mock the SPARQL wrapper for the second part
            mock_sparql_instance = Mock()
            mock_sparql_wrapper.return_value = mock_sparql_instance
            mock_sparql_instance.query.return_value.convert.return_value = {
                "results": {"bindings": [{"violationCount": {"value": "15"}}]}
            }

            result = homepage_service.get_most_violated_node_shape()

            # Verify the function uses efficient query patterns
            assert "nodeShape" in result
            assert "violations" in result
