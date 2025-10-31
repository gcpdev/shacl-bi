#!/usr/bin/env python3
"""
Script to clear the Violation Knowledge Graph (VKG) from Virtuoso.
This removes all violation explanations and cached data.
"""

import os
import sys

# Add the current directory to Python path to import config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Virtuoso service functions to use the same connection setup
from functions.virtuoso_service import execute_sparql_update

# Simple logging setup
def log_info(message):
    print(f"[INFO] {message}")

def log_error(message):
    print(f"[ERROR] {message}")

def clear_violation_kg():
    """
    Clears the Violation Knowledge Graph in Virtuoso by executing a
    SPARQL CLEAR GRAPH query using the same connection method as the app.
    """
    # VKG graph URI - same as used throughout the application
    vkg_graph_uri = "http://ex.org/ViolationKnowledgeGraph"

    log_info(f"Preparing to clear graph: {vkg_graph_uri}")

    # SPARQL query to clear the graph
    query = f"CLEAR GRAPH <{vkg_graph_uri}>"

    try:
        log_info("Executing SPARQL CLEAR GRAPH query...")
        execute_sparql_update(query)
        log_info(f"Successfully cleared graph: {vkg_graph_uri}")
    except Exception as e:
        log_error(f"An error occurred while trying to clear the graph: {e}")
        log_error("This might be due to network issues or Virtuoso configuration")


def clear_all_validation_graphs():
    """
    Additionally clear all validation session graphs
    """
    log_info("Also clearing validation session graphs...")

    # Clear validation graphs by matching the full pattern
    query = """
    DELETE WHERE {
      GRAPH ?g {
        ?s ?p ?o
      }
      FILTER (str(?g) = "http://ex.org/ValidationReport/Session_" ||
              regex(str(?g), "^http://ex.org/ValidationReport/Session_"))
    }
    """

    try:
        execute_sparql_update(query)
        log_info("Successfully cleared validation session graphs")
    except Exception as e:
        log_error(f"Error clearing validation graphs: {e}")


def clear_shapes_graphs():
    """
    Clear all shapes graphs
    """
    log_info("Clearing shapes graphs...")

    # Clear shapes graphs by matching the full pattern
    query = """
    DELETE WHERE {
      GRAPH ?g {
        ?s ?p ?o
      }
      FILTER (str(?g) = "http://ex.org/Shapes/Session_" ||
              regex(str(?g), "^http://ex.org/Shapes/Session_"))
    }
    """

    try:
        execute_sparql_update(query)
        log_info("Successfully cleared shapes graphs")
    except Exception as e:
        log_error(f"Error clearing shapes graphs: {e}")


def clear_all_session_graphs():
    """
    Comprehensive clear using individual CLEAR GRAPH commands for all session graphs
    """
    log_info("Performing comprehensive clear of all session graphs...")

    # First, get a list of all session-related graphs
    from functions.virtuoso_service import execute_sparql_query

    try:
        # Query to find all session-related graphs
        query = """
        SELECT DISTINCT ?g WHERE {
          GRAPH ?g { ?s ?p ?o }
          FILTER (
            regex(str(?g), "Session_[a-f0-9]{8}$") ||
            regex(str(?g), "ValidationReport/Session_") ||
            regex(str(?g), "Shapes/Session_")
          )
        }
        ORDER BY ?g
        """

        result = execute_sparql_query(query)
        if result and "results" in result and "bindings" in result["results"]:
            log_info(f"Found {len(result['results']['bindings'])} session-related graphs to clear")

            for binding in result["results"]["bindings"]:
                graph_uri = binding["g"]["value"]
                log_info(f"Clearing: {graph_uri}")

                clear_query = f"CLEAR GRAPH <{graph_uri}>"
                execute_sparql_update(clear_query)

            log_info("Successfully cleared all session-related graphs")
        else:
            log_info("No session-related graphs found to clear")

    except Exception as e:
        log_error(f"Error in comprehensive clear: {e}")


def clear_ontology_graphs():
    """
    Clear all ontology graphs that might contain session data
    """
    log_info("Clearing ontology and system graphs...")

    # List of system graphs that should be cleared
    system_graphs = [
        "http://ex.org/xpshacl",
        "http://ex.org/ontology",
        "http://example.org/ns"
    ]

    for graph_uri in system_graphs:
        try:
            log_info(f"Attempting to clear: {graph_uri}")
            query = f"CLEAR GRAPH <{graph_uri}>"
            execute_sparql_update(query)
            log_info(f"Successfully cleared: {graph_uri}")
        except Exception as e:
            log_info(f"Could not clear {graph_uri}: {e}")  # Not an error if it doesn't exist


def show_graph_statistics():
    """
    Show statistics about what's left in the database
    """
    log_info("Checking remaining graph statistics...")

    from functions.virtuoso_service import execute_sparql_query

    try:
        # Count remaining graphs
        query = """
        SELECT (COUNT(DISTINCT ?g) as ?graphCount) WHERE {
          GRAPH ?g { ?s ?p ?o }
        }
        """
        result = execute_sparql_query(query)
        if result and "results" in result and "bindings" in result["results"]:
            count = result["results"]["bindings"][0]["graphCount"]["value"]
            log_info(f"Remaining graphs in database: {count}")

        # List remaining graphs that contain data
        query = """
        SELECT DISTINCT ?g WHERE {
          GRAPH ?g { ?s ?p ?o }
        }
        ORDER BY ?g
        """
        result = execute_sparql_query(query)
        if result and "results" in result and "bindings" in result["results"]:
            log_info("Remaining graphs:")
            for binding in result["results"]["bindings"]:
                graph_uri = binding["g"]["value"]
                log_info(f"  - {graph_uri}")

    except Exception as e:
        log_error(f"Error getting graph statistics: {e}")


if __name__ == "__main__":
    log_info("=== VKG Clear Script ===")
    log_info("This script will clear:")
    log_info("1. Violation Knowledge Graph (VKG)")
    log_info("2. All validation session graphs")
    log_info("3. All shapes graphs")
    log_info("4. All ontology/system graphs")
    log_info("5. Comprehensive individual graph clearing")
    log_info("")

    # Ask for confirmation
    try:
        response = input("Do you want to continue? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            log_info("Operation cancelled by user.")
            sys.exit(0)
    except KeyboardInterrupt:
        log_info("\nOperation cancelled by user.")
        sys.exit(0)

    log_info("Starting cleanup...")
    clear_violation_kg()
    clear_all_validation_graphs()
    clear_shapes_graphs()
    clear_all_session_graphs()  # This will clear everything remaining
    clear_ontology_graphs()
    log_info("")
    show_graph_statistics()
    log_info("=== Clear Complete ===")
