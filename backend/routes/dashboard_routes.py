from flask import Blueprint, jsonify, request
from functions.dashboard_service import get_dashboard_data
from functions import virtuoso_service

dashboard_bp = Blueprint("dashboard", __name__)


def get_most_recent_session_id():
    """
    Find the most recent session ID by looking at validation report graphs.
    Returns the session ID without the 'Session_' prefix, or None if no sessions found.
    """
    try:
        # Query to find all session-specific validation report graphs and get the most recent one
        query = """
        SELECT ?sessionGraph
        WHERE {
            GRAPH ?graphName {
                ?report a <http://www.w3.org/ns/shacl#ValidationReport> .
            }
            FILTER(strstarts(str(?graphName), "http://ex.org/ValidationReport/Session_"))
            BIND(?graphName AS ?sessionGraph)
        }
        ORDER BY DESC(?sessionGraph)
        LIMIT 1
        """

        result = virtuoso_service.execute_sparql_query(query)
        bindings = result.get("results", {}).get("bindings", [])

        if bindings:
            session_graph_uri = bindings[0].get("sessionGraph", {}).get("value", "")
            # Extract session ID from URI like "http://ex.org/ValidationReport/Session_ab28b2e2"
            if "Session_" in session_graph_uri:
                return session_graph_uri.split("Session_")[1]

        return None
    except Exception as e:
        print(f"Error finding most recent session: {e}")
        return None


@dashboard_bp.route("/api/test-violation-count", methods=["GET"])
def test_violation_count():
    """Test endpoint to directly check violation count"""
    try:
        session_id = request.args.get("session_id")
        if session_id:
            validation_graph_uri = (
                f"http://ex.org/ValidationReport/Session_{session_id}"
            )
            shapes_graph_uri = f"http://ex.org/ShapesGraph/Session_{session_id}"
        else:
            validation_graph_uri = "http://ex.org/ValidationReport"
            shapes_graph_uri = "http://ex.org/ShapesGraph"

        print(f"Test endpoint: Querying violations from {validation_graph_uri}")
        count = virtuoso_service.get_number_of_violations_in_validation_report(
            validation_graph_uri
        )
        print(f"Test endpoint: Found {count} violations")

        # Also test shapes graph functions
        try:
            from functions import (
                get_number_of_node_shapes,
                get_number_of_paths_in_shapes_graph,
            )

            shapes_count = get_number_of_node_shapes(shapes_graph_uri)
            paths_count = get_number_of_paths_in_shapes_graph(shapes_graph_uri)
            print(f"Test endpoint: Found {shapes_count} shapes and {paths_count} paths")
        except Exception as e:
            shapes_count = f"Error: {str(e)}"
            paths_count = f"Error: {str(e)}"

        return (
            jsonify(
                {
                    "violation_count": count,
                    "validation_graph_uri": validation_graph_uri,
                    "shapes_graph_uri": shapes_graph_uri,
                    "shapes_count": shapes_count,
                    "paths_count": paths_count,
                }
            ),
            200,
        )
    except Exception as e:
        print(f"Test endpoint error: {e}")
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route("/api/test-recent-session", methods=["GET"])
def test_most_recent_session():
    """Test endpoint to check the most recent session finding logic"""
    try:
        session_id = get_most_recent_session_id()
        return (
            jsonify(
                {"most_recent_session_id": session_id, "found": session_id is not None}
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route("/api/debug-shapes-graph", methods=["GET"])
def debug_shapes_graph():
    """Debug endpoint to check shapes graph data"""
    try:
        session_id = request.args.get("session_id", "fee25bee")
        validation_graph_uri = f"http://ex.org/ValidationReport/Session_{session_id}"
        shapes_graph_uri = f"http://ex.org/ShapesGraph/Session_{session_id}"

        # Test direct SPARQL queries
        results = {}

        # Count nodes in shapes graph
        shapes_query = f"""
        SELECT (COUNT(DISTINCT ?shape) as ?shapeCount) WHERE {{
            GRAPH <{shapes_graph_uri}> {{
                ?shape a <http://www.w3.org/ns/shacl#NodeShape> .
            }}
        }}
        """

        # Count paths in shapes graph
        paths_query = f"""
        SELECT (COUNT(DISTINCT ?path) as ?pathCount) WHERE {{
            GRAPH <{shapes_graph_uri}> {{
                ?shape <http://www.w3.org/ns/shacl#property> ?prop .
                ?prop <http://www.w3.org/ns/shacl#path> ?path .
            }}
        }}
        """

        # Count constraint components
        components_query = f"""
        SELECT (COUNT(DISTINCT ?component) as ?componentCount) WHERE {{
            GRAPH <{shapes_graph_uri}> {{
                ?constraint a ?component .
                FILTER(?component != <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>)
            }}
        }}
        """

        for name, query in [
            ("shapes", shapes_query),
            ("paths", paths_query),
            ("components", components_query),
        ]:
            try:
                result = virtuoso_service.execute_sparql_query(query)
                count = int(
                    result.get("results", {})
                    .get("bindings", [{}])[0]
                    .get(name + "Count", {})
                    .get("value", 0)
                )
                results[name] = count
            except Exception as e:
                results[name] = f"Error: {str(e)}"

        # Check if shapes graph exists
        graph_exists_query = f"""
        ASK WHERE {{
            GRAPH <{shapes_graph_uri}> {{ ?s ?p ?o }}
        }}
        """

        try:
            exists_result = virtuoso_service.execute_sparql_query(graph_exists_query)
            graph_exists = exists_result.get("boolean", False)
            results["graph_exists"] = graph_exists
        except Exception as e:
            results["graph_exists"] = f"Error: {str(e)}"

        return (
            jsonify(
                {
                    "session_id": session_id,
                    "validation_graph_uri": validation_graph_uri,
                    "shapes_graph_uri": shapes_graph_uri,
                    "results": results,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route("/api/dashboard-data", methods=["GET"])
def get_dashboard_data_route():
    """
    Get dashboard analytics data
    Returns comprehensive statistics for the SHACL dashboard
    Supports session-specific data isolation
    """
    try:
        # Check for session_id parameter for tenant isolation
        session_id = request.args.get("session_id")

        if session_id:
            # Use the provided session ID
            validation_graph_uri = (
                f"http://ex.org/ValidationReport/Session_{session_id}"
            )
        else:
            # Try to find the most recent session automatically
            try:
                # Inline SPARQL query to find most recent session
                query = """
                SELECT ?sessionGraph
                WHERE {
                    GRAPH ?graphName {
                        ?report a <http://www.w3.org/ns/shacl#ValidationReport> .
                    }
                    FILTER(strstarts(str(?graphName), "http://ex.org/ValidationReport/Session_"))
                    BIND(?graphName AS ?sessionGraph)
                }
                ORDER BY DESC(?sessionGraph)
                LIMIT 1
                """

                result = virtuoso_service.execute_sparql_query(query)
                bindings = result.get("results", {}).get("bindings", [])

                if bindings:
                    session_graph_uri = (
                        bindings[0].get("sessionGraph", {}).get("value", "")
                    )
                    if "Session_" in session_graph_uri:
                        session_id = session_graph_uri.split("Session_")[1]
                        validation_graph_uri = (
                            f"http://ex.org/ValidationReport/Session_{session_id}"
                        )
                        print(f"Auto-selected most recent session: {session_id}")
                    else:
                        validation_graph_uri = "http://ex.org/ValidationReport"
                        print("Invalid session graph format, using default empty graph")
                else:
                    # No sessions found, use default graph (will be empty)
                    validation_graph_uri = "http://ex.org/ValidationReport"
                    print("No sessions found, using default empty graph")
            except Exception as e:
                print(f"Error finding most recent session: {e}")
                validation_graph_uri = "http://ex.org/ValidationReport"

        data = get_dashboard_data(validation_graph_uri)
        return (
            jsonify(
                {
                    **data,
                    "session_id": session_id,
                    "validation_graph_uri": validation_graph_uri,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
