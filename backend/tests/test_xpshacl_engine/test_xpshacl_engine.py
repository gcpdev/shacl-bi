"""
Test main XPSHACL engine functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from rdflib import Graph, URIRef, Literal, Namespace
import rdflib

class TestXPSHACLEngine:
    """Test main XPSHACL engine orchestrator."""

    def test_engine_initialization(self):
        """Test engine initialization."""
        from functions.xpshacl_engine.xpshacl_engine import XPSHACLEngine

        engine = XPSHACLEngine()
        assert hasattr(engine, 'validator')
        assert hasattr(engine, 'explanation_generator')
        assert hasattr(engine, 'repair_engine')
        assert hasattr(engine, 'knowledge_graph')

    @patch('functions.xpshacl_engine.xpshacl_engine.ExtendedShaclValidator')
    def test_validate_dataset(self, mock_validator_class):
        """Test dataset validation."""
        from functions.xpshacl_engine.xpshacl_engine import XPSHACLEngine
        from functions.xpshacl_engine.xpshacl_architecture import ConstraintViolation

        # Mock validator
        mock_validator = Mock()
        mock_violation = ConstraintViolation(
            focus_node="http://example.org/resource1",
            shape_id="http://example.org/shapes/PersonShape",
            constraint_id="http://www.w3.org/ns/shacl#MinCountConstraintComponent",
            violation_type="CARDINALITY",
            property_path="http://example.org/ns#name",
            value=None
        )
        mock_validator.validate.return_value = [mock_violation]
        mock_validator_class.return_value = mock_validator

        engine = XPSHACLEngine()
        shapes_graph = Graph()
        data_graph = Graph()

        violations = engine.validate_dataset(shapes_graph, data_graph)
        assert len(violations) == 1
        assert violations[0].focus_node == "http://example.org/resource1"

    @patch('functions.xpshacl_engine.xpshacl_engine.ExtendedShaclValidator')
    @patch('functions.xpshacl_engine.xpshacl_engine.ExplanationGenerator')
    def test_generate_explanations(self, mock_explanation_class, mock_validator_class):
        """Test explanation generation."""
        from functions.xpshacl_engine.xpshacl_engine import XPSHACLEngine
        from functions.xpshacl_engine.xpshacl_architecture import ConstraintViolation

        # Mock validator
        mock_validator = Mock()
        mock_violation = ConstraintViolation(
            focus_node="http://example.org/resource1",
            shape_id="http://example.org/shapes/PersonShape",
            constraint_id="http://www.w3.org/ns/shacl#MinCountConstraintComponent",
            violation_type="CARDINALITY",
            property_path="http://example.org/ns#name",
            value=None
        )
        mock_validator.validate.return_value = [mock_violation]
        mock_validator_class.return_value = mock_validator

        # Mock explanation generator
        mock_explanation_gen = Mock()
        mock_explanation = Mock()
        mock_explanation.natural_language_explanation = "Test explanation"
        mock_explanation.correction_suggestions = ["Fix this"]
        mock_explanation_gen.generate_explanation.return_value = mock_explanation
        mock_explanation_class.return_value = mock_explanation_gen

        engine = XPSHACLEngine()
        shapes_graph = Graph()
        data_graph = Graph()

        explanations = engine.generate_explanations(shapes_graph, data_graph)
        assert len(explanations) == 1
        assert explanations[0].natural_language_explanation == "Test explanation"

    @patch('functions.xpshacl_engine.xpshacl_engine.ExtendedShaclValidator')
    @patch('functions.xpshacl_engine.xpshacl_engine.RepairEngine')
    def test_generate_repairs(self, mock_repair_class, mock_validator_class):
        """Test repair generation."""
        from functions.xpshacl_engine.xpshacl_engine import XPSHACLEngine
        from functions.xpshacl_engine.xpshacl_architecture import ConstraintViolation

        # Mock validator
        mock_validator = Mock()
        mock_violation = ConstraintViolation(
            focus_node="http://example.org/resource1",
            shape_id="http://example.org/shapes/PersonShape",
            constraint_id="http://www.w3.org/ns/shacl#MinCountConstraintComponent",
            violation_type="CARDINALITY",
            property_path="http://example.org/ns#name",
            value=None
        )
        mock_validator.validate.return_value = [mock_violation]
        mock_validator_class.return_value = mock_validator

        # Mock repair engine
        mock_repair_engine = Mock()
        mock_repair = Mock()
        mock_repair.repair_query = "INSERT DATA { <s> <p> 'value' }"
        mock_repair.repair_description = "Add missing value"
        mock_repair_engine.generate_repair.return_value = mock_repair
        mock_repair_class.return_value = mock_repair_engine

        engine = XPSHACLEngine()
        shapes_graph = Graph()
        data_graph = Graph()

        repairs = engine.generate_repairs(shapes_graph, data_graph)
        assert len(repairs) == 1
        assert repairs[0].repair_query == "INSERT DATA { <s> <p> 'value' }"

    def test_engine_with_knowledge_graph(self):
        """Test engine with knowledge graph integration."""
        from functions.xpshacl_engine.xpshacl_engine import XPSHACLEngine
        from functions.xpshacl_engine.knowledge_graph import ViolationKnowledgeGraph

        engine = XPSHACLEngine()
        assert isinstance(engine.knowledge_graph, ViolationKnowledgeGraph)

    @patch('functions.xpshacl_engine.xpshacl_engine.ExtendedShaclValidator')
    def test_batch_validation(self, mock_validator_class):
        """Test batch validation of multiple datasets."""
        from functions.xpshacl_engine.xpshacl_engine import XPSHACLEngine
        from functions.xpshacl_engine.xpshacl_architecture import ConstraintViolation

        # Mock validator
        mock_validator = Mock()
        mock_violation1 = ConstraintViolation(
            focus_node="http://example.org/resource1",
            shape_id="http://example.org/shapes/PersonShape",
            constraint_id="http://www.w3.org/ns/shacl#MinCountConstraintComponent",
            violation_type="CARDINALITY",
            property_path="http://example.org/ns#name",
            value=None
        )
        mock_violation2 = ConstraintViolation(
            focus_node="http://example.org/resource2",
            shape_id="http://example.org/shapes/PersonShape",
            constraint_id="http://www.w3.org/ns/shacl#PatternConstraintComponent",
            violation_type="PATTERN",
            property_path="http://example.org/ns#email",
            value="invalid"
        )
        mock_validator.validate.side_effect = [
            [mock_violation1],  # First dataset
            [mock_violation2]   # Second dataset
        ]
        mock_validator_class.return_value = mock_validator

        engine = XPSHACLEngine()
        shapes_graph = Graph()
        data_graphs = [Graph(), Graph()]  # Two datasets

        results = engine.batch_validate(shapes_graph, data_graphs)
        assert len(results) == 2
        assert len(results[0]) == 1
        assert len(results[1]) == 1

    def test_engine_configuration(self):
        """Test engine configuration options."""
        from functions.xpshacl_engine.xpshacl_engine import XPSHACLEngine

        config = {
            "enable_explanations": True,
            "enable_repairs": True,
            "knowledge_graph_path": "/tmp/test_vkg.ttl",
            "performance_logging": True
        }

        engine = XPSHACLEngine(config)
        assert engine.config == config

    @patch('functions.xpshacl_engine.xpshacl_engine.ExtendedShaclValidator')
    def test_validate_with_custom_config(self, mock_validator_class):
        """Test validation with custom configuration."""
        from functions.xpshacl_engine.xpshacl_engine import XPSHACLEngine

        config = {
            "abort_on_first_error": True,
            "enable_inference": False,
            "severity_level": "Warning"
        }

        engine = XPSHACLEngine(config)
        mock_validator = Mock()
        mock_validator.validate.return_value = []
        mock_validator_class.return_value = mock_validator

        shapes_graph = Graph()
        data_graph = Graph()

        engine.validate_dataset(shapes_graph, data_graph)
        # Verify validator was called with correct configuration
        mock_validator.validate.assert_called_once()

    def test_engine_statistics(self):
        """Test engine statistics collection."""
        from functions.xpshacl_engine.xpshacl_engine import XPSHACLEngine

        engine = XPSHACLEngine()

        # Initially should have no statistics
        stats = engine.get_statistics()
        assert 'validations_performed' in stats
        assert 'violations_detected' in stats
        assert 'explanations_generated' in stats
        assert stats['validations_performed'] == 0

    @patch('functions.xpshacl_engine.xpshacl_engine.ExtendedShaclValidator')
    def test_engine_statistics_increment(self, mock_validator_class):
        """Test that engine statistics increment correctly."""
        from functions.xpshacl_engine.xpshacl_engine import XPSHACLEngine
        from functions.xpshacl_engine.xpshacl_architecture import ConstraintViolation

        engine = XPSHACLEngine()

        # Mock validator to return violations
        mock_validator = Mock()
        mock_violation = ConstraintViolation(
            focus_node="http://example.org/resource1",
            shape_id="http://example.org/shapes/PersonShape",
            constraint_id="http://www.w3.org/ns/shacl#MinCountConstraintComponent",
            violation_type="CARDINALITY",
            property_path="http://example.org/ns#name",
            value=None
        )
        mock_validator.validate.return_value = [mock_violation]
        mock_validator_class.return_value = mock_validator

        shapes_graph = Graph()
        data_graph = Graph()

        # Perform validation
        engine.validate_dataset(shapes_graph, data_graph)

        # Check statistics
        stats = engine.get_statistics()
        assert stats['validations_performed'] == 1
        assert stats['violations_detected'] == 1

    def test_engine_error_handling(self):
        """Test engine error handling."""
        from functions.xpshacl_engine.xpshacl_engine import XPSHACLEngine

        engine = XPSHACLEngine()

        # Test with invalid inputs
        with pytest.raises(TypeError):
            engine.validate_dataset(None, Graph())

        with pytest.raises(TypeError):
            engine.validate_dataset(Graph(), None)

    @patch('functions.xpshacl_engine.xpshacl_engine.ExtendedShaclValidator')
    def test_engine_caching(self, mock_validator_class):
        """Test engine result caching."""
        from functions.xpshacl_engine.xpshacl_engine import XPSHACLEngine

        config = {"enable_caching": True}
        engine = XPSHACLEngine(config)

        mock_validator = Mock()
        mock_validator.validate.return_value = []
        mock_validator_class.return_value = mock_validator

        shapes_graph = Graph()
        data_graph = Graph()

        # First validation
        result1 = engine.validate_dataset(shapes_graph, data_graph)

        # Second validation with same inputs should use cache
        result2 = engine.validate_dataset(shapes_graph, data_graph)

        # Should have same results
        assert result1 == result2

    @patch('functions.xpshacl_engine.xpshacl_engine.ExtendedShaclValidator')
    def test_engine_performance_monitoring(self, mock_validator_class):
        """Test engine performance monitoring."""
        from functions.xpshacl_engine.xpshacl_engine import XPSHACLEngine

        config = {"performance_monitoring": True}
        engine = XPSHACLEngine(config)

        mock_validator = Mock()
        mock_validator.validate.return_value = []
        mock_validator_class.return_value = mock_validator

        shapes_graph = Graph()
        data_graph = Graph()

        # Perform validation
        engine.validate_dataset(shapes_graph, data_graph)

        # Check performance metrics
        metrics = engine.get_performance_metrics()
        assert 'last_validation_time' in metrics
        assert 'total_validation_time' in metrics
        assert 'average_validation_time' in metrics

    def test_engine_memory_management(self):
        """Test engine memory management."""
        from functions.xpshacl_engine.xpshacl_engine import XPSHACLEngine

        engine = XPSHACLEngine()

        # Test clearing caches and freeing memory
        engine.clear_caches()
        engine.free_memory()

        # Should not raise any errors
        stats = engine.get_statistics()
        assert stats is not None

    def test_engine_serialization(self):
        """Test engine state serialization."""
        from functions.xpshacl_engine.xpshacl_engine import XPSHACLEngine

        engine = XPSHACLEngine()

        # Test serializing engine state
        state = engine.serialize_state()
        assert isinstance(state, dict)
        assert 'config' in state
        assert 'statistics' in state

        # Test restoring engine state
        new_engine = XPSHACLEngine()
        new_engine.restore_state(state)
        assert new_engine.config == engine.config