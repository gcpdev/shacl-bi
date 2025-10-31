"""
Edge case and error handling tests for homepage service.
These tests focus on boundary conditions, error scenarios, and robustness.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json


class TestHomepageServiceEdgeCases:
    """Test edge cases and error handling for homepage service."""

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_zero_violations_handling(self, mock_sparql_wrapper):
        """Test handling when there are no violations."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": [{"violationCount": {"value": "0"}}]}
        }

        result = homepage_service.get_number_of_violations_in_validation_report()

        assert result == 0
        mock_sparql_instance.setQuery.assert_called_once()

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_empty_shapes_graph(self, mock_sparql_wrapper):
        """Test handling when shapes graph is empty."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": [{"nodeShapesCount": {"value": "0"}}]}
        }

        result = homepage_service.get_number_of_node_shapes()

        assert result == 0

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_no_node_shapes_with_violations(self, mock_sparql_wrapper):
        """Test the fixed function when no node shapes have violations."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": [{"violatedNodeShapesCount": {"value": "0"}}]}
        }

        result = homepage_service.get_number_of_node_shapes_with_violations()

        assert result == 0

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_single_violation_handling(self, mock_sparql_wrapper):
        """Test handling when there's exactly one violation."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": [{"violationCount": {"value": "1"}}]}
        }

        result = homepage_service.get_number_of_violations_in_validation_report()

        assert result == 1

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_large_number_handling(self, mock_sparql_wrapper):
        """Test handling of very large violation counts."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": [{"violationCount": {"value": "999999999"}}]}
        }

        result = homepage_service.get_number_of_violations_in_validation_report()

        assert result == 999999999

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_malformed_response_handling(self, mock_sparql_wrapper):
        """Test handling of malformed SPARQL responses."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance

        # Test missing 'results' key - function catches this and raises RuntimeError
        mock_sparql_instance.query.return_value.convert.return_value = {}

        with pytest.raises(RuntimeError, match="Error querying validation report"):
            homepage_service.get_number_of_violations_in_validation_report()

        # Test missing 'bindings' key - function catches this and raises RuntimeError
        mock_sparql_instance.query.return_value.convert.return_value = {"results": {}}

        with pytest.raises(RuntimeError, match="Error querying validation report"):
            homepage_service.get_number_of_violations_in_validation_report()

        # Test empty bindings - function catches this and raises RuntimeError
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": []}
        }

        with pytest.raises(RuntimeError, match="Error querying validation report"):
            homepage_service.get_number_of_violations_in_validation_report()

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_invalid_numeric_response(self, mock_sparql_wrapper):
        """Test handling when response contains non-numeric values."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance

        # Test with string instead of number - function catches this and raises RuntimeError
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": [{"violationCount": {"value": "not_a_number"}}]}
        }

        with pytest.raises(RuntimeError, match="Error querying validation report"):
            homepage_service.get_number_of_violations_in_validation_report()

        # Test with negative number (should be handled gracefully)
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": [{"violationCount": {"value": "-5"}}]}
        }

        result = homepage_service.get_number_of_violations_in_validation_report()
        assert result == -5

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_network_connection_timeout(self, mock_sparql_wrapper):
        """Test handling of network connection timeouts."""
        from functions import homepage_service
        import requests

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance

        # Simulate timeout - function catches this and raises RuntimeError
        mock_sparql_instance.query.side_effect = requests.exceptions.Timeout(
            "Request timed out"
        )

        with pytest.raises(RuntimeError, match="Error querying validation report"):
            homepage_service.get_number_of_violations_in_validation_report()

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_authentication_failure(self, mock_sparql_wrapper):
        """Test handling of authentication failures."""
        from functions import homepage_service
        import requests

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance

        # Simulate authentication error - function catches this and raises RuntimeError
        mock_sparql_instance.query.side_effect = requests.exceptions.HTTPError(
            "401 Unauthorized"
        )

        with pytest.raises(RuntimeError, match="Error querying validation report"):
            homepage_service.get_number_of_violations_in_validation_report()

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_invalid_graph_uri_handling(self, mock_sparql_wrapper):
        """Test handling of invalid graph URIs."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": [{"violatedNodeShapesCount": {"value": "0"}}]}
        }

        # Test with empty URI
        result = homepage_service.get_number_of_node_shapes_with_violations(
            shapes_graph_uri="", validation_report_uri="http://example.org/validation"
        )
        assert result == 0

        # Test with None URI (should use default)
        result = homepage_service.get_number_of_node_shapes_with_violations(
            shapes_graph_uri=None, validation_report_uri="http://example.org/validation"
        )
        assert result == 0

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_unicode_handling_in_responses(self, mock_sparql_wrapper):
        """Test handling of Unicode characters in SPARQL responses."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {
                "bindings": [
                    {
                        "path": {"value": "http://example.org/路径"},
                        "violationCount": {"value": "5"},
                    },
                    {
                        "path": {"value": "http://example.org/путь"},
                        "violationCount": {"value": "3"},
                    },
                ]
            }
        }

        result = homepage_service.get_violations_per_path()

        assert len(result) == 2
        assert result[0]["PathName"] == "http://example.org/路径"
        assert result[1]["PathName"] == "http://example.org/путь"

    @patch("functions.homepage_service.get_violations_per_node_shape")
    def test_empty_distribution_data_handling(self, mock_get_violations):
        """Test distribution calculation with empty violation data."""
        from functions import homepage_service

        # Mock empty violation data - this should raise a ValueError in the function
        mock_get_violations.return_value = []

        with pytest.raises(ValueError, match="max\\(\\) iterable argument is empty"):
            homepage_service.distribution_of_violations_per_shape()

    @patch("functions.homepage_service.get_violations_per_node_shape")
    def test_single_value_distribution_handling(self, mock_get_violations):
        """Test distribution calculation with single violation count."""
        from functions import homepage_service

        # Mock single violation data
        mock_get_violations.return_value = [
            {"NodeShapeName": "shape1", "NumViolations": 5}
        ]

        result = homepage_service.distribution_of_violations_per_shape()

        assert "labels" in result
        assert "datasets" in result
        assert len(result["labels"]) == 10
        assert len(result["datasets"][0]["data"]) == 10

        # One bin should have count 1, others should be 0
        data = result["datasets"][0]["data"]
        assert sum(data) == 1  # Total should be 1
        assert data.count(1) == 1  # Exactly one bin should have count 1
        assert data.count(0) == 9  # Nine bins should be empty

    @patch("functions.homepage_service.get_violations_per_node_shape")
    def test_large_violation_distribution(self, mock_get_violations):
        """Test distribution calculation with very large violation counts."""
        from functions import homepage_service

        # Mock large violation numbers
        mock_get_violations.return_value = [
            {"NodeShapeName": "shape1", "NumViolations": 1000000},
            {"NodeShapeName": "shape2", "NumViolations": 500000},
            {"NodeShapeName": "shape3", "NumViolations": 100},
        ]

        result = homepage_service.distribution_of_violations_per_shape()

        assert "labels" in result
        assert "datasets" in result
        assert len(result["labels"]) == 10

        # Verify data distribution
        data = result["datasets"][0]["data"]
        assert sum(data) == 3  # Three shapes total
        assert all(isinstance(count, int) for count in data)

    @patch("functions.homepage_service.requests.get")
    def test_most_violated_empty_response(self, mock_requests_get):
        """Test most violated functions with empty responses."""
        from functions import homepage_service

        # Test empty response for most violated path
        mock_response = Mock()
        mock_response.json.return_value = {"results": {"bindings": []}}
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        result = homepage_service.get_most_violated_path()

        assert result["path"] is None
        assert result["violations"] == 0

        # Test empty response for most violated focus node
        result = homepage_service.get_most_violated_focus_node()

        assert result["focusNode"] is None
        assert result["violations"] == 0

    @patch("functions.homepage_service.requests.get")
    def test_malformed_json_response(self, mock_requests_get):
        """Test handling of malformed JSON responses."""
        from functions import homepage_service
        import json

        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        with pytest.raises(json.JSONDecodeError):
            homepage_service.get_distinct_constraint_components_count()

    @patch("functions.homepage_service.benchmark_function_execution")
    def test_benchmark_function_with_errors(self, mock_benchmark):
        """Test benchmark function with errors during execution."""
        from functions import homepage_service

        def error_function():
            raise RuntimeError("Test error")

        mock_benchmark.side_effect = RuntimeError("Test error")

        with pytest.raises(RuntimeError):
            homepage_service.benchmark_function_execution(error_function, runs=1)

    def test_benchmark_function_zero_runs(self):
        """Test benchmark function with zero runs."""
        from functions import homepage_service

        def test_function():
            return "test"

        with pytest.raises(ZeroDivisionError):
            homepage_service.benchmark_function_execution(test_function, runs=0)

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_concurrent_query_execution(self, mock_sparql_wrapper):
        """Test behavior when multiple queries might be executed concurrently."""
        from functions import homepage_service
        import threading
        import time

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance
        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": [{"violationCount": {"value": "5"}}]}
        }

        results = []
        errors = []

        def query_function():
            try:
                result = (
                    homepage_service.get_number_of_violations_in_validation_report()
                )
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Run multiple threads
        threads = [threading.Thread(target=query_function) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Verify all threads completed successfully
        assert len(errors) == 0
        assert len(results) == 5
        assert all(result == 5 for result in results)

    @patch("functions.homepage_service.SPARQLWrapper")
    def test_memory_efficiency_with_large_results(self, mock_sparql_wrapper):
        """Test memory handling with large result sets."""
        from functions import homepage_service

        mock_sparql_instance = Mock()
        mock_sparql_wrapper.return_value = mock_sparql_instance

        # Mock large result set
        large_bindings = []
        for i in range(10000):
            large_bindings.append(
                {
                    "path": {"value": f"http://example.org/path{i}"},
                    "violationCount": {"value": str(i)},
                }
            )

        mock_sparql_instance.query.return_value.convert.return_value = {
            "results": {"bindings": large_bindings}
        }

        result = homepage_service.get_violations_per_path()

        # Verify function can handle large result sets
        assert len(result) == 10000
        assert result[0]["NumViolations"] == 0
        assert result[-1]["NumViolations"] == 9999

    def test_default_parameter_validation(self):
        """Test that default parameters are properly validated."""
        from functions import homepage_service
        import inspect

        # Test function signatures
        functions_to_test = [
            "get_number_of_node_shapes_with_violations",
            "get_number_of_node_shapes",
            "get_number_of_paths_in_shapes_graph",
            "get_number_of_paths_with_violations",
            "get_number_of_focus_nodes_in_validation_report",
            "count_triples",
        ]

        for func_name in functions_to_test:
            func = getattr(homepage_service, func_name)
            sig = inspect.signature(func)

            # Verify default parameters exist where expected
            if func_name in ["get_number_of_node_shapes_with_violations"]:
                assert "shapes_graph_uri" in sig.parameters
                assert "validation_report_uri" in sig.parameters
                assert sig.parameters["shapes_graph_uri"].default is not None
                assert sig.parameters["validation_report_uri"].default is not None
