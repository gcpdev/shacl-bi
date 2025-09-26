"""Virtuoso integration + knowledge graph."""

from SPARQLWrapper import SPARQLWrapper, JSON
from . import config
from .llm import generate_severity
import uuid

def get_db():
    """Returns a SPARQLWrapper instance for the configured Virtuoso endpoint."""
    sparql = SPARQLWrapper(config.VIRTUOSO_ENDPOINT)
    return sparql

def execute_query(query, method='SELECT'):
    """
    Executes a SPARQL query against the Virtuoso database.

    Args:
        query (str): The SPARQL query to be executed.
        method (str): The query method ('SELECT' or 'UPDATE').

    Returns:
        The query results, or None if the query fails.
    """
    try:
        sparql = get_db()
        sparql.setQuery(query)
        if method == 'SELECT':
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            return results
        elif method == 'UPDATE':
            sparql.method = 'POST'
            sparql.query()
            return None
    except Exception as e:
        print(f"Error executing query: {e}")
        return None

def load_ontology(ontology_file, graph_uri):
    """
    Loads an ontology file into the specified graph in Virtuoso.

    Args:
        ontology_file (str): The path to the ontology file.
        graph_uri (str): The URI of the graph to load the ontology into.
    """
    with open(ontology_file, 'r') as f:
        ontology_data = f.read()
    
    query = f"""
    INSERT DATA {{ GRAPH <{graph_uri}> {{ {ontology_data} }} }}
    """

    execute_query(query, method='UPDATE')

def insert_validation_report(results_graph, graph_uri):
    """
    Inserts the validation report graph into the specified graph in Virtuoso.

    Args:
        results_graph (rdflib.Graph): The validation report graph.
        graph_uri (str): The URI of the graph to load the report into.
    """
    report_data = results_graph.serialize(format='turtle')
    query = f"""
    INSERT DATA {{ GRAPH <{graph_uri}> {{ {report_data} }} }}
    """
    execute_query(query, method='UPDATE')

def create_violation_instances(validation_graph_uri, violation_kg_graph_uri):
    """
    Creates violation instances in the Violation Knowledge Graph for each validation result.
    This function is less efficient as it iterates over each validation result to generate a severity level.
    """
    query = f"""
    PREFIX sh: <http://www.w3.org/ns/shacl#>

    SELECT ?validationResult
    WHERE {{
        GRAPH <{validation_graph_uri}> {{
            ?validationResult a sh:ValidationResult .
        }}
    }}
    """
    results = execute_query(query)
    if not results or not results['results']['bindings']:
        return

    for r in results['results']['bindings']:
        validation_result_uri = r['validationResult']['value']
        severity = generate_severity(validation_result_uri)
        violation_id = str(uuid.uuid4())

        insert_query = f"""
        PREFIX vio: <http://ex.org/Violation#>
        PREFIX sh: <http://www.w3.org/ns/shacl#>

        INSERT DATA {{
            GRAPH <{violation_kg_graph_uri}> {{
                <http://ex.org/Violation/{violation_id}> a vio:Violation ;
                    vio:hasValidationResult <{validation_result_uri}> ;
                    vio:hasSeverity \"{severity}\" .
            }}
        }}
        """
        execute_query(insert_query, method='UPDATE')


def get_violation_by_id(violation_id, violation_kg_graph_uri):
    """
    Retrieves a violation by its ID from the Violation Knowledge Graph.

    Args:
        violation_id (str): The ID of the violation.
        violation_kg_graph_uri (str): The URI of the violation knowledge graph.

    Returns:
        A dictionary containing the violation details, or None if not found.
    """
    query = f"""
    PREFIX vio: <http://ex.org/Violation#>
    PREFIX sh: <http://www.w3.org/ns/shacl#>

    SELECT ?p ?o ?result_p ?result_o
    WHERE {{
        GRAPH <{violation_kg_graph_uri}> {{
            <http://ex.org/Violation/{violation_id}> ?p ?o .
            OPTIONAL {{
                <http://ex.org/Violation/{violation_id}> vio:hasValidationResult ?result .
                GRAPH <{config.VALIDATION_GRAPH}> {{
                    ?result ?result_p ?result_o .
                }}
            }}
        }}
    }}
    """
    results = execute_query(query)
    if not results or not results['results']['bindings']:
        return None

    violation_details = {}
    validation_result = {}
    for r in results['results']['bindings']:
        p = r['p']['value']
        o = r['o']['value']
        violation_details[p] = o

        if 'result_p' in r and 'result_o' in r:
            result_p = r['result_p']['value']
            result_o = r['result_o']['value']
            validation_result[result_p] = result_o
            
    violation_details['validation_result'] = validation_result

    return violation_details

def get_violations_count(violation_kg_graph_uri):
    """
    Counts the total number of violations in the Violation Knowledge Graph.

    Args:
        violation_kg_graph_uri (str): The URI of the violation knowledge graph.

    Returns:
        The total number of violations.
    """
    query = f"""
    PREFIX vio: <http://ex.org/Violation#>

    SELECT (COUNT(?violation) as ?count)
    WHERE {{
        GRAPH <{violation_kg_graph_uri}> {{
            ?violation a vio:Violation .
        }}
    }}
    """
    results = execute_query(query)
    if not results or not results['results']['bindings']:
        return 0

    return int(results['results']['bindings'][0]['count']['value'])

def get_all_violations(violation_kg_graph_uri, sort_by='severity', order='desc'):
    """
    Retrieves all violations from the Violation Knowledge Graph.

    Args:
        violation_kg_graph_uri (str): The URI of the violation knowledge graph.
        sort_by (str): The property to sort by (e.g., 'severity').
        order (str): The sort order ('asc' or 'desc').

    Returns:
        A list of dictionaries, where each dictionary represents a violation.
    """
    order_clause = f"ORDER BY {order.upper()}(?{sort_by})"

    query = f"""
    PREFIX vio: <http://ex.org/Violation#>

    SELECT ?violation ?severity
    WHERE {{
        GRAPH <{violation_kg_graph_uri}> {{
            ?violation a vio:Violation ;
                vio:hasSeverity ?severity .
        }}
    }}
    {order_clause}
    """
    results = execute_query(query)
    if not results or not results['results']['bindings']:
        return []

    violations = []
    for r in results['results']['bindings']:
        violations.append({
            'id': r['violation']['value'].split('/')[-1],
            'severity': r['severity']['value']
        })

    return violations