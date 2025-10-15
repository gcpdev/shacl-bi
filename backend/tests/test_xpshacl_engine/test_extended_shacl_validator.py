"""
Test extended SHACL validator functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from rdflib import Graph, URIRef, Literal, Namespace
import rdflib

class TestExtendedShaclValidator:
    """Test extended SHACL validator with PHOENIX-style context enrichment."""

    def test_validator_initialization(self, mock_graph):
        """Test validator initialization with shapes graph."""
        from functions.xpshacl_engine.extended_shacl_validator import ExtendedShaclValidator

        validator = ExtendedShaclValidator(mock_graph)
        assert validator.shapes_graph == mock_graph
        assert validator.results_graph is None

    def test_validator_initialization_with_invalid_input(self):
        """Test validator initialization with invalid input."""
        from functions.xpshacl_engine.extended_shacl_validator import ExtendedShaclValidator

        with pytest.raises(TypeError):
            ExtendedShaclValidator("not_a_graph")

        with pytest.raises(TypeError):
            ExtendedShaclValidator(None)

    @patch('functions.xpshacl_engine.extended_shacl_validator.validate')
    def test_validate_success(self, mock_pyshacl_validate, mock_graph):
        """Test successful validation."""
        from functions.xpshacl_engine.extended_shacl_validator import ExtendedShaclValidator

        # Mock pyshacl validate to return conforms=True
        mock_pyshacl_validate.return_value = (True, None, None)

        validator = ExtendedShaclValidator(mock_graph)
        data_graph = Graph()

        violations = validator.validate(data_graph)
        assert violations == []

    @patch('functions.xpshacl_engine.extended_shacl_validator.validate')
    def test_validate_with_violations(self, mock_pyshacl_validate, mock_graph):
        """Test validation with violations."""
        from functions.xpshacl_engine.extended_shacl_validator import ExtendedShaclValidator
        from functions.xpshacl_engine.xpshacl_architecture import ConstraintViolation, ViolationType

        # Create mock results graph with violations
        results_graph = Graph()
        sh = Namespace("http://www.w3.org/ns/shacl#")
        ex = Namespace("http://example.org/")

        # Add validation result
        violation_node = URIRef("http://example.org/violation1")
        results_graph.add((violation_node, rdflib.RDF.type, URIRef(sh + "ValidationResult")))
        results_graph.add((violation_node, URIRef(sh + "focusNode"), URIRef(ex + "resource1")))
        results_graph.add((violation_node, URIRef(sh + "sourceConstraintComponent"), URIRef(sh + "MinCountConstraintComponent")))

        mock_pyshacl_validate.return_value = (False, results_graph, None)

        validator = ExtendedShaclValidator(mock_graph)
        data_graph = Graph()

        violations = validator.validate(data_graph)
        assert len(violations) == 1
        assert violations[0].focus_node == "http://example.org/resource1"
        assert violations[0].violation_type == ViolationType.CARDINALITY

    def test_get_violation_type_mapping(self):
        """Test violation type mapping."""
        from functions.xpshacl_engine.extended_shacl_validator import ExtendedShaclValidator
        from functions.xpshacl_engine.xpshacl_architecture import ViolationType

        validator = ExtendedShaclValidator(Graph())

        # Test known constraint components
        min_count_type = validator._get_violation_(URIRef("http://www.w3.org/ns/shacl#MinCountConstraintComponent"))
        assert min_count_type == ViolationType.CARDINALITY

        max_count_type = validator._get_violation_(URIRef("http://www.w3.org/ns/shacl#MaxCountConstraintComponent"))
        assert max_count_type == ViolationType.CARDINALITY

        # Test unknown constraint component
        unknown_type = validator._get_violation_(URIRef("http://example.org/UnknownConstraintComponent"))
        assert unknown_type == ViolationType.OTHER

    def test_extract_violations_from_graph(self, mock_graph):
        """Test extracting violations from results graph."""
        from functions.xpshacl_engine.extended_shacl_validator import ExtendedShaclValidator

        # Create results graph with various violation types
        results_graph = Graph()
        sh = Namespace("http://www.w3.org/ns/shacl#")
        ex = Namespace("http://example.org/")

        # Add MinCount violation
        violation1 = URIRef("http://example.org/violation1")
        results_graph.add((violation1, rdflib.RDF.type, URIRef(sh + "ValidationResult")))
        results_graph.add((violation1, URIRef(sh + "focusNode"), URIRef(ex + "resource1")))
        results_graph.add((violation1, URIRef(sh + "sourceConstraintComponent"), URIRef(sh + "MinCountConstraintComponent")))
        results_graph.add((violation1, URIRef(sh + "resultPath"), URIRef(ex + "name")))

        # Add Pattern violation
        violation2 = URIRef("http://example.org/violation2")
        results_graph.add((violation2, rdflib.RDF.type, URIRef(sh + "ValidationResult")))
        results_graph.add((violation2, URIRef(sh + "focusNode"), URIRef(ex + "resource2")))
        results_graph.add((violation2, URIRef(sh + "sourceConstraintComponent"), URIRef(sh + "PatternConstraintComponent")))
        results_graph.add((violation2, URIRef(sh + "resultPath"), URIRef(ex + "email")))
        results_graph.add((violation2, URIRef(sh + "value"), Literal("invalid-email")))

        validator = ExtendedShaclValidator(mock_graph)
        violations = validator._extract_violations_from_graph(results_graph, Graph())

        assert len(violations) == 2
        assert violations[0].focus_node == "http://example.org/resource1"
        assert violations[1].focus_node == "http://example.org/resource2"
        assert violations[1].value == "invalid-email"

    @patch('functions.xpshacl_engine.extended_shacl_validator.exrex')
    def test_pattern_violation_enrichment(self, mock_exrex, mock_graph):
        """Test pattern violation enrichment with example values."""
        from functions.xpshacl_engine.extended_shacl_validator import ExtendedShaclValidator

        # Mock exrex.getone
        mock_exrex.getone.return_value = "Example@domain.com"

        # Add shape with pattern constraint to shapes graph
        sh = Namespace("http://www.w3.org/ns/shacl#")
        ex = Namespace("http://example.org/")
        xsd = Namespace("http://www.w3.org/2001/XMLSchema#")

        shape = URIRef(ex + "PersonShape")
        mock_graph.add((shape, rdflib.RDF.type, URIRef(sh + "NodeShape")))
        mock_graph.add((shape, URIRef(sh + "targetClass"), URIRef(ex + "Person")))
        mock_graph.add((shape, URIRef(sh + "property"), URIRef(ex + "property1")))
        property1 = URIRef(ex + "property1")
        mock_graph.add((property1, URIRef(sh + "path"), URIRef(ex + "email")))
        mock_graph.add((property1, URIRef(sh + "pattern"), Literal("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$")))

        # Create results graph with pattern violation
        results_graph = Graph()
        violation = URIRef("http://example.org/violation1")
        results_graph.add((violation, rdflib.RDF.type, URIRef(sh + "ValidationResult")))
        results_graph.add((violation, URIRef(sh + "focusNode"), URIRef(ex + "person1")))
        results_graph.add((violation, URIRef(sh + "sourceConstraintComponent"), URIRef(sh + "PatternConstraintComponent")))
        results_graph.add((violation, URIRef(sh + "resultPath"), URIRef(ex + "email")))
        results_graph.add((violation, URIRef(sh + "sourceShape"), property1))  # Should point to property shape

        validator = ExtendedShaclValidator(mock_graph)
        violations = validator._extract_violations_from_graph(results_graph, Graph())

        assert len(violations) == 1
        assert 'exampleValue' in violations[0].context
        assert violations[0].context['exampleValue'] == "Example@domain.com"

    def test_max_count_violation_enrichment(self, mock_graph):
        """Test MaxCount violation enrichment."""
        from functions.xpshacl_engine.extended_shacl_validator import ExtendedShaclValidator

        # Add shape with MaxCount constraint
        sh = Namespace("http://www.w3.org/ns/shacl#")
        ex = Namespace("http://example.org/")

        shape = URIRef(ex + "PersonShape")
        mock_graph.add((shape, rdflib.RDF.type, URIRef(sh + "NodeShape")))
        mock_graph.add((shape, URIRef(sh + "property"), URIRef(ex + "property1")))
        property1 = URIRef(ex + "property1")
        mock_graph.add((property1, URIRef(sh + "path"), URIRef(ex + "email")))
        mock_graph.add((property1, URIRef(sh + "maxCount"), Literal(1)))

        # Create results graph with MaxCount violation
        results_graph = Graph()
        violation = URIRef("http://example.org/violation1")
        results_graph.add((violation, rdflib.RDF.type, URIRef(sh + "ValidationResult")))
        results_graph.add((violation, URIRef(sh + "focusNode"), URIRef(ex + "person1")))
        results_graph.add((violation, URIRef(sh + "sourceConstraintComponent"), URIRef(sh + "MaxCountConstraintComponent")))
        results_graph.add((violation, URIRef(sh + "resultPath"), URIRef(ex + "email")))
        results_graph.add((violation, URIRef(sh + "sourceShape"), property1))

        # Create data graph with actual values
        data_graph = Graph()
        person1 = URIRef(ex + "person1")
        data_graph.add((person1, URIRef(ex + "email"), Literal("email1@example.com")))
        data_graph.add((person1, URIRef(ex + "email"), Literal("email2@example.com")))

        validator = ExtendedShaclValidator(mock_graph)
        violations = validator._extract_violations_from_graph(results_graph, data_graph)

        assert len(violations) == 1
        assert 'maxCount' in violations[0].context
        assert violations[0].context['maxCount'] == 1
        assert 'actualValues' in violations[0].context
        assert len(violations[0].context['actualValues']) == 2

    def test_in_constraint_violation_enrichment(self, mock_graph):
        """Test InConstraint violation enrichment."""
        from functions.xpshacl_engine.extended_shacl_validator import ExtendedShaclValidator

        # Add shape with InConstraint
        sh = Namespace("http://www.w3.org/ns/shacl#")
        ex = Namespace("http://example.org/")
        rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")

        shape = URIRef(ex + "PersonShape")
        mock_graph.add((shape, rdflib.RDF.type, URIRef(sh + "NodeShape")))
        mock_graph.add((shape, URIRef(sh + "property"), URIRef(ex + "property1")))
        property1 = URIRef(ex + "property1")
        mock_graph.add((property1, URIRef(sh + "path"), URIRef(ex + "status")))

        # Create RDF list for allowed values
        list_node = URIRef(ex + "list1")
        mock_graph.add((property1, URIRef(sh + "in"), list_node))
        mock_graph.add((list_node, URIRef(rdf + "first"), Literal("Active")))
        mock_graph.add((list_node, URIRef(rdf + "rest"), URIRef(ex + "list2")))
        mock_graph.add((URIRef(ex + "list2"), URIRef(rdf + "first"), Literal("Inactive")))
        mock_graph.add((URIRef(ex + "list2"), URIRef(rdf + "rest"), rdf.nil))

        # Create results graph with InConstraint violation
        results_graph = Graph()
        violation = URIRef("http://example.org/violation1")
        results_graph.add((violation, rdflib.RDF.type, URIRef(sh + "ValidationResult")))
        results_graph.add((violation, URIRef(sh + "focusNode"), URIRef(ex + "person1")))
        results_graph.add((violation, URIRef(sh + "sourceConstraintComponent"), URIRef(sh + "InConstraintComponent")))
        results_graph.add((violation, URIRef(sh + "resultPath"), URIRef(ex + "status")))
        results_graph.add((violation, URIRef(sh + "sourceShape"), property1))

        validator = ExtendedShaclValidator(mock_graph)
        violations = validator._extract_violations_from_graph(results_graph, Graph())

        assert len(violations) == 1
        assert 'allowedValues' in violations[0].context
        assert "Active" in violations[0].context['allowedValues']
        assert "Inactive" in violations[0].context['allowedValues']

    def test_serialize_focus_node(self, mock_graph):
        """Test focus node serialization."""
        from functions.xpshacl_engine.extended_shacl_validator import _serialize_focus_node

        # Add data to graph
        ex = Namespace("http://example.org/")
        person1 = URIRef(ex + "person1")
        mock_graph.add((person1, URIRef(ex + "name"), Literal("John Doe")))
        mock_graph.add((person1, URIRef(ex + "age"), Literal(30)))
        mock_graph.add((person1, URIRef(ex + "type"), URIRef(ex + "Person")))

        definition = _serialize_focus_node(person1, mock_graph)
        assert isinstance(definition, str)
        assert "John Doe" in definition
        assert "30" in definition

    def test_validator_with_complex_shapes(self, mock_graph):
        """Test validator with complex shapes and multiple constraints."""
        from functions.xpshacl_engine.extended_shacl_validator import ExtendedShaclValidator

        # Add complex shape with multiple constraints
        sh = Namespace("http://www.w3.org/ns/shacl#")
        ex = Namespace("http://example.org/")
        xsd = Namespace("http://www.w3.org/2001/XMLSchema#")

        shape = URIRef(ex + "ComplexShape")
        mock_graph.add((shape, rdflib.RDF.type, URIRef(sh + "NodeShape")))

        # Add multiple property constraints
        for i, prop in enumerate(['name', 'email', 'age']):
            property_node = URIRef(f"http://example.org/property{i}")
            mock_graph.add((shape, URIRef(sh + "property"), property_node))
            mock_graph.add((property_node, URIRef(sh + "path"), URIRef(ex + prop)))

            if prop == 'name':
                mock_graph.add((property_node, URIRef(sh + "datatype"), URIRef(xsd + "string")))
                mock_graph.add((property_node, URIRef(sh + "minCount"), Literal(1)))
            elif prop == 'email':
                mock_graph.add((property_node, URIRef(sh + "pattern"), Literal("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$")))
            elif prop == 'age':
                mock_graph.add((property_node, URIRef(sh + "datatype"), URIRef(xsd + "integer")))
                mock_graph.add((property_node, URIRef(sh + "minInclusive"), Literal(0)))
                mock_graph.add((property_node, URIRef(sh + "maxInclusive"), Literal(150)))

        validator = ExtendedShaclValidator(mock_graph)
        assert validator.shapes_graph == mock_graph

    @patch('functions.xpshacl_engine.extended_shacl_validator.validate')
    def test_validator_performance_logging(self, mock_pyshacl_validate, mock_graph):
        """Test that validator logs performance metrics."""
        from functions.xpshacl_engine.extended_shacl_validator import ExtendedShaclValidator
        import logging

        # Create mock results graph with violations to trigger logging
        results_graph = Graph()
        sh = Namespace("http://www.w3.org/ns/shacl#")
        ex = Namespace("http://example.org/")
        violation_node = URIRef("http://example.org/violation1")
        results_graph.add((violation_node, rdflib.RDF.type, URIRef(sh + "ValidationResult")))

        mock_pyshacl_validate.return_value = (False, results_graph, None)

        # Capture log messages by patching the module-level logger directly
        with patch('functions.xpshacl_engine.extended_shacl_validator.logger') as mock_logger:
            validator = ExtendedShaclValidator(mock_graph)
            data_graph = Graph()

            violations = validator.validate(data_graph)

            # Verify that debug logging was called
            mock_logger.debug.assert_called()
            # Check that performance timing was logged
            log_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            assert any("pyshacl validation took" in call for call in log_calls)

    def test_validator_error_handling(self, mock_graph):
        """Test validator error handling."""
        from functions.xpshacl_engine.extended_shacl_validator import ExtendedShaclValidator

        validator = ExtendedShaclValidator(mock_graph)

        # Test with None data graph
        with pytest.raises(TypeError):
            validator.validate(None)

        # Test with invalid data graph
        with pytest.raises(TypeError):
            validator.validate("not_a_graph")

    @patch('functions.xpshacl_engine.extended_shacl_validator.validate')
    def test_validator_with_empty_results_graph(self, mock_pyshacl_validate, mock_graph):
        """Test validator handling of empty results graph."""
        from functions.xpshacl_engine.extended_shacl_validator import ExtendedShaclValidator

        mock_pyshacl_validate.return_value = (False, Graph(), None)

        validator = ExtendedShaclValidator(mock_graph)
        data_graph = Graph()

        violations = validator.validate(data_graph)
        assert violations == []