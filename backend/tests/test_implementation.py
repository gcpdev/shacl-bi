#!/usr/bin/env python3
"""
Test script to verify the new example value functionality in violation details
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rdflib import Graph
from functions.xpshacl_engine.extended_shacl_validator import ExtendedShaclValidator
import exrex


def test_example_value_generation():
    """Test the example value generation for pattern constraints"""
    print("=== Testing Example Value Generation ===")

    # Load the comprehensive shapes
    shapes_graph = Graph()
    shapes_graph.parse("data/comprehensive_shapes.ttl", format="turtle")
    print(f"Loaded {len(shapes_graph)} triples from shapes graph")

    # Load the comprehensive data
    data_graph = Graph()
    data_graph.parse("data/comprehensive_data.ttl", format="turtle")
    print(f"Loaded {len(data_graph)} triples from data graph")

    # Create validator and validate
    validator = ExtendedShaclValidator(shapes_graph)
    violations = validator.validate(data_graph)

    print(f"\nFound {len(violations)} violations:")

    for i, violation in enumerate(violations, 1):
        print(f"\n--- Violation {i} ---")
        print(f"Focus Node: {violation.focus_node}")
        print(f"Property Path: {violation.property_path}")
        print(f"Constraint ID: {violation.constraint_id}")
        print(f"Value: {violation.value}")

        # Show context information (PHOENIX-style)
        if violation.context:
            print("Context Information:")
            for key, value in violation.context.items():
                print(f"  {key}: {value}")

        # Check for pattern violations specifically
        if "PatternConstraintComponent" in violation.constraint_id:
            print("=== PATTERN VIOLATION ===")
            if "pattern" in violation.context:
                pattern = violation.context["pattern"]
                print(f"Pattern: {pattern}")

                # Test exrex directly
                try:
                    example = exrex.getone(pattern)
                    print(f"Generated Example: {example}")

                    # Compare with our implementation
                    if "exampleValue" in violation.context:
                        print(
                            f"Our Implementation: {violation.context['exampleValue']}"
                        )
                        print("[SUCCESS] Example values generated successfully!")
                    else:
                        print("[ERROR] Example value not found in context")
                except Exception as e:
                    print(f"[ERROR] Error generating example: {e}")
            else:
                print("[ERROR] No pattern found in context")

        print("-" * 50)


def test_simple_routes_context():
    """Test the context generation in simple routes"""
    print("\n=== Testing Simple Routes Context Generation ===")

    try:
        from routes.simple_routes import _get_violation_context

        # Test a pattern violation
        test_violation = {
            "constraint_id": "http://www.w3.org/ns/shacl#PatternConstraintComponent",
            "property_path": "http://example.org/ns#employeeId",
            "focus_node": "http://example.org/emp_manager",
        }

        context = _get_violation_context(test_violation, "test_session")
        print("Pattern Context Test:")
        print(f"Context: {context}")

        if "exampleValue" in context:
            print(f"[SUCCESS] Example value: {context['exampleValue']}")
        else:
            print("[ERROR] No example value generated")

        # Test an InConstraint violation (from PHOENIX data)
        in_violation = {
            "constraint_id": "http://www.w3.org/ns/shacl#InConstraintComponent",
            "property_path": "http://example.org/ns#status",
            "focus_node": "http://example.org/ns#proj_laureaus",
            "value": "Archived",
        }

        in_context = _get_violation_context(in_violation, "test_session")
        print("\nInConstraint Context Test:")
        print(f"Context: {in_context}")

        if "allowedValues" in in_context:
            print(f"[SUCCESS] Allowed values: {in_context['allowedValues']}")
        else:
            print("[ERROR] No allowed values generated")

    except Exception as e:
        print(f"[ERROR] Error testing simple routes: {e}")


def test_in_constraint_data():
    """Test InConstraint violations from comprehensive data"""
    print("\n=== Testing InConstraint Violations ===")

    from rdflib import Graph
    from functions.xpshacl_engine.extended_shacl_validator import ExtendedShaclValidator

    # Load the comprehensive shapes and data
    shapes_graph = Graph()
    shapes_graph.parse("data/comprehensive_shapes.ttl", format="turtle")

    data_graph = Graph()
    data_graph.parse("data/comprehensive_data.ttl", format="turtle")

    # Create validator and validate
    validator = ExtendedShaclValidator(shapes_graph)
    violations = validator.validate(data_graph)

    in_constraint_violations = [
        v for v in violations if "InConstraintComponent" in v.constraint_id
    ]

    print(f"Found {len(in_constraint_violations)} InConstraint violations:")

    for i, violation in enumerate(in_constraint_violations, 1):
        print(f"\n--- InConstraint Violation {i} ---")
        print(f"Focus Node: {violation.focus_node}")
        print(f"Property Path: {violation.property_path}")
        print(f"Value: {violation.value}")

        if violation.context:
            print("Context Information:")
            for key, value in violation.context.items():
                print(f"  {key}: {value}")

        print("-" * 50)


if __name__ == "__main__":
    test_example_value_generation()
    test_simple_routes_context()
    test_in_constraint_data()
    print("\n=== Test Complete ===")
