"""
Test dashboard service functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timedelta

class TestDashboardService:
    """Test dashboard service for main dashboard functionality."""

    @patch('functions.dashboard_service.virtuoso_service')
    def test_get_dashboard_summary(self, mock_virtuoso):
        """Test getting dashboard summary statistics."""
        from functions import dashboard_service

        mock_virtuoso.execute_sparql_query.return_value = {
            "results": {
                "bindings": [
                    {"metric": {"value": "totalSessions"}, "count": {"value": "25"}},
                    {"metric": {"value": "totalViolations"}, "count": {"value": "150"}},
                    {"metric": {"value": "totalShapes"}, "count": {"value": "12"}}
                ]
            }
        }

        summary = dashboard_service.get_dashboard_summary()
        assert 'totalSessions' in summary
        assert 'totalViolations' in summary
        assert 'totalShapes' in summary
        assert summary['totalSessions'] == 25

    @patch('functions.dashboard_service.virtuoso_service')
    def test_get_recent_sessions(self, mock_virtuoso):
        """Test getting recent validation sessions."""
        from functions import dashboard_service

        mock_virtuoso.execute_sparql_query.return_value = {
            "results": {
                "bindings": [
                    {"sessionId": {"value": "session_123"}, "createdAt": {"value": "2023-01-01T10:00:00"}, "status": {"value": "completed"}},
                    {"sessionId": {"value": "session_124"}, "createdAt": {"value": "2023-01-01T11:00:00"}, "status": {"value": "in_progress"}}
                ]
            }
        }

        sessions = dashboard_service.get_recent_sessions(limit=10)
        assert len(sessions) == 2
        assert sessions[0]['sessionId'] == 'session_123'
        assert sessions[0]['status'] == 'completed'

    @patch('functions.dashboard_service.virtuoso_service')
    def test_get_validation_queue_status(self, mock_virtuoso):
        """Test getting validation queue status."""
        from functions import dashboard_service

        mock_virtuoso.execute_sparql_query.return_value = {
            "results": {
                "bindings": [
                    {"queuedJobs": {"value": "3"}, "averageWaitTime": {"value": "2.5"}}
                ]
            }
        }

        queue_status = dashboard_service.get_validation_queue_status()
        assert isinstance(queue_status, dict)
        assert queue_status['queuedJobs'] == 3
        assert queue_status['averageWaitTime'] == 2.5
        assert 'processingJobs' in queue_status
        assert 'completedJobs' in queue_status

    @patch('functions.dashboard_service.virtuoso_service')
    def test_get_system_health_metrics(self, mock_virtuoso):
        """Test getting system health metrics."""
        from functions import dashboard_service

        mock_virtuoso.execute_sparql_query.return_value = None  # Simple query success

        health = dashboard_service.get_system_health_metrics()
        assert 'overall' in health
        assert 'components' in health
        assert 'lastCheck' in health
        assert 'database' in health['components']
        assert 'memory' in health['components']
        assert 'storage' in health['components']
        assert 'cpu' in health['components']
        assert health['overall'] in ['healthy', 'warning', 'critical']

    @patch('functions.dashboard_service.virtuoso_service')
    def test_get_active_validations(self, mock_virtuoso):
        """Test getting currently active validations."""
        from functions import dashboard_service

        mock_virtuoso.execute_sparql_query.return_value = {
            "results": {
                "bindings": [
                    {"validationId": {"value": "val_1"}, "sessionId": {"value": "session_123"}, "progress": {"value": "65"}},
                    {"validationId": {"value": "val_2"}, "sessionId": {"value": "session_124"}, "progress": {"value": "30"}}
                ]
            }
        }

        active_validations = dashboard_service.get_active_validations()
        assert len(active_validations) == 2
        assert active_validations[0]['progress'] == 65

    @patch('functions.dashboard_service.virtuoso_service')
    def test_get_recent_errors(self, mock_virtuoso):
        """Test getting recent system errors."""
        from functions import dashboard_service

        mock_virtuoso.execute_sparql_query.return_value = {
            "results": {
                "bindings": [
                    {"errorId": {"value": "error_1"}, "message": {"value": "Database connection failed"}, "timestamp": {"value": "2023-01-01T10:30:00"}, "severity": {"value": "high"}},
                    {"errorId": {"value": "error_2"}, "message": {"value": "Invalid SPARQL syntax"}, "timestamp": {"value": "2023-01-01T11:15:00"}, "severity": {"value": "medium"}}
                ]
            }
        }

        errors = dashboard_service.get_recent_errors(limit=5)
        assert len(errors) == 2
        assert errors[0]['severity'] == 'high'
        assert 'Database connection failed' in errors[0]['message']

    @patch('functions.dashboard_service.virtuoso_service')
    def test_get_user_activity_stats(self, mock_virtuoso):
        """Test getting user activity statistics."""
        from functions import dashboard_service

        mock_virtuoso.execute_sparql_query.return_value = {
            "results": {
                "bindings": [
                    {"userId": {"value": "user_1"}, "action": {"value": "validation"}, "count": {"value": "15"}},
                    {"userId": {"value": "user_1"}, "action": {"value": "repair"}, "count": {"value": "8"}},
                    {"userId": {"value": "user_2"}, "action": {"value": "validation"}, "count": {"value": "12"}}
                ]
            }
        }

        activity = dashboard_service.get_user_activity_stats(days=7)
        assert len(activity) == 3
        assert activity[0]['userId'] == 'user_1'
        assert activity[0]['action'] == 'validation'

    @patch('functions.dashboard_service.virtuoso_service')
    def test_get_performance_trends(self, mock_virtuoso):
        """Test getting performance trends over time."""
        from functions import dashboard_service

        mock_virtuoso.execute_sparql_query.return_value = {
            "results": {
                "bindings": [
                    {"date": {"value": "2023-01-01"}, "avgValidationTime": {"value": "2.5"}, "totalValidations": {"value": "10"}},
                    {"date": {"value": "2023-01-02"}, "avgValidationTime": {"value": "2.1"}, "totalValidations": {"value": "15"}}
                ]
            }
        }

        trends = dashboard_service.get_performance_trends(days=30)
        assert len(trends) == 2
        assert trends[0]['date'] == '2023-01-01'
        assert float(trends[0]['avgValidationTime']) == 2.5

    def test_get_resource_usage(self):
        """Test getting system resource usage."""
        from functions import dashboard_service

        usage = dashboard_service.get_resource_usage()
        assert isinstance(usage, dict)
        assert 'cpu' in usage
        assert 'memory' in usage
        assert 'storage' in usage
        assert 'network' in usage

        # Check cpu resource structure
        cpu_data = usage['cpu']
        assert 'usage' in cpu_data
        assert 'cores' in cpu_data
        assert 'load' in cpu_data

        # Check memory resource structure
        memory_data = usage['memory']
        assert 'total' in memory_data
        assert 'used' in memory_data
        assert 'available' in memory_data
        assert 'usage' in memory_data

    @patch('functions.dashboard_service.virtuoso_service')
    def test_get_validation_history(self, mock_virtuoso):
        """Test getting validation history."""
        from functions import dashboard_service

        mock_virtuoso.execute_sparql_query.return_value = {
            "results": {
                "bindings": [
                    {"validationId": {"value": "val_1"}, "sessionId": {"value": "session_123"}, "startTime": {"value": "2023-01-01T10:00:00"}, "endTime": {"value": "2023-01-01T10:02:30"}, "status": {"value": "completed"}, "violationsFound": {"value": "5"}},
                    {"validationId": {"value": "val_2"}, "sessionId": {"value": "session_124"}, "startTime": {"value": "2023-01-01T11:00:00"}, "endTime": {"value": "2023-01-01T11:01:45"}, "status": {"value": "completed"}, "violationsFound": {"value": "12"}}
                ]
            }
        }

        history = dashboard_service.get_validation_history(limit=20)
        assert len(history) == 2
        assert history[0]['violationsFound'] == 5
        assert history[0]['status'] == 'completed'

    def test_calculate_dashboard_metrics(self):
        """Test dashboard metrics calculation."""
        from functions import dashboard_service

        test_data = {
            'successful_validations': 95,
            'total_validations': 100,
            'total_processing_time': 250,  # 2.5 * 100
            'total_errors': 5,
            'total_operations': 100,
            'throughput': 50  # 50/100 * 100 = 50
        }

        metrics = dashboard_service.calculate_dashboard_metrics(test_data)
        assert 'validationSuccessRate' in metrics
        assert 'averageProcessingTime' in metrics
        assert 'errorRate' in metrics
        assert 'systemEfficiency' in metrics

        # Verify calculations based on actual function implementation
        assert metrics['validationSuccessRate'] == 95.0  # 95/100 * 100
        assert metrics['averageProcessingTime'] == 2.5  # 250/100
        assert metrics['errorRate'] == 5.0  # 5/100 * 100
        assert metrics['systemEfficiency'] == 0.5  # min(100, 50/100)

    @patch('functions.dashboard_service.get_dashboard_summary')
    @patch('functions.dashboard_service.get_system_health_metrics')
    def test_get_alerts_and_notifications(self, mock_health, mock_summary):
        """Test getting alerts and notifications."""
        from functions import dashboard_service

        # Mock summary with low violations (no alert)
        mock_summary.return_value = {'recentViolations': 50}
        mock_health.return_value = {'overall': 'healthy'}

        alerts = dashboard_service.get_alerts_and_notifications()
        assert len(alerts) == 0

        # Mock summary with high violations (should trigger alert)
        mock_summary.return_value = {'recentViolations': 150}

        alerts = dashboard_service.get_alerts_and_notifications()
        assert len(alerts) == 1
        assert alerts[0]['id'] == 'high_violation_rate'
        assert alerts[0]['type'] == 'warning'
        assert 'High violation rate detected' in alerts[0]['message']
        assert alerts[0]['actionable'] is True

        # Mock unhealthy system (should trigger alert)
        mock_health.return_value = {'overall': 'critical'}
        mock_summary.return_value = {'recentViolations': 50}

        alerts = dashboard_service.get_alerts_and_notifications()
        assert len(alerts) == 1
        assert alerts[0]['id'] == 'system_health_issue'
        assert alerts[0]['type'] == 'error'
        assert 'System health issues detected' in alerts[0]['message']
        assert alerts[0]['actionable'] is True

    def test_get_quick_actions_data(self):
        """Test getting data for quick action buttons."""
        from functions import dashboard_service

        quick_actions = dashboard_service.get_quick_actions_data()
        assert isinstance(quick_actions, dict)
        assert 'canRunValidation' in quick_actions
        assert 'canExportData' in quick_actions
        assert 'canClearCache' in quick_actions
        assert 'pendingActions' in quick_actions
        assert isinstance(quick_actions['pendingActions'], list)

    def test_format_dashboard_response(self):
        """Test formatting dashboard response data."""
        from functions import dashboard_service

        # Test with list of dictionaries (the expected input type)
        raw_data = [
            {
                "totalSessions": {"value": "25"},
                "totalViolations": {"value": "150"},
                "systemStatus": {"value": "healthy"}
            }
        ]

        formatted = dashboard_service.format_dashboard_response(raw_data)
        assert isinstance(formatted, list)
        assert len(formatted) == 1
        assert formatted[0]['totalSessions'] == 25
        assert formatted[0]['totalViolations'] == 150
        assert formatted[0]['systemStatus'] == 'healthy'

    def test_get_widget_data(self):
        """Test getting data for dashboard widgets."""
        from functions import dashboard_service

        # Test single widget data
        widget_data = dashboard_service.get_widget_data('summary')
        assert isinstance(widget_data, dict)
        assert 'totalSessions' in widget_data

        # Test widget that doesn't exist
        empty_data = dashboard_service.get_widget_data('nonexistent')
        assert empty_data == {}