import json
from . import virtuoso_service

def get_dashboard_data(validation_graph_uri="http://ex.org/ValidationReport"):
    try:
        print(f"Dashboard service: Querying violations from {validation_graph_uri}")
        total_violations = virtuoso_service.get_number_of_violations_in_validation_report(validation_graph_uri)
        print(f"Dashboard service: Found {total_violations} violations")
    except Exception as e:
        print(f"Dashboard service: Error getting violations: {e}")
        total_violations = 0

    try:
        all_shapes = virtuoso_service.get_all_shapes_names(validation_graph_uri)
    except Exception:
        all_shapes = []

    violated_node_shapes = len(all_shapes)

    try:
        total_paths = len(virtuoso_service.get_all_property_path_names(validation_graph_uri))
    except Exception:
        total_paths = 0

    try:
        total_focus_nodes = len(virtuoso_service.get_all_focus_node_names(validation_graph_uri))
    except Exception:
        total_focus_nodes = 0

    try:
        total_constraint_components = len(virtuoso_service.get_all_constraint_components_names(validation_graph_uri))
    except Exception:
        total_constraint_components = 0

    try:
        # This function doesn't support graph_uri yet, use default
        most_violated_shape = virtuoso_service.get_maximum_number_of_violations_in_validation_report_for_node_shape()
    except Exception:
        most_violated_shape = {"nodeShape": "No data", "violationCount": 0}

    shapes_data = []
    for shape in all_shapes:
        try:
            violations = virtuoso_service.get_number_of_violations_for_node_shape(shape, validation_graph_uri)
        except Exception:
            violations = 0

        try:
            # This function doesn't support graph_uri yet, use default
            property_shapes = virtuoso_service.get_number_of_property_shapes_for_node_shape(shape)
        except Exception:
            property_shapes = 0

        try:
            focus_nodes = virtuoso_service.get_number_of_affected_focus_nodes_for_node_shape(shape, validation_graph_uri)
        except Exception:
            focus_nodes = 0

        try:
            property_paths = virtuoso_service.get_number_of_property_paths_for_node_shape(shape, validation_graph_uri)
        except Exception:
            property_paths = 0

        try:
            # This function doesn't support graph_uri yet, use default
            most_violated_constraint = virtuoso_service.get_most_violated_constraint_for_node_shape(shape)
        except Exception:
            most_violated_constraint = "No data"

        shapes_data.append({
            'name': shape,
            'violations': violations,
            'propertyShapes': property_shapes,
            'focusNodes': focus_nodes,
            'propertyPaths': property_paths,
            'mostViolatedConstraint': most_violated_constraint,
            'violationToConstraintRatio': violations / property_shapes if property_shapes > 0 else 0
        })

    # Get histogram data with error handling
    try:
        shape_histogram_data = virtuoso_service.get_violations_per_shape_histogram(validation_graph_uri)
    except Exception:
        shape_histogram_data = []

    try:
        path_histogram_data = virtuoso_service.get_violations_per_path_histogram(validation_graph_uri)
    except Exception:
        path_histogram_data = []

    try:
        focus_node_histogram_data = virtuoso_service.get_violations_per_focus_node_histogram(validation_graph_uri)
    except Exception:
        focus_node_histogram_data = []

    try:
        constraint_component_histogram_data = virtuoso_service.get_violations_per_constraint_component_histogram(validation_graph_uri)
    except Exception:
        constraint_component_histogram_data = []

    # Get actual most violated items
    try:
        most_violated_path = virtuoso_service.get_most_violated_path(validation_graph_uri)
    except Exception:
        most_violated_path = ""

    try:
        most_violated_focus_node = virtuoso_service.get_most_violated_focus_node(validation_graph_uri)
    except Exception:
        most_violated_focus_node = ""

    try:
        most_violated_constraint_component = virtuoso_service.get_most_violated_constraint_component(validation_graph_uri)
    except Exception:
        most_violated_constraint_component = ""

    dashboard_data = {
        "tags": [
            { "title": "Total Violations", "value": total_violations, "titleMaxViolated": "", "maxViolated": "" },
            { "title": "Violated Node Shapes", "value": f"{violated_node_shapes}/{violated_node_shapes}", "titleMaxViolated": "Most Violated Node Shape", "maxViolated": most_violated_shape.get('nodeShape', 'No data') },
            { "title": "Violated Paths", "value": f"{total_paths}/{total_paths}", "titleMaxViolated": "Most Violated Path", "maxViolated": most_violated_path },
            { "title": "Violated Focus Nodes", "value": total_focus_nodes, "titleMaxViolated": "Most Violated Focus Node", "maxViolated": most_violated_focus_node },
            { "title": "Violated Constraint Components", "value": f"{total_constraint_components}/{total_constraint_components}", "titleMaxViolated": "Most Violated Constraint Component", "maxViolated": most_violated_constraint_component },
        ],
        "shapes": shapes_data,
        "shapeHistogramData": shape_histogram_data,
        "pathHistogramData": path_histogram_data,
        "focusNodeHistogramData": focus_node_histogram_data,
        "constraintComponentHistogramData": constraint_component_histogram_data,
    }
    return dashboard_data
