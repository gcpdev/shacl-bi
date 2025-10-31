import random
from . import virtuoso_service
import config

import numpy as np


def _create_histogram(data, color, label="Violations"):
    if not data:
        return {
            "labels": [],
            "datasets": [
                {
                    "label": label,
                    "data": [],
                    "backgroundColor": color,
                    "borderColor": color,
                    "borderWidth": 1,
                },
            ],
        }

    values = [item[1] for item in data]
    bins = np.histogram_bin_edges(values, bins="auto")
    hist, _ = np.histogram(values, bins=bins)

    return {
        "labels": [f"{int(bins[i])}-{int(bins[i+1])}" for i in range(len(bins) - 1)],
        "datasets": [
            {
                "label": label,
                "data": hist.tolist(),
                "backgroundColor": color,
                "borderColor": color,
                "borderWidth": 1,
            },
        ],
    }


def get_main_content_data(directory_path, shapes_graph_name, validation_report_name):
    config.update_graphs(shapes_graph_name, validation_report_name)

    total_violations = virtuoso_service.get_number_of_violations_in_validation_report()
    shapes_info = virtuoso_service.get_number_of_shapes_in_shapes_graph()
    violated_shapes = virtuoso_service.get_all_shapes_names()
    violated_paths = virtuoso_service.get_all_property_path_names()
    violated_focus_nodes = virtuoso_service.get_all_focus_node_names()
    violated_constraint_components = (
        virtuoso_service.get_all_constraint_components_names()
    )

    most_violated_shape = virtuoso_service.get_most_violated_shape()
    most_violated_path = virtuoso_service.get_most_violated_path()
    most_violated_focus_node = virtuoso_service.get_most_violated_focus_node()
    most_violated_constraint_component = (
        virtuoso_service.get_most_violated_constraint_component()
    )

    tags = [
        {
            "title": "Total Violations",
            "value": total_violations,
            "titleMaxViolated": "",
            "maxViolated": "",
        },
        {
            "title": "Violated Node Shapes",
            "value": f"{len(violated_shapes)}/{shapes_info['nodeShapes']}",
            "titleMaxViolated": "Most Violated Node Shape",
            "maxViolated": most_violated_shape,
        },
        {
            "title": "Violated Paths",
            "value": f" {len(violated_paths)}/{shapes_info['propertyShapes']}",
            "titleMaxViolated": "Most Violated Path",
            "maxViolated": most_violated_path,
        },
        {
            "title": "Violated Focus Nodes",
            "value": len(violated_focus_nodes),
            "titleMaxViolated": "Most Violated Focus Node",
            "maxViolated": most_violated_focus_node,
        },
        {
            "title": "Violated Constraint Components",
            "value": f"{len(violated_constraint_components)}/5",
            "titleMaxViolated": "Most Violated Constraint Component",
            "maxViolated": most_violated_constraint_component,
        },
    ]

    shape_histogram_data = _create_histogram(
        virtuoso_service.get_violations_per_shape_histogram(), "rgba(154, 188, 228)"
    )
    path_histogram_data = _create_histogram(
        virtuoso_service.get_violations_per_path_histogram(), "rgba(94, 148, 212, 1)"
    )
    focus_node_histogram_data = _create_histogram(
        virtuoso_service.get_violations_per_focus_node_histogram(),
        "rgba(22, 93, 177, 1)",
    )
    constraint_component_histogram_data = _create_histogram(
        virtuoso_service.get_violations_per_constraint_component_histogram(),
        "rgba(10, 45, 87)",
    )

    return {
        "tags": tags,
        "shapeHistogramData": shape_histogram_data,
        "pathHistogramData": path_histogram_data,
        "focusNodeHistogramData": focus_node_histogram_data,
        "constraintComponentHistogramData": constraint_component_histogram_data,
    }
