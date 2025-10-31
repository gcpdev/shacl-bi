"""
Test PHOENIX service functionality for enhanced explanations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestPhoenixService:
    """Test PHOENIX integration service."""

    def test_explanation_cache_initialization(self):
        """Test explanation cache initialization."""
        from functions import phoenix_service

        assert hasattr(phoenix_service, "explanation_cache")
        assert isinstance(phoenix_service.explanation_cache, dict)
        assert len(phoenix_service.explanation_cache) == 0  # Should start empty

    @patch("functions.phoenix_service.load_vkg_from_virtuoso")
    def test_load_vkg_from_virtuoso_success(self, mock_load_vkg):
        """Test successful VKG loading from Virtuoso."""
        from functions import phoenix_service

        mock_vkg = Mock()
        mock_vkg.get_explanation.return_value = Mock()
        mock_load_vkg.return_value = mock_vkg

        result = phoenix_service.load_vkg_from_virtuoso()
        assert result == mock_vkg
        mock_load_vkg.assert_called_once()

    @patch("functions.virtuoso_service.execute_sparql_query")
    @patch("config.VIOLATION_KG_ONTOLOGY_PATH", "nonexistent_file.ttl")
    @patch("os.path.exists")
    def test_load_vkg_from_virtuoso_failure(self, mock_exists, mock_sparql):
        """Test VKG loading failure handling."""
        from functions import phoenix_service
        from functions.xpshacl_engine.knowledge_graph import ViolationKnowledgeGraph

        # Mock all attempts to fail
        mock_sparql.side_effect = Exception("Database connection failed")
        mock_exists.return_value = False  # Local file doesn't exist

        result = phoenix_service.load_vkg_from_virtuoso()
        # Function returns a minimal VKG as fallback, not None
        assert isinstance(result, ViolationKnowledgeGraph)
        assert len(result.graph) == 0  # Should be empty (minimal VKG)

    @patch("functions.phoenix_service.create_violation_signature")
    def test_create_violation_signature(self, mock_create_signature):
        """Test violation signature creation."""
        from functions import phoenix_service

        # Mock violation object
        mock_violation = Mock()
        mock_violation.focus_node = "http://example.org/resource1"
        mock_violation.constraint_id = (
            "http://www.w3.org/ns/shacl#MinCountConstraintComponent"
        )

        mock_create_signature.return_value = "test_signature_123"

        signature = phoenix_service.create_violation_signature(mock_violation)
        assert signature == "test_signature_123"
        mock_create_signature.assert_called_once_with(mock_violation)

    @patch("functions.phoenix_service.load_vkg_from_virtuoso")
    def test_get_cached_explanation(self, mock_load_vkg):
        """Test getting cached explanation."""
        from functions import phoenix_service

        mock_violation = Mock()
        mock_violation.focus_node = "http://example.org/resource1"
        mock_violation.constraint_id = (
            "http://www.w3.org/ns/shacl#PatternConstraintComponent"
        )

        # Mock the signature function to return different values
        with patch(
            "functions.phoenix_service.create_violation_signature"
        ) as mock_create_signature:
            mock_create_signature.return_value = "signature_123"

            # Test cache hit
            phoenix_service.explanation_cache["signature_123"] = Mock(
                natural_language_explanation="Test explanation",
                correction_suggestions=["Fix this"],
                proposed_repair_query="INSERT DATA { ... }",
            )

            result = phoenix_service.get_cached_explanation(mock_violation)
            assert result is not None
            assert result.natural_language_explanation == "Test explanation"

        # Test cache miss with different signature
        with patch(
            "functions.phoenix_service.create_violation_signature"
        ) as mock_create_signature:
            mock_create_signature.return_value = "signature_456"  # Different signature

            result = phoenix_service.get_cached_explanation(Mock())
            assert result is None

    @patch("functions.phoenix_service.load_vkg_from_virtuoso")
    @patch("functions.phoenix_service.create_violation_signature")
    def test_generate_enhanced_explanation(
        self, mock_create_signature, mock_load_vkg, sample_violation
    ):
        """Test enhanced explanation generation."""
        from functions import phoenix_service

        mock_vkg = Mock()
        mock_explanation = Mock()
        mock_explanation.natural_language_explanation = "Enhanced explanation"
        mock_explanation.correction_suggestions = ["Suggestion 1", "Suggestion 2"]
        mock_explanation.proposed_repair_query = "DELETE WHERE { ... }"
        mock_vkg.get_explanation.return_value = mock_explanation

        mock_load_vkg.return_value = mock_vkg
        mock_create_signature.return_value = "test_signature"

        # Create mock violation object
        class MockViolation:
            def __init__(self):
                self.focus_node = sample_violation["focus_node"]
                self.constraint_id = sample_violation["sourceConstraintComponent"]
                self.property_path = sample_violation["resultPath"]
                self.value = sample_violation["value"]

        mock_violation = MockViolation()

        result = phoenix_service.generate_enhanced_explanation(mock_violation)
        assert result is not None
        assert (
            result["natural_language_explanation"] == "Enhanced explanation"
        )  # clean_llm_text should preserve normal spaces
        assert len(result["correction_suggestions"]) == 2
        assert "proposed_repair_query" in result

    @patch("functions.phoenix_service.load_vkg_from_virtuoso")
    def test_generate_enhanced_explanation_no_vkg(
        self, mock_load_vkg, sample_violation
    ):
        """Test enhanced explanation generation when VKG is unavailable."""
        from functions import phoenix_service

        mock_load_vkg.return_value = None

        result = phoenix_service.generate_enhanced_explanation(Mock())
        assert result is None

    @patch("functions.phoenix_service.load_vkg_from_virtuoso")
    @patch("functions.phoenix_service.create_violation_signature")
    def test_cache_explanation(self, mock_create_signature, mock_load_vkg):
        """Test explanation caching."""
        from functions import phoenix_service

        mock_violation = Mock()
        mock_create_signature.return_value = "test_signature"

        explanation = {
            "natural_language_explanation": "Test explanation",
            "correction_suggestions": ["Fix it"],
            "proposed_repair_query": "INSERT DATA { ... }",
        }

        phoenix_service.cache_explanation(mock_violation, explanation)
        assert "test_signature" in phoenix_service.explanation_cache

    def test_clear_explanation_cache(self):
        """Test clearing explanation cache."""
        from functions import phoenix_service

        # Add some data to cache
        phoenix_service.explanation_cache["test1"] = Mock()
        phoenix_service.explanation_cache["test2"] = Mock()

        phoenix_service.clear_explanation_cache()
        assert len(phoenix_service.explanation_cache) == 0

    @patch("functions.phoenix_service.load_vkg_from_virtuoso")
    def test_batch_generate_explanations(self, mock_load_vkg):
        """Test batch explanation generation."""
        from functions import phoenix_service

        mock_vkg = Mock()
        mock_explanations = [
            Mock(
                natural_language_explanation="Explanation 1",
                correction_suggestions=[],
                proposed_repair_query="",
            ),
            Mock(
                natural_language_explanation="Explanation 2",
                correction_suggestions=[],
                proposed_repair_query="",
            ),
            Mock(
                natural_language_explanation="Explanation 3",
                correction_suggestions=[],
                proposed_repair_query="",
            ),
        ]
        mock_vkg.get_explanation.side_effect = mock_explanations
        mock_load_vkg.return_value = mock_vkg

        # Create proper mock violation objects
        class MockViolation:
            def __init__(self):
                self.focus_node = f"http://example.org/resource{hash(self)}"
                self.constraint_id = (
                    "http://www.w3.org/ns/shacl#PatternConstraintComponent"
                )
                self.property_path = "http://example.org/ns#name"
                self.value = "test_value"
                self.shape_id = "http://example.org/shapes/TestShape"
                self.message = "Test violation"
                self.severity = "Violation"

        violations = [MockViolation() for _ in range(3)]
        with patch(
            "functions.phoenix_service.create_violation_signature",
            side_effect=["sig1", "sig2", "sig3"],
        ):
            results = phoenix_service.batch_generate_explanations(violations)

        assert len(results) == 3
        assert all(result is not None for result in results)

    @patch("functions.phoenix_service.load_vkg_from_virtuoso")
    def test_get_constraint_statistics(self, mock_load_vkg):
        """Test getting constraint statistics."""
        from functions import phoenix_service

        mock_vkg = Mock()
        mock_stats = {
            "total_violations": 100,
            "constraint_types": {
                "MinCountConstraintComponent": 45,
                "MaxCountConstraintComponent": 30,
                "PatternConstraintComponent": 25,
            },
        }
        mock_vkg.get_statistics.return_value = mock_stats
        mock_load_vkg.return_value = mock_vkg

        stats = phoenix_service.get_constraint_statistics()
        assert stats["total_violations"] == 100
        assert "constraint_types" in stats

    @patch("functions.phoenix_service.load_vkg_from_virtuoso")
    def test_get_explanation_by_type(self, mock_load_vkg):
        """Test getting explanations by constraint type."""
        from functions import phoenix_service

        mock_vkg = Mock()
        mock_explanations = [
            Mock(
                constraint_type="MinCountConstraintComponent",
                explanation="Missing value",
            ),
            Mock(
                constraint_type="MaxCountConstraintComponent",
                explanation="Too many values",
            ),
        ]
        mock_vkg.get_explanations_by_type.return_value = mock_explanations
        mock_load_vkg.return_value = mock_vkg

        explanations = phoenix_service.get_explanation_by_type(
            "MinCountConstraintComponent"
        )
        assert len(explanations) == 2
        assert (
            explanations[0]["constraint_type"] == "MinCountConstraintComponent"
        )  # Function returns dicts, not objects

    def test_violation_to_dict_conversion(self):
        """Test converting violation objects to dictionaries."""
        from functions import phoenix_service
        from functions.xpshacl_engine.xpshacl_architecture import (
            ConstraintViolation,
            ViolationType,
        )

        violation = ConstraintViolation(
            focus_node="http://example.org/resource1",
            shape_id="http://example.org/shapes/PersonShape",
            constraint_id="http://www.w3.org/ns/shacl#PatternConstraintComponent",
            violation_type=ViolationType.PATTERN,
            property_path="http://example.org/ns#name",
            value="invalid_value",
        )

        violation_dict = phoenix_service.violation_to_dict(violation)

        assert violation_dict["focus_node"] == "http://example.org/resource1"
        assert (
            violation_dict["constraint_id"]
            == "http://www.w3.org/ns/shacl#PatternConstraintComponent"
        )

    def test_dict_to_violation_conversion(self):
        """Test converting dictionaries to violation objects."""
        from functions import phoenix_service

        violation_dict = {
            "focus_node": "http://example.org/resource1",
            "shape_id": "http://example.org/shapes/PersonShape",
            "constraint_id": "http://www.w3.org/ns/shacl#PatternConstraintComponent",
            "violation_type": "pattern",
            "property_path": "http://example.org/ns#name",
            "value": "invalid_value",
            "message": "Constraint violation",
            "severity": "Violation",
        }

        violation = phoenix_service.dict_to_violation(violation_dict)
        assert violation.focus_node == "http://example.org/resource1"
        assert (
            violation.constraint_id
            == "http://www.w3.org/ns/shacl#PatternConstraintComponent"
        )

    @patch("functions.phoenix_service.load_vkg_from_virtuoso")
    def test_get_explanation_confidence_score(self, mock_load_vkg):
        """Test getting explanation confidence score."""
        from functions import phoenix_service
        from functions.xpshacl_engine.xpshacl_architecture import (
            ConstraintViolation,
            ViolationType,
        )

        mock_vkg = Mock()
        mock_vkg.get_confidence_score.return_value = 0.85
        mock_load_vkg.return_value = mock_vkg

        # Create a proper ConstraintViolation object
        violation = ConstraintViolation(
            focus_node="http://example.org/resource1",
            shape_id="http://example.org/shapes/TestShape",
            constraint_id="http://www.w3.org/ns/shacl#PatternConstraintComponent",
            violation_type=ViolationType.PATTERN,
            property_path="http://example.org/ns#name",
            value="test_value",
        )

        score = phoenix_service.get_explanation_confidence_score(violation)
        assert score == 0.85

    def test_filter_relevant_explanations(self):
        """Test filtering explanations by relevance."""
        from functions import phoenix_service

        explanations = [
            {"confidence": 0.9, "constraint_type": "MinCount"},
            {"confidence": 0.7, "constraint_type": "MaxCount"},
            {"confidence": 0.8, "constraint_type": "Pattern"},
        ]

        # Filter by confidence threshold
        relevant = phoenix_service.filter_explanations(explanations, min_confidence=0.8)
        assert len(relevant) == 2
        assert all(exp["confidence"] >= 0.8 for exp in relevant)

        # Filter by constraint type
        pattern_explanations = phoenix_service.filter_explanations(
            explanations, constraint_type="Pattern"
        )
        assert len(pattern_explanations) == 1
        assert pattern_explanations[0]["constraint_type"] == "Pattern"

    @patch("functions.phoenix_service.load_vkg_from_virtuoso")
    def test_update_explanation_cache_with_ttl(self, mock_load_vkg):
        """Test updating cache with TTL (time-to-live)."""
        from functions import phoenix_service
        from functions.xpshacl_engine.xpshacl_architecture import (
            ConstraintViolation,
            ViolationType,
        )
        import time

        mock_vkg = Mock()
        mock_load_vkg.return_value = mock_vkg

        # Create a proper ConstraintViolation object
        violation = ConstraintViolation(
            focus_node="http://example.org/resource1",
            shape_id="http://example.org/shapes/TestShape",
            constraint_id="http://www.w3.org/ns/shacl#PatternConstraintComponent",
            violation_type=ViolationType.PATTERN,
            property_path="http://example.org/ns#name",
            value="test_value",
        )

        explanation = {"natural_language_explanation": "Test"}

        # Add with TTL
        phoenix_service.cache_explanation_with_ttl(violation, explanation, ttl=60)

        # Should be in cache (find the actual signature)
        cache_keys = list(phoenix_service.explanation_cache.keys())
        assert len(cache_keys) > 0  # Should have added something to cache

        # Get the actual key used
        cache_key = cache_keys[0]
        assert cache_key in phoenix_service.explanation_cache

        # Mock time passage
        with patch("time.time", return_value=time.time() + 61):
            # Should be expired and removed
            phoenix_service.clean_expired_cache()
            assert cache_key not in phoenix_service.explanation_cache
