"""
Test homepage service functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timedelta


class TestHomepageService:
    """Test homepage service for main dashboard functionality."""

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_get_number_of_violations_in_validation_report(self, mock_sparql_wrapper):
        """Test getting the total number of violations in validation report."""
        from functions import homepage_service

        # Mock SPARQL response
        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": [{"violationCount": {"value": "150"}}]}
        }

        result = homepage_service.get_number_of_violations_in_validation_report()

        # Verify SPARQL was configured correctly
        mock_sparql_instance.setQuery.assert_called_once()
        mock_sparql_instance.setReturnFormat.assert_called_once()

        assert result == 150

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_get_number_of_node_shapes(self, mock_sparql_wrapper):
        """Test getting the number of node shapes in shapes graph."""
        from functions import homepage_service

        # Mock SPARQL response
        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": [{"nodeShapesCount": {"value": "25"}}]}
        }

        result = homepage_service.get_number_of_node_shapes()

        mock_sparql_instance.setQuery.assert_called_once()
        mock_sparql_instance.setReturnFormat.assert_called_once()

        assert result == 25

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_get_number_of_node_shapes_with_violations(self, mock_sparql_wrapper):
        """Test getting the number of node shapes with violations - the fixed function."""
        from functions import homepage_service

        # Mock SPARQL response
        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": [{"violatedNodeShapesCount": {"value": "12"}}]}
        }

        result = homepage_service.get_number_of_node_shapes_with_violations()

        # Verify the SPARQL query structure
        call_args = mock_sparql_instance.setQuery.call_args[0][0]

        # Check that the query contains the correct structure
        assert "COUNT(DISTINCT ?nodeShape)" in call_args
        assert "GRAPH" in call_args
        assert "UNION" in call_args
        assert "http://www.w3.org/ns/shacl#NodeShape" in call_args
        assert "http://www.w3.org/ns/shacl#sourceShape" in call_args

        assert result == 12

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_get_number_of_node_shapes_with_violations_custom_uris(
        self, mock_sparql_wrapper
    ):
        """Test getting node shapes with violations using custom graph URIs."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": [{"violatedNodeShapesCount": {"value": "8"}}]}
        }

        custom_shapes_uri = "http://custom.example.org/shapes"
        custom_validation_uri = "http://custom.example.org/validation"

        result = homepage_service.get_number_of_node_shapes_with_violations(
            shapes_graph_uri=custom_shapes_uri,
            validation_report_uri=custom_validation_uri,
        )

        call_args = mock_sparql_instance.setQuery.call_args[0][0]
        assert custom_shapes_uri in call_args
        assert custom_validation_uri in call_args

        assert result == 8

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_get_number_of_paths_in_shapes_graph(self, mock_sparql_wrapper):
        """Test getting the number of unique paths in shapes graph."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": [{"pathCount": {"value": "45"}}]}
        }

        result = homepage_service.get_number_of_paths_in_shapes_graph()

        mock_sparql_instance.setQuery.assert_called_once()
        assert result == 45

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_get_number_of_paths_with_violations(self, mock_sparql_wrapper):
        """Test getting the number of paths with violations."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": [{"pathCount": {"value": "32"}}]}
        }

        result = homepage_service.get_number_of_paths_with_violations()

        mock_sparql_instance.setQuery.assert_called_once()
        assert result == 32

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_get_number_of_focus_nodes_in_validation_report(self, mock_sparql_wrapper):
        """Test getting the number of unique focus nodes in validation report."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": [{"focusNodeCount": {"value": "67"}}]}
        }

        result = homepage_service.get_number_of_focus_nodes_in_validation_report()

        mock_sparql_instance.setQuery.assert_called_once()
        assert result == 67

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_count_triples(self, mock_sparql_wrapper):
        """Test counting triples in validation report."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": [{"tripleCount": {"value": "1234"}}]}
        }

        result = homepage_service.count_triples()

        mock_sparql_instance.setQuery.assert_called_once()
        assert result == 1234

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_get_violations_per_node_shape(self, mock_sparql_wrapper):
        """Test getting violations per node shape."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance

        # Mock shapes graph query
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
                    {
                        "nodeShape": {"value": "http://example.org/shape2"},
                        "propertyShape": {"value": "http://example.org/prop3"},
                    },
                ]
            }
        }

        # Mock validation report queries
        validation_response = {
            "results": {"bindings": [{"violationCount": {"value": "10"}}]}
        }

        mock_sparql_instance.query.return_value.convert.side_effect = [
            shapes_response,  # First call for shapes
            validation_response,  # Second call for shape1 violations
            validation_response,  # Third call for shape2 violations
        ]

        result = homepage_service.get_violations_per_node_shape()

        assert len(result) == 2  # Two node shapes
        assert result[0]["NodeShapeName"] == "http://example.org/shape1"
        assert result[0]["NumViolations"] == 10

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_get_violations_per_path(self, mock_sparql_wrapper):
        """Test getting violations per path."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {
                "bindings": [
                    {
                        "path": {"value": "http://example.org/path1"},
                        "violationCount": {"value": "15"},
                    },
                    {
                        "path": {"value": "http://example.org/path2"},
                        "violationCount": {"value": "8"},
                    },
                    {
                        "path": {"value": "http://example.org/path3"},
                        "violationCount": {"value": "3"},
                    },
                ]
            }
        }

        result = homepage_service.get_violations_per_path()

        assert len(result) == 3
        assert result[0]["PathName"] == "http://example.org/path1"
        assert result[0]["NumViolations"] == 15

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_get_violations_per_focus_node(self, mock_sparql_wrapper):
        """Test getting violations per focus node."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {
                "bindings": [
                    {
                        "focusNode": {"value": "http://example.org/node1"},
                        "violationCount": {"value": "12"},
                    },
                    {
                        "focusNode": {"value": "http://example.org/node2"},
                        "violationCount": {"value": "6"},
                    },
                ]
            }
        }

        result = homepage_service.get_violations_per_focus_node()

        assert len(result) == 2
        assert result[0]["FocusNodeName"] == "http://example.org/node1"
        assert result[0]["NumViolations"] == 12

    @patch("functions.homepage_service.get_violations_per_node_shape")
    def test_distribution_of_violations_per_shape(self, mock_get_violations):
        """Test distribution of violations per shape for chart data."""
        from functions import homepage_service

        # Mock violation data
        mock_violations_data = [
            {"NodeShapeName": "shape1", "NumViolations": 5},
            {"NodeShapeName": "shape2", "NumViolations": 15},
            {"NodeShapeName": "shape3", "NumViolations": 25},
            {"NodeShapeName": "shape4", "NumViolations": 35},
        ]
        mock_get_violations.return_value = mock_violations_data

        result = homepage_service.distribution_of_violations_per_shape()

        assert "labels" in result
        assert "datasets" in result
        assert len(result["labels"]) == 10  # Default 10 bins
        assert len(result["datasets"][0]["data"]) == 10
        assert result["datasets"][0]["label"] == "Frequency"

    @patch("functions.homepage_service.requests.get")
    def test_get_most_violated_node_shape(self, mock_requests_get):
        """Test finding the most violated node shape."""
        from functions import homepage_service

        # Mock shapes query response
        shapes_response = Mock()
        shapes_response.json.return_value = {
            "results": {
                "bindings": [
                    {
                        "nodeShape": {"value": "http://example.org/shape1"},
                        "propertyShape": {"value": "http://example.org/prop1"},
                    },
                    {
                        "nodeShape": {"value": "http://example.org/shape2"},
                        "propertyShape": {"value": "http://example.org/prop2"},
                    },
                ]
            }
        }
        shapes_response.raise_for_status.return_value = None

        # Mock violations query response
        violations_response = Mock()
        violations_response.json.return_value = {
            "results": {"bindings": [{"violationCount": {"value": "20"}}]}
        }
        violations_response.raise_for_status.return_value = None

        mock_requests_get.side_effect = [
            shapes_response,
            violations_response,
            violations_response,
        ]

        result = homepage_service.get_most_violated_node_shape()

        assert "nodeShape" in result
        assert "violations" in result
        assert result["violations"] == 20

    @patch("functions.homepage_service.requests.get")
    def test_get_most_violated_path(self, mock_requests_get):
        """Test finding the most violated path."""
        from functions import homepage_service

        mock_response = Mock()
        mock_response.json.return_value = {
            "results": {
                "bindings": [
                    {
                        "path": {"value": "http://example.org/mostViolatedPath"},
                        "violationCount": {"value": "50"},
                    }
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        result = homepage_service.get_most_violated_path()

        assert result["path"] == "http://example.org/mostViolatedPath"
        assert result["violations"] == 50

    @patch("functions.homepage_service.requests.get")
    def test_get_most_violated_focus_node(self, mock_requests_get):
        """Test finding the most violated focus node."""
        from functions import homepage_service

        mock_response = Mock()
        mock_response.json.return_value = {
            "results": {
                "bindings": [
                    {
                        "focusNode": {"value": "http://example.org/mostViolatedNode"},
                        "violationCount": {"value": "30"},
                    }
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        result = homepage_service.get_most_violated_focus_node()

        assert result["focusNode"] == "http://example.org/mostViolatedNode"
        assert result["violations"] == 30

    @patch("functions.homepage_service.requests.get")
    def test_get_most_frequent_constraint_component(self, mock_requests_get):
        """Test finding the most frequent constraint component."""
        from functions import homepage_service

        mock_response = Mock()
        mock_response.json.return_value = {
            "results": {
                "bindings": [
                    {
                        "constraintComponent": {
                            "value": "http://www.w3.org/ns/shacl#MinCountConstraintComponent"
                        },
                        "occurrenceCount": {"value": "25"},
                    }
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        result = homepage_service.get_most_frequent_constraint_component()

        assert (
            result["constraintComponent"]
            == "http://www.w3.org/ns/shacl#MinCountConstraintComponent"
        )
        assert result["occurrences"] == 25

    @patch("functions.homepage_service.requests.get")
    def test_get_distinct_constraint_components_count(self, mock_requests_get):
        """Test counting distinct constraint components."""
        from functions import homepage_service

        mock_response = Mock()
        mock_response.json.return_value = {
            "results": {"bindings": [{"distinctCount": {"value": "8"}}]}
        }
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        result = homepage_service.get_distinct_constraint_components_count()

        assert result == 8

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_error_handling_query_failure(self, mock_sparql_wrapper):
        """Test error handling when SPARQL query fails."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.side_effect = Exception("SPARQL endpoint error")

        with pytest.raises(RuntimeError, match="Error querying validation report"):
            homepage_service.get_number_of_violations_in_validation_report()

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_empty_results_handling(self, mock_sparql_wrapper):
        """Test handling of empty query results."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": []}
        }

        # The function catches exceptions and re-raises them as RuntimeError
        with pytest.raises(RuntimeError, match="Error querying validation report"):
            homepage_service.get_number_of_violations_in_validation_report()

    @patch("functions.homepage_service.requests.get")
    def test_get_distinct_constraints_count_in_shapes(self, mock_requests_get):
        """Test counting distinct constraints in shapes graph."""
        from functions import homepage_service

        mock_response = Mock()
        mock_response.json.return_value = {
            "results": {"bindings": [{"distinctCount": {"value": "12"}}]}
        }
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        result = homepage_service.get_distinct_constraints_count_in_shapes()

        assert result == 12

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_benchmark_function_execution(self, mock_sparql_wrapper):
        """Test benchmark function execution timing."""
        from functions import homepage_service
        import time

        # Mock a simple function to benchmark
        def mock_function():
            time.sleep(0.001)  # 1ms delay
            return "test_result"

        # Mock SPARQL for the function that gets benchmarked
        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": [{"count": {"value": "5"}}]}
        }

        # Test the benchmark function
        result = homepage_service.benchmark_function_execution(
            mock_function, runs=3, csv_filename="test_benchmark.csv"
        )

        assert "times_ms" in result
        assert "average_ms" in result
        assert "results" in result
        assert len(result["times_ms"]) == 3
        assert all(r == "test_result" for r in result["results"])

        # Clean up test file
        import os

        if os.path.exists("test_benchmark.csv"):
            os.remove("test_benchmark.csv")
