import os
import sys
import logging
from SPARQLWrapper import SPARQLWrapper, JSON, DIGEST
from rdflib import Graph

import config
from .xpshacl_engine.xpshacl_architecture import ConstraintViolation, ViolationType

logging.basicConfig(filename='virtuoso.log', level=logging.DEBUG)

def execute_sparql_query(query, format=JSON):
    logging.debug(f"Endpoint URL: {config.ENDPOINT_URL}")
    logging.debug(f"Username: {config.USERNAME}")
    logging.debug(f"Auth required: {config.AUTH_REQUIRED}")
    sparql = SPARQLWrapper(config.ENDPOINT_URL)
    if config.AUTH_REQUIRED:
        sparql.setCredentials(config.USERNAME, config.PASSWORD)
    sparql.setHTTPAuth(DIGEST)
    sparql.setQuery(query)
    sparql.setReturnFormat(format)
    return sparql.query().convert()

def execute_sparql_update(query):
    logging.debug(f"Endpoint URL: {config.ENDPOINT_URL}")
    logging.debug(f"Username: {config.USERNAME}")
    logging.debug(f"Auth required: {config.AUTH_REQUIRED}")
    sparql = SPARQLWrapper(config.ENDPOINT_URL)
    if config.AUTH_REQUIRED:
        sparql.setCredentials(config.USERNAME, config.PASSWORD)
    sparql.setHTTPAuth(DIGEST)
    sparql.setQuery(query)
    sparql.setMethod('POST')
    sparql.query()

def load_graph(graph: Graph, graph_uri: str):
    # Clear the graph first
    clear_query = f"CLEAR GRAPH <{graph_uri}>"
    execute_sparql_update(clear_query)

    # Insert the new data
    nt_data = graph.serialize(format='nt')
    insert_query = f"""
        INSERT DATA {{
            GRAPH <{graph_uri}> {{
                {nt_data}
            }}
        }}
    """
    execute_sparql_update(insert_query)

def get_all_shapes_names(graph_uri=config.VALIDATION_REPORT_URI):
    query = f"""
        SELECT DISTINCT ?shape
        FROM <{graph_uri}>
        WHERE {{
            ?violation <http://www.w3.org/ns/shacl#sourceShape> ?shape .
        }}
    """
    results = execute_sparql_query(query)
    return [result["shape"]["value"] for result in results["results"]["bindings"]]

def get_all_focus_node_names(graph_uri=config.VALIDATION_REPORT_URI):
    query = f"""
        SELECT DISTINCT ?focusNode
        FROM <{graph_uri}>
        WHERE {{
            ?violation <http://www.w3.org/ns/shacl#focusNode> ?focusNode .
        }}
    """
    results = execute_sparql_query(query)
    return [result["focusNode"]["value"] for result in results["results"]["bindings"]]

def get_all_property_path_names(graph_uri=config.VALIDATION_REPORT_URI):
    query = f"""
        SELECT DISTINCT ?propertyPath
        FROM <{graph_uri}>
        WHERE {{
            ?violation <http://www.w3.org/ns/shacl#resultPath> ?propertyPath .
        }}
    """
    results = execute_sparql_query(query)
    return [result["propertyPath"]["value"] for result in results["results"]["bindings"]]

def get_all_constraint_components_names(graph_uri=config.VALIDATION_REPORT_URI):
    query = f"""
        SELECT DISTINCT ?constraintComponent
        FROM <{graph_uri}>
        WHERE {{
            ?violation <http://www.w3.org/ns/shacl#sourceConstraintComponent> ?constraintComponent .
        }}
    """
    results = execute_sparql_query(query)
    return [result["constraintComponent"]["value"] for result in results["results"]["bindings"]]

def get_violations_for_shape_name(shape_name, graph_uri=config.VALIDATION_REPORT_URI):
    if isinstance(shape_name, dict) and "shape" in shape_name:
        shape_name = shape_name["shape"]

    if not isinstance(shape_name, str):
        raise ValueError("Invalid input: shape_name must be a string or a JSON object with a 'shape' key.")

    query = f"""
        SELECT ?focusNode ?resultMessage ?resultPath ?resultSeverity ?sourceConstraintComponent ?value
        FROM <{graph_uri}>
        WHERE {{
            ?violation a <http://www.w3.org/ns/shacl#ValidationResult> ;
                       <http://www.w3.org/ns/shacl#sourceShape> <{shape_name}> ;
                       <http://www.w3.org/ns/shacl#focusNode> ?focusNode ;
                       <http://www.w3.org/ns/shacl#resultMessage> ?resultMessage ;
                       <http://www.w3.org/ns/shacl#resultPath> ?resultPath ;
                       <http://www.w3.org/ns/shacl#resultSeverity> ?resultSeverity ;
                       <http://www.w3.org/ns/shacl#sourceConstraintComponent> ?sourceConstraintComponent ;
                       <http://www.w3.org/ns/shacl#value> ?value .
        }}
    """
    results = execute_sparql_query(query)
    violations = []
    for result in results["results"]["bindings"]:
        violations.append(ConstraintViolation(
            focus_node=result["focusNode"]["value"],
            shape_id=shape_name,
            constraint_id=result["sourceConstraintComponent"]["value"],
            violation_type=ViolationType.OTHER, # This needs to be determined from the constraint component
            property_path=result["resultPath"]["value"],
            value=result["value"]["value"],
            message=result["resultMessage"]["value"],
            severity=result["resultSeverity"]["value"],
        ))
    return violations

def get_number_of_shapes_in_shapes_graph(graph_uri=config.SHAPES_GRAPH_URI):
    query = f"""
        SELECT 
            (COUNT(DISTINCT ?nodeShape) AS ?nodeShapesCount)
            (COUNT(DISTINCT ?propertyShape) AS ?propertyShapesCount)
        FROM <{graph_uri}>
        WHERE {{
            OPTIONAL {{ ?nodeShape a <http://www.w3.org/ns/shacl#NodeShape> . }}
            OPTIONAL {{ ?shape <http://www.w3.org/ns/shacl#property> ?propertyShape . }}
        }}
    """
    results = execute_sparql_query(query)
    node_shapes_count = int(results["results"]["bindings"][0]["nodeShapesCount"]["value"])
    property_shapes_count = int(results["results"]["bindings"][0]["propertyShapesCount"]["value"])
    return {
        "nodeShapes": node_shapes_count,
        "propertyShapes": property_shapes_count
    }

def get_number_of_violations_in_validation_report(graph_uri=config.VALIDATION_REPORT_URI):
    query = f"""
        SELECT (COUNT(?violation) AS ?violationCount)
        FROM <{graph_uri}>
        WHERE {{
            ?violation a <http://www.w3.org/ns/shacl#ValidationResult> .
        }}
    """
    results = execute_sparql_query(query)
    return int(results["results"]["bindings"][0]["violationCount"]["value"])

def map_property_shapes_to_node_shapes(validation_report_uri=config.VALIDATION_REPORT_URI, shapes_graph_uri=config.SHAPES_GRAPH_URI):
    query = f"""
        SELECT DISTINCT ?propertyShape ?nodeShape
        FROM <{validation_report_uri}>
        FROM <{shapes_graph_uri}>
        WHERE {{
            ?violation <http://www.w3.org/ns/shacl#sourceShape> ?propertyShape .
            ?nodeShape <http://www.w3.org/ns/shacl#property> ?propertyShape .
        }}
    """
    results = execute_sparql_query(query)
    return [
        {result["propertyShape"]["value"]: result["nodeShape"]["value"]}
        for result in results["results"]["bindings"]
    ]

def get_shape_from_shapes_graph(node_shape_names):
    node_shapes_values = " ".join([f"<{uri}>" for uri in node_shape_names])
    query = f"""
        SELECT DISTINCT ?subject ?predicate ?object
        FROM <{config.SHAPES_GRAPH_URI}>
        WHERE {{
            VALUES ?subject {{ {node_shapes_values} }}
            ?subject ?predicate ?object .
        }}
    """
    node_shape_results = execute_sparql_query(query)

    shape_details = {}
    for result in node_shape_results["results"]["bindings"]:
        subject = result["subject"]["value"]
        predicate = result["predicate"]["value"]
        object_value = result["object"]["value"]

        if subject not in shape_details:
            shape_details[subject] = {
                "triples": [],
                "propertyShapes": {}
            }

        shape_details[subject]["triples"].append({
            "predicate": predicate,
            "object": object_value
        })

    property_shapes = {triple["object"] for shape in shape_details.values() for triple in shape["triples"] if triple["predicate"] == "http://www.w3.org/ns/shacl#property"}

    for property_shape in property_shapes:
        query = f"""
            SELECT DISTINCT ?predicate ?object
            FROM <{config.SHAPES_GRAPH_URI}>
            WHERE {{
                <{property_shape}> ?predicate ?object .
            }}
        """
        property_shape_results = execute_sparql_query(query)

        for result in property_shape_results["results"]["bindings"]:
            predicate = result["predicate"]["value"]
            object_value = result["object"]["value"]

            for node_shape, details in shape_details.items():
                if property_shape not in details["propertyShapes"]:
                    details["propertyShapes"][property_shape] = []

                details["propertyShapes"][property_shape].append({
                    "predicate": predicate,
                    "object": object_value
                })

    return shape_details

def get_number_of_property_shapes_for_node_shape(shape_name):
    query = f"""
        SELECT (COUNT(DISTINCT ?propertyShape) AS ?propertyShapeCount)
        FROM <{config.SHAPES_GRAPH_URI}>
        WHERE {{
            <{shape_name}> <http://www.w3.org/ns/shacl#property> ?propertyShape .
        }}
    """
    results = execute_sparql_query(query)
    return int(results["results"]["bindings"][0]["propertyShapeCount"]["value"])

def get_most_violated_constraint_for_node_shape(shape_name):
    sparql = SPARQLWrapper(config.ENDPOINT_URL)
    if config.AUTH_REQUIRED:
        sparql.setCredentials(config.USERNAME, config.PASSWORD)
    sparql.setHTTPAuth(DIGEST)
    sparql.setQuery(f"""
        SELECT DISTINCT ?propertyShape
        FROM <{config.SHAPES_GRAPH_URI}>
        WHERE {{
            <{shape_name}> <http://www.w3.org/ns/shacl#property> ?propertyShape .
        }}
    """)
    sparql.setReturnFormat(JSON)
    shapes_results = sparql.query().convert()

    property_shapes = [result["propertyShape"]["value"] for result in shapes_results["results"]["bindings"]]

    if not property_shapes:
        return ""

    property_shapes_values = " ".join([f"<{uri}>" for uri in property_shapes])

    sparql.setQuery(f"""
        SELECT ?constraintComponent (COUNT(?violation) AS ?violationCount)
        FROM <{config.VALIDATION_REPORT_URI}>
        WHERE {{
            ?violation <http://www.w3.org/ns/shacl#sourceShape> ?propertyShape ;
                       <http://www.w3.org/ns/shacl#sourceConstraintComponent> ?constraintComponent .
            VALUES ?propertyShape {{ {property_shapes_values} }}
        }}
        GROUP BY ?constraintComponent
        ORDER BY DESC(?violationCount)
        LIMIT 1
    """)
    validation_results = sparql.query().convert()

    if validation_results["results"]["bindings"]:
        return validation_results["results"]["bindings"][0]["constraintComponent"]["value"]

    return ""

def get_maximum_number_of_violations_in_validation_report_for_node_shape():
    sparql = SPARQLWrapper(config.ENDPOINT_URL)
    if config.AUTH_REQUIRED:
        sparql.setCredentials(config.USERNAME, config.PASSWORD)
    sparql.setHTTPAuth(DIGEST)
    sparql.setQuery(f"""
        SELECT DISTINCT ?nodeShape ?propertyShape
        FROM <{config.SHAPES_GRAPH_URI}>
        WHERE {{
            ?nodeShape a <http://www.w3.org/ns/shacl#NodeShape> ;
                       <http://www.w3.org/ns/shacl#property> ?propertyShape .
        }}
    """)
    sparql.setReturnFormat(JSON)
    node_shapes_results = sparql.query().convert()

    node_shapes_map = {}
    for result in node_shapes_results["results"]["bindings"]:
        node_shape = result["nodeShape"]["value"]
        property_shape = result["propertyShape"]["value"]
        if node_shape not in node_shapes_map:
            node_shapes_map[node_shape] = []
        node_shapes_map[node_shape].append(property_shape)

    violation_counts = {}
    for node_shape, property_shapes in node_shapes_map.items():
        property_shapes_values = " ".join([f"<{uri}>" for uri in property_shapes])
        sparql.setQuery(f"""
            SELECT (COUNT(?violation) AS ?violationCount)
            FROM <{config.VALIDATION_REPORT_URI}>
            WHERE {{
                ?violation <http://www.w3.org/ns/shacl#sourceShape> ?propertyShape .
                VALUES ?propertyShape {{ {property_shapes_values} }}
            }}
        """)
        validation_results = sparql.query().convert()

        violation_count = int(validation_results["results"]["bindings"][0]["violationCount"]["value"])
        violation_counts[node_shape] = violation_count

    if violation_counts:
        max_node_shape = max(violation_counts, key=violation_counts.get)
        return {"nodeShape": max_node_shape, "violationCount": violation_counts[max_node_shape]}

    return {"nodeShape": "", "violationCount": 0}

def get_average_number_of_violations_in_validation_report_for_node_shape():
    sparql = SPARQLWrapper(config.ENDPOINT_URL)
    if config.AUTH_REQUIRED:
        sparql.setCredentials(config.USERNAME, config.PASSWORD)
    sparql.setHTTPAuth(DIGEST)
    sparql.setQuery(f"""
        SELECT DISTINCT ?nodeShape ?propertyShape
        FROM <{config.SHAPES_GRAPH_URI}>
        WHERE {{
            ?nodeShape a <http://www.w3.org/ns/shacl#NodeShape> ;
                       <http://www.w3.org/ns/shacl#property> ?propertyShape .
        }}
    """)
    sparql.setReturnFormat(JSON)
    node_shapes_results = sparql.query().convert()

    node_shapes_map = {}
    for result in node_shapes_results["results"]["bindings"]:
        node_shape = result["nodeShape"]["value"]
        property_shape = result["propertyShape"]["value"]
        if node_shape not in node_shapes_map:
            node_shapes_map[node_shape] = []
        node_shapes_map[node_shape].append(property_shape)

    total_violations = 0
    total_node_shapes = len(node_shapes_map)

    for node_shape, property_shapes in node_shapes_map.items():
        property_shapes_values = " ".join([f"<{uri}>" for uri in property_shapes])
        sparql.setQuery(f"""
            SELECT (COUNT(?violation) AS ?violationCount)
            FROM <{config.VALIDATION_REPORT_URI}>
            WHERE {{
                ?violation <http://www.w3.org/ns/shacl#sourceShape> ?propertyShape .
                VALUES ?propertyShape {{ {property_shapes_values} }}
            }}
        """)
        validation_results = sparql.query().convert()

        violation_count = int(validation_results["results"]["bindings"][0]["violationCount"]["value"])
        total_violations += violation_count

    if total_node_shapes == 0:
        return 0.0

    average_violations = total_violations / total_node_shapes
    return round(average_violations, 2)

def get_violations_per_shape_histogram(graph_uri=config.VALIDATION_REPORT_URI):
    query = f"""
        SELECT ?shape (COUNT(?violation) AS ?violationCount)
        FROM <{graph_uri}>
        WHERE {{
            ?violation a <http://www.w3.org/ns/shacl#ValidationResult> ;
                       <http://www.w3.org/ns/shacl#sourceShape> ?shape .
        }}
        GROUP BY ?shape
    """
    results = execute_sparql_query(query)
    return [(result["shape"]["value"], int(result["violationCount"]["value"])) for result in results["results"]["bindings"]]

def get_violations_per_path_histogram(graph_uri=config.VALIDATION_REPORT_URI):
    query = f"""
        SELECT ?path (COUNT(?violation) AS ?violationCount)
        FROM <{graph_uri}>
        WHERE {{
            ?violation a <http://www.w3.org/ns/shacl#ValidationResult> ;
                       <http://www.w3.org/ns/shacl#resultPath> ?path .
        }}
        GROUP BY ?path
    """
    results = execute_sparql_query(query)
    return [(result["path"]["value"], int(result["violationCount"]["value"])) for result in results["results"]["bindings"]]

def get_violations_per_focus_node_histogram(graph_uri=config.VALIDATION_REPORT_URI):
    query = f"""
        SELECT ?focusNode (COUNT(?violation) AS ?violationCount)
        FROM <{graph_uri}>
        WHERE {{
            ?violation a <http://www.w3.org/ns/shacl#ValidationResult> ;
                       <http://www.w3.org/ns/shacl#focusNode> ?focusNode .
        }}
        GROUP BY ?focusNode
    """
    results = execute_sparql_query(query)
    return [(result["focusNode"]["value"], int(result["violationCount"]["value"])) for result in results["results"]["bindings"]]

def get_violations_per_constraint_component_histogram(graph_uri=config.VALIDATION_REPORT_URI):
    query = f"""
        SELECT ?constraint (COUNT(?violation) AS ?violationCount)
        FROM <{graph_uri}>
        WHERE {{
            ?violation a <http://www.w3.org/ns/shacl#ValidationResult> ;
                       <http://www.w3.org/ns/shacl#sourceConstraintComponent> ?constraint .
        }}
        GROUP BY ?constraint
    """
    results = execute_sparql_query(query)
    return [(result["constraint"]["value"], int(result["violationCount"]["value"])) for result in results["results"]["bindings"]]

def get_most_violated_shape(graph_uri=config.VALIDATION_REPORT_URI):
    query = f"""
        SELECT ?shape (COUNT(?violation) AS ?violationCount)
        FROM <{graph_uri}>
        WHERE {{
            ?violation a <http://www.w3.org/ns/shacl#ValidationResult> ;
                       <http://www.w3.org/ns/shacl#sourceShape> ?shape .
        }}
        GROUP BY ?shape
        ORDER BY DESC(?violationCount)
        LIMIT 1
    """
    results = execute_sparql_query(query)
    if results["results"]["bindings"]:
        return results["results"]["bindings"][0]["shape"]["value"]
    return ""

def get_most_violated_path(graph_uri=config.VALIDATION_REPORT_URI):
    query = f"""
        SELECT ?path (COUNT(?violation) AS ?violationCount)
        FROM <{graph_uri}>
        WHERE {{
            ?violation a <http://www.w3.org/ns/shacl#ValidationResult> ;
                       <http://www.w3.org/ns/shacl#resultPath> ?path .
        }}
        GROUP BY ?path
        ORDER BY DESC(?violationCount)
        LIMIT 1
    """
    results = execute_sparql_query(query)
    if results["results"]["bindings"]:
        return results["results"]["bindings"][0]["path"]["value"]
    return ""

def get_most_violated_focus_node(graph_uri=config.VALIDATION_REPORT_URI):
    query = f"""
        SELECT ?focusNode (COUNT(?violation) AS ?violationCount)
        FROM <{graph_uri}>
        WHERE {{
            ?violation a <http://www.w3.org/ns/shacl#ValidationResult> ;
                       <http://www.w3.org/ns/shacl#focusNode> ?focusNode .
        }}
        GROUP BY ?focusNode
        ORDER BY DESC(?violationCount)
        LIMIT 1
    """
    results = execute_sparql_query(query)
    if results["results"]["bindings"]:
        return results["results"]["bindings"][0]["focusNode"]["value"]
    return ""

def get_most_violated_constraint_component(graph_uri=config.VALIDATION_REPORT_URI):
    query = f"""
        SELECT ?constraint (COUNT(?violation) AS ?violationCount)
        FROM <{graph_uri}>
        WHERE {{
            ?violation a <http://www.w3.org/ns/shacl#ValidationResult> ;
                       <http://www.w3.org/ns/shacl#sourceConstraintComponent> ?constraint .
        }}
        GROUP BY ?constraint
        ORDER BY DESC(?violationCount)
        LIMIT 1
    """
    results = execute_sparql_query(query)
    if results["results"]["bindings"]:
        return results["results"]["bindings"][0]["constraint"]["value"]
    return ""