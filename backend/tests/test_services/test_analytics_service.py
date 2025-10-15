"""
Test analytics service functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timedelta

class TestAnalyticsService:
    """Test analytics service for data visualization."""

    @patch('functions.analytics_service.virtuoso_service')
    def test_get_violation_statistics(self, mock_virtuoso):
        """Test getting violation statistics."""
        from functions import analytics_service

        # Mock query results
        mock_virtuoso.execute_sparql_query.return_value = {
            "results": {
                "bindings": [
                    {"constraintType": {"value": "MinCountConstraintComponent"}, "count": {"value": "15"}},
                    {"constraintType": {"value": "MaxCountConstraintComponent"}, "count": {"value": "8"}},
                    {"constraintType": {"value": "PatternConstraintComponent"}, "count": {"value": "12"}}
                ]
            }
        }

        stats = analytics_service.get_violation_statistics("session_123")
        assert len(stats) == 3
        assert stats[0]['constraintType'] == 'MinCountConstraintComponent'
        assert stats[0]['count'] == 15

    @patch('functions.analytics_service.virtuoso_service')
    def test_get_property_distribution(self, mock_virtuoso):
        """Test getting property distribution analysis."""
        from functions import analytics_service

        mock_virtuoso.execute_sparql_query.return_value = {
            "results": {
                "bindings": [
                    {"property": {"value": "http://example.org/ns#name"}, "violationCount": {"value": "5"}},
                    {"property": {"value": "http://example.org/ns#email"}, "violationCount": {"value": "3"}}
                ]
            }
        }

        distribution = analytics_service.get_property_distribution("session_123")
        assert len(distribution) == 2
        assert distribution[0]['property'] == 'http://example.org/ns#name'
        assert distribution[0]['violationCount'] == 5

    @patch('functions.analytics_service.virtuoso_service')
    def test_get_severity_analysis(self, mock_virtuoso):
        """Test getting severity analysis."""
        from functions import analytics_service

        mock_virtuoso.execute_sparql_query.return_value = {
            "results": {
                "bindings": [
                    {"severity": {"value": "http://www.w3.org/ns/shacl#Violation"}, "count": {"value": "25"}},
                    {"severity": {"value": "http://www.w3.org/ns/shacl#Warning"}, "count": {"value": "10"}}
                ]
            }
        }

        severity = analytics_service.get_severity_analysis("session_123")
        assert len(severity) == 2
        assert severity[0]['severity'] == 'http://www.w3.org/ns/shacl#Violation'
        assert severity[0]['count'] == 25

    @patch('functions.analytics_service.virtuoso_service')
    def test_get_temporal_trends(self, mock_virtuoso):
        """Test getting temporal violation trends."""
        from functions import analytics_service

        mock_virtuoso.execute_sparql_query.return_value = {
            "results": {
                "bindings": [
                    {"date": {"value": "2023-01-01"}, "count": {"value": "5"}},
                    {"date": {"value": "2023-01-02"}, "count": {"value": "8"}},
                    {"date": {"value": "2023-01-03"}, "count": {"value": "3"}}
                ]
            }
        }

        trends = analytics_service.get_temporal_trends("session_123", days=7)
        assert len(trends) == 3
        assert trends[0]['date'] == '2023-01-01'
        assert trends[0]['count'] == 5

    @patch('functions.analytics_service.virtuoso_service')
    def test_get_shape_complexity_metrics(self, mock_virtuoso):
        """Test getting shape complexity metrics."""
        from functions import analytics_service

        mock_virtuoso.execute_sparql_query.return_value = {
            "results": {
                "bindings": [
                    {"shape": {"value": "http://example.org/shapes/PersonShape"}, "constraintCount": {"value": "4"}},
                    {"shape": {"value": "http://example.org/shapes/OrganizationShape"}, "constraintCount": {"value": "2"}}
                ]
            }
        }

        metrics = analytics_service.get_shape_complexity_metrics()
        assert len(metrics) == 2
        assert metrics[0]['shape'] == 'http://example.org/shapes/PersonShape'
        assert metrics[0]['constraintCount'] == 4

    @patch('functions.analytics_service.virtuoso_service')
    def test_get_focus_node_analysis(self, mock_virtuoso):
        """Test getting focus node violation analysis."""
        from functions import analytics_service

        mock_virtuoso.execute_sparql_query.return_value = {
            "results": {
                "bindings": [
                    {"focusNode": {"value": "http://example.org/person1"}, "violationCount": {"value": "3"}},
                    {"focusNode": {"value": "http://example.org/person2"}, "violationCount": {"value": "2"}}
                ]
            }
        }

        analysis = analytics_service.get_focus_node_analysis("session_123")
        assert len(analysis) == 2
        assert analysis[0]['focusNode'] == 'http://example.org/person1'
        assert analysis[0]['violationCount'] == 3

    @patch('functions.analytics_service.virtuoso_service')
    def test_get_repair_success_rate(self, mock_virtuoso):
        """Test getting repair success rate analytics."""
        from functions import analytics_service

        mock_virtuoso.execute_sparql_query.return_value = {
            "results": {
                "bindings": [
                    {"constraintType": {"value": "MinCountConstraintComponent"}, "attempted": {"value": "10"}, "successful": {"value": "8"}},
                    {"constraintType": {"value": "PatternConstraintComponent"}, "attempted": {"value": "5"}, "successful": {"value": "4"}}
                ]
            }
        }

        success_rates = analytics_service.get_repair_success_rate("session_123")
        assert len(success_rates) == 2
        assert success_rates[0]['constraintType'] == 'MinCountConstraintComponent'
        assert success_rates[0]['attempted'] == 10
        assert success_rates[0]['successful'] == 8
        assert success_rates[0]['successRate'] == 0.8

    @patch('functions.analytics_service.virtuoso_service')
    def test_get_data_quality_score(self, mock_virtuoso):
        """Test getting overall data quality score."""
        from functions import analytics_service

        mock_virtuoso.execute_sparql_query.return_value = {
            "results": {
                "bindings": [
                    {"totalTriples": {"value": "1000"}, "violations": {"value": "50"}, "warnings": {"value": "20"}}
                ]
            }
        }

        quality_score = analytics_service.get_data_quality_score("session_123")
        assert 'totalTriples' in quality_score
        assert 'violations' in quality_score
        assert 'qualityScore' in quality_score
        assert quality_score['qualityScore'] >= 0 and quality_score['qualityScore'] <= 100

    @patch('functions.analytics_service.virtuoso_service')
    def test_get_constraint_correlation_matrix(self, mock_virtuoso):
        """Test getting constraint correlation matrix."""
        from functions import analytics_service

        mock_virtuoso.execute_sparql_query.return_value = {
            "results": {
                "bindings": [
                    {"constraint1": {"value": "MinCountConstraintComponent"}, "constraint2": {"value": "MaxCountConstraintComponent"}, "correlation": {"value": "0.3"}},
                    {"constraint1": {"value": "MinCountConstraintComponent"}, "constraint2": {"value": "PatternConstraintComponent"}, "correlation": {"value": "0.1"}}
                ]
            }
        }

        matrix = analytics_service.get_constraint_correlation_matrix("session_123")
        assert len(matrix) == 2
        assert matrix[0]['constraint1'] == 'MinCountConstraintComponent'
        assert float(matrix[0]['correlation']) >= -1 and float(matrix[0]['correlation']) <= 1

    def test_calculate_quality_metrics(self):
        """Test quality metrics calculation."""
        from functions import analytics_service

        test_data = {
            'total_violations': 50,
            'total_warnings': 20,
            'total_items': 1000,
            'repairs_attempted': 30,
            'repairs_successful': 25
        }

        metrics = analytics_service.calculate_quality_metrics(test_data)
        assert 'violation_rate' in metrics
        assert 'warning_rate' in metrics
        assert 'repair_success_rate' in metrics
        assert 'overall_score' in metrics

        # Verify calculations
        assert metrics['violation_rate'] == 0.05  # 50/1000
        assert metrics['warning_rate'] == 0.02   # 20/1000
        assert round(metrics['repair_success_rate'], 3) == 0.833  # 25/30

    @patch('functions.analytics_service.virtuoso_service')
    def test_get_session_comparison(self, mock_virtuoso):
        """Test comparing multiple sessions."""
        from functions import analytics_service

        mock_virtuoso.execute_sparql_query.return_value = {
            "results": {
                "bindings": [
                    {"sessionId": {"value": "session_1"}, "violationCount": {"value": "10"}, "qualityScore": {"value": "85.5"}},
                    {"sessionId": {"value": "session_2"}, "violationCount": {"value": "15"}, "qualityScore": {"value": "78.2"}}
                ]
            }
        }

        comparison = analytics_service.get_session_comparison(["session_1", "session_2"])
        assert len(comparison) == 2
        assert comparison[0]['sessionId'] == 'session_1'
        assert comparison[0]['violationCount'] == 10

    @patch('functions.analytics_service.virtuoso_service')
    def test_get_top_violating_resources(self, mock_virtuoso):
        """Test getting top violating resources."""
        from functions import analytics_service

        mock_virtuoso.execute_sparql_query.return_value = {
            'results': {
                'bindings': [
                    {'focusNode': {'value': 'http://example.org/person1'}, 'violationCount': {'value': '5'}},
                    {'focusNode': {'value': 'http://example.org/person2'}, 'violationCount': {'value': '3'}}
                ]
            }
        }

        top_resources = analytics_service.get_top_violating_resources("session_123", limit=10)
        assert len(top_resources) == 2
        assert top_resources[0]['resource'] == 'http://example.org/person1'
        assert top_resources[0]['violationCount'] == 5

    @patch('functions.analytics_service.virtuoso_service')
    def test_get_validation_performance_metrics(self, mock_virtuoso):
        """Test getting validation performance metrics."""
        from functions import analytics_service

        mock_virtuoso.execute_sparql_query.return_value = {
            "results": {
                "bindings": [
                    {"validationId": {"value": "val_1"}, "duration": {"value": "1250"}, "triplesValidated": {"value": "500"}},
                    {"validationId": {"value": "val_2"}, "duration": {"value": "2100"}, "triplesValidated": {"value": "800"}}
                ]
            }
        }

        metrics = analytics_service.get_validation_performance_metrics()
        assert len(metrics) == 2
        assert metrics[0]['validationId'] == 'val_1'
        assert metrics[0]['duration'] == 1250
        assert metrics[0]['throughput'] == 500 / 1.25  # triples per second

    def test_format_analytics_response(self):
        """Test formatting analytics response."""
        from functions import analytics_service

        raw_data = [
            {"constraintType": {"value": "MinCountConstraintComponent"}, "count": {"value": "15"}}
        ]

        formatted = analytics_service.format_analytics_response(raw_data)
        assert isinstance(formatted, list)
        assert len(formatted) == 1
        assert formatted[0]['constraintType'] == 'MinCountConstraintComponent'
        assert formatted[0]['count'] == 15
        assert isinstance(formatted[0]['count'], int)

    def test_calculate_trend_direction(self):
        """Test calculating trend direction."""
        from functions import analytics_service

        # Test increasing trend
        increasing_data = [1, 2, 3, 4, 5]
        assert analytics_service.calculate_trend_direction(increasing_data) == 'increasing'

        # Test decreasing trend
        decreasing_data = [5, 4, 3, 2, 1]
        assert analytics_service.calculate_trend_direction(decreasing_data) == 'decreasing'

        # Test stable trend
        stable_data = [3, 3, 3, 3, 3]
        assert analytics_service.calculate_trend_direction(stable_data) == 'stable'

        # Test insufficient data
        short_data = [1, 2]
        assert analytics_service.calculate_trend_direction(short_data) == 'insufficient_data'

    @patch('functions.analytics_service.virtuoso_service')
    def test_get_recommendations(self, mock_virtuoso):
        """Test getting improvement recommendations."""
        from functions import analytics_service

        mock_virtuoso.execute_sparql_query.return_value = {
            "results": {
                "bindings": [
                    {"constraintType": {"value": "PatternConstraintComponent"}, "count": {"value": "25"}},
                    {"constraintType": {"value": "MinCountConstraintComponent"}, "count": {"value": "15"}}
                ]
            }
        }

        recommendations = analytics_service.get_improvement_recommendations("session_123")
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all('constraintType' in rec for rec in recommendations)
        assert all('recommendation' in rec for rec in recommendations)