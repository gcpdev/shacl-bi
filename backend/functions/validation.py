from rdflib import Graph
from rdflib.namespace import Namespace

# SHACL namespace
SHACL = Namespace("http://www.w3.org/ns/shacl#")
from typing import Dict, Any, List, Optional
from functions.xpshacl_engine.extended_shacl_validator import ExtendedShaclValidator
from functions import virtuoso_service
from .xpshacl_engine.xpshacl_architecture import ConstraintViolation
import config
import logging
import json
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

def validate(data_graph: Graph, shapes_graph: Graph, validation_report: Graph = None):
    if validation_report:
        # SHACL Dashboard mode: load existing validation report
        virtuoso_service.load_graph(validation_report, config.VALIDATION_REPORT_URI)
        return validation_report
    else:
        # PHOENIX mode: perform validation
        validator = ExtendedShaclValidator(shapes_graph)
        violations = validator.validate(data_graph)
        # The validation report is the results_graph from the validator
        validation_report_graph = validator.results_graph
        virtuoso_service.load_graph(validation_report_graph, config.VALIDATION_REPORT_URI)
        return validation_report_graph

def validate_data_against_shapes(data_ttl: str, shapes_ttl: str, session_id: str) -> Dict[str, Any]:
    """Validate data against shapes and return results."""
    try:
        # Parse TTL strings into graphs
        data_graph = Graph().parse(data=data_ttl, format='turtle')
        shapes_graph = Graph().parse(data=shapes_ttl, format='turtle')

        # Create validation session graph
        session_graph_uri = f"http://example.org/validation/session_{session_id}"

        # Load data and shapes into Virtuoso
        data_graph_uri = f"{session_graph_uri}/data"
        shapes_graph_uri = f"{session_graph_uri}/shapes"

        virtuoso_service.load_ttl_string(data_ttl, data_graph_uri)
        virtuoso_service.load_ttl_string(shapes_ttl, shapes_graph_uri)

        # Perform validation
        validator = ExtendedShaclValidator(shapes_graph)
        violations = validator.validate(data_graph)
        conforms = not violations

        # Store validation results
        results_graph_uri = f"{session_graph_uri}/results"
        if validator.results_graph:
            virtuoso_service.load_ttl_string(
                validator.results_graph.serialize(format='turtle'),
                results_graph_uri
            )

        # Process violations for return
        violations_data = []
        for i, violation in enumerate(violations or []):
            violations_data.append({
                'id': i,
                'focusNode': getattr(violation, 'focus_node', 'Unknown'),
                'resultPath': getattr(violation, 'property_path', 'Unknown'),
                'value': getattr(violation, 'value', 'Unknown'),
                'message': getattr(violation, 'message', 'Constraint violation'),
                'severity': getattr(violation, 'severity', 'Violation'),
                'constraintComponent': getattr(violation, 'constraint_id', 'Unknown')
            })

        validation_report = {
            'conforms': conforms,
            'violations': violations_data,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'data_graph_uri': data_graph_uri,
            'shapes_graph_uri': shapes_graph_uri,
            'results_graph_uri': results_graph_uri
        }

        return validation_report

    except Exception as e:
        logger.error(f"Error in validate_data_against_shapes: {str(e)}")
        return {
            'conforms': False,
            'violations': [],
            'error': str(e),
            'session_id': session_id
        }

def get_validation_report(session_id: str) -> Dict[str, Any]:
    """Get validation report for a session."""
    try:
        query = f"""
        SELECT ?reportUri ?conforms ?violationsCount WHERE {{
            GRAPH <http://example.org/validation/session_{session_id}> {{
                ?reportUri a <http://www.w3.org/ns/shacl#ValidationReport> .
                ?reportUri <http://www.w3.org/ns/shacl#conforms> ?conforms .
                OPTIONAL {{
                    ?reportUri <http://www.w3.org/ns/shacl#result> ?result .
                }}
                BIND(COUNT(?result) as ?violationsCount)
            }}
        }}
        """

        result = virtuoso_service.execute_sparql_query(query)
        bindings = result.get('results', {}).get('bindings', [])

        if bindings:
            binding = bindings[0]
            return {
                'reportUri': binding.get('reportUri', {}).get('value', ''),
                'conforms': binding.get('conforms', {}).get('value', '') == 'true',
                'violationsCount': int(binding.get('violationsCount', {}).get('value', 0))
            }
        else:
            return {'error': 'Validation report not found'}

    except Exception as e:
        logger.error(f"Error getting validation report: {str(e)}")
        return {'error': str(e)}

def create_validation_session(shapes_graph: str, data_graph: str) -> Dict[str, Any]:
    """Create a new validation session."""
    try:
        session_id = str(uuid.uuid4())
        session_graph_uri = f"http://example.org/validation/session_{session_id}"

        # Create session metadata
        update_query = f"""
        INSERT DATA {{
            GRAPH <{session_graph_uri}> {{
                <{session_graph_uri}> a <http://xpshacl.org/#ValidationSession> .
                <{session_graph_uri}> <http://xpshacl.org/#sessionId> "{session_id}" .
                <{session_graph_uri}> <http://xpshacl.org/#createdAt> "{datetime.now().isoformat()}"^^xsd:dateTime .
                <{session_graph_uri}> <http://xpshacl.org/#shapesGraph> <{shapes_graph}> .
                <{session_graph_uri}> <http://xpshacl.org/#dataGraph> <{data_graph}> .
                <{session_graph_uri}> <http://xpshacl.org/#status> "created" .
            }}
        }}
        """

        virtuoso_service.execute_sparql_update(update_query)

        return {
            'sessionId': session_id,
            'graphUri': session_graph_uri,
            'status': 'created',
            'createdAt': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error creating validation session: {str(e)}")
        return {'error': str(e)}

def validate_with_config(data_graph: str, shapes_graph: str, config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Validate with custom configuration."""
    try:
        session_id = str(uuid.uuid4())

        # Apply configuration
        severity_level = config_dict.get('severity_level', 'Violation')
        include_rdfs = config_dict.get('include_rdfs', False)
        enable_inference = config_dict.get('enable_inference', True)
        abort_on_first = config_dict.get('abort_on_first', False)

        # Perform validation with configuration
        validation_result = validate_data_against_shapes(
            virtuoso_service.get_graph_content(data_graph),
            virtuoso_service.get_graph_content(shapes_graph),
            session_id
        )

        # Filter violations by severity if specified
        if severity_level != 'Violation':
            validation_result['violations'] = [
                v for v in validation_result['violations']
                if v.get('severity') == severity_level
            ]

        validation_result['configuration'] = config_dict

        return validation_result

    except Exception as e:
        logger.error(f"Error in validate_with_config: {str(e)}")
        return {
            'violations': [],
            'configuration': config_dict,
            'error': str(e)
        }

def get_validation_statistics() -> Dict[str, Any]:
    """Get validation statistics."""
    try:
        query = """
        SELECT (COUNT(?validation) as ?totalValidations)
               (COUNT(?successful) as ?successfulValidations)
               (COUNT(?failed) as ?failedValidations) WHERE {
            ?validation a <http://xpshacl.org/#ValidationExecution> .
            OPTIONAL {
                ?validation <http://xpshacl.org/#status> "completed" .
                ?validation <http://xpshacl.org/#conforms> "true"^^xsd:boolean .
                BIND(?validation as ?successful)
            }
            OPTIONAL {
                ?validation <http://xpshacl.org/#status> "completed" .
                ?validation <http://xpshacl.org/#conforms> "false"^^xsd:boolean .
                BIND(?validation as ?failed)
            }
        }
        """

        result = virtuoso_service.execute_sparql_query(query)
        bindings = result.get('results', {}).get('bindings', [])

        if bindings:
            binding = bindings[0]
            total = int(binding.get('totalValidations', {}).get('value', 0))
            successful = int(binding.get('successfulValidations', {}).get('value', 0))
            failed = int(binding.get('failedValidations', {}).get('value', 0))

            success_rate = successful / total if total > 0 else 0.0

            return {
                'totalValidations': total,
                'successfulValidations': successful,
                'failedValidations': failed,
                'successRate': success_rate
            }
        else:
            return {
                'totalValidations': 0,
                'successfulValidations': 0,
                'failedValidations': 0,
                'successRate': 0.0
            }

    except Exception as e:
        logger.error(f"Error getting validation statistics: {str(e)}")
        return {
            'totalValidations': 0,
            'successfulValidations': 0,
            'failedValidations': 0,
            'successRate': 0.0
        }

def batch_validate(datasets: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Validate multiple datasets."""
    results = []

    for dataset in datasets:
        try:
            data_graph = dataset.get('data_graph')
            shapes_graph = dataset.get('shapes_graph')

            if not data_graph or not shapes_graph:
                results.append({'error': 'Missing data_graph or shapes_graph'})
                continue

            session_id = str(uuid.uuid4())
            result = validate_data_against_shapes(
                virtuoso_service.get_graph_content(data_graph),
                virtuoso_service.get_graph_content(shapes_graph),
                session_id
            )

            result['dataset'] = dataset
            results.append(result)

        except Exception as e:
            logger.error(f"Error in batch validation: {str(e)}")
            results.append({
                'dataset': dataset,
                'error': str(e),
                'violations': []
            })

    return results

def get_validation_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Get validation history."""
    try:
        query = f"""
        SELECT ?validationId ?timestamp ?dataGraph ?shapesGraph ?violationsFound WHERE {{
            ?validation a <http://xpshacl.org/#ValidationExecution> .
            ?validation <http://xpshacl.org/#validationId> ?validationId .
            ?validation <http://xpshacl.org/#timestamp> ?timestamp .
            ?validation <http://xpshacl.org/#dataGraph> ?dataGraph .
            ?validation <http://xpshacl.org/#shapesGraph> ?shapesGraph .
            ?validation <http://xpshacl.org/#violationsFound> ?violationsFound .
        }}
        ORDER BY DESC(?timestamp)
        LIMIT {limit}
        """

        result = virtuoso_service.execute_sparql_query(query)
        bindings = result.get('results', {}).get('bindings', [])

        history = []
        for binding in bindings:
            history.append({
                'validationId': binding.get('validationId', {}).get('value', ''),
                'timestamp': binding.get('timestamp', {}).get('value', ''),
                'dataGraph': binding.get('dataGraph', {}).get('value', ''),
                'shapesGraph': binding.get('shapesGraph', {}).get('value', ''),
                'violationsFound': int(binding.get('violationsFound', {}).get('value', 0))
            })

        return history

    except Exception as e:
        logger.error(f"Error getting validation history: {str(e)}")
        return []

def compare_validations(validation1: Dict[str, Any], validation2: Dict[str, Any]) -> Dict[str, Any]:
    """Compare two validation results."""
    try:
        violations1 = validation1.get('violations', 0) if isinstance(validation1.get('violations'), int) else len(validation1.get('violations', []))
        violations2 = validation2.get('violations', 0) if isinstance(validation2.get('violations'), int) else len(validation2.get('violations', []))

        violation_difference = violations1 - violations2
        improvement = violation_difference < 0

        conforms1 = validation1.get('conforms', False)
        conforms2 = validation2.get('conforms', False)

        return {
            'improvement': improvement,
            'violation_difference': violation_difference,
            'violations_before': violations1,
            'violations_after': violations2,
            'conforms_before': conforms1,
            'conforms_after': conforms2,
            'status_improvement': conforms2 and not conforms1
        }

    except Exception as e:
        logger.error(f"Error comparing validations: {str(e)}")
        return {'error': str(e)}

def validate_shacl_syntax(shapes_ttl: str) -> Dict[str, Any]:
    """Validate SHACL shapes syntax."""
    try:
        shapes_graph = Graph().parse(data=shapes_ttl, format='turtle')

        # Check for SHACL shapes
        shapes_query = """
        SELECT (COUNT(?shape) as ?shapeCount) WHERE {
            ?shape a <http://www.w3.org/ns/shacl#NodeShape> .
        }
        """

        result = virtuoso_service.execute_sparql_query(shapes_query)
        shape_count = int(result.get('results', {}).get('bindings', [{}])[0].get('shapeCount', {}).get('value', 0))

        return {
            'valid': True,
            'errors': [],
            'shapeCount': shape_count,
            'triplesCount': len(shapes_graph)
        }

    except Exception as e:
        return {
            'valid': False,
            'errors': [str(e)],
            'shapeCount': 0,
            'triplesCount': 0
        }

def validate_rdf_syntax(data_ttl: str) -> Dict[str, Any]:
    """Validate RDF data syntax."""
    try:
        data_graph = Graph().parse(data=data_ttl, format='turtle')

        return {
            'valid': True,
            'format': 'turtle',
            'triples_count': len(data_graph),
            'errors': []
        }

    except Exception as e:
        return {
            'valid': False,
            'format': 'turtle',
            'triples_count': 0,
            'errors': [str(e)]
        }

def get_validation_progress(validation_id: str) -> Dict[str, Any]:
    """Get validation progress."""
    try:
        query = f"""
        SELECT ?validationId ?totalTriples ?processedTriples ?status WHERE {{
            ?validation a <http://xpshacl.org/#ValidationExecution> .
            ?validation <http://xpshacl.org/#validationId> "{validation_id}" .
            ?validation <http://xpshacl.org/#totalTriples> ?totalTriples .
            ?validation <http://xpshacl.org/#processedTriples> ?processedTriples .
            ?validation <http://xpshacl.org/#status> ?status .
        }}
        """

        result = virtuoso_service.execute_sparql_query(query)
        bindings = result.get('results', {}).get('bindings', [])

        if bindings:
            binding = bindings[0]
            total = int(binding.get('totalTriples', {}).get('value', 1))
            processed = int(binding.get('processedTriples', {}).get('value', 0))
            percentage = (processed / total) * 100 if total > 0 else 0

            return {
                'validationId': validation_id,
                'totalTriples': total,
                'processedTriples': processed,
                'percentage': round(percentage, 2),
                'status': binding.get('status', {}).get('value', 'unknown')
            }
        else:
            return {'error': 'Validation not found'}

    except Exception as e:
        logger.error(f"Error getting validation progress: {str(e)}")
        return {'error': str(e)}

def cancel_validation(validation_id: str) -> Dict[str, Any]:
    """Cancel a validation."""
    try:
        update_query = f"""
        WHERE {{
            ?validation a <http://xpshacl.org/#ValidationExecution> .
            ?validation <http://xpshacl.org/#validationId> "{validation_id}" .
        }}
        DELETE {{
            ?validation <http://xpshacl.org/#status> ?oldStatus .
        }}
        INSERT {{
            ?validation <http://xpshacl.org/#status> "cancelled" .
        }}
        """

        virtuoso_service.execute_sparql_update(update_query)

        return {
            'cancelled': True,
            'validationId': validation_id,
            'cancelledAt': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error cancelling validation: {str(e)}")
        return {
            'cancelled': False,
            'validationId': validation_id,
            'error': str(e)
        }

def retry_validation(validation_id: str) -> Dict[str, Any]:
    """Retry a failed validation."""
    try:
        new_validation_id = str(uuid.uuid4())

        # Copy original validation settings
        query = f"""
        SELECT ?dataGraph ?shapesGraph WHERE {{
            ?validation a <http://xpshacl.org/#ValidationExecution> .
            ?validation <http://xpshacl.org/#validationId> "{validation_id}" .
            ?validation <http://xpshacl.org/#dataGraph> ?dataGraph .
            ?validation <http://xpshacl.org/#shapesGraph> ?shapesGraph .
        }}
        """

        result = virtuoso_service.execute_sparql_query(query)
        bindings = result.get('results', {}).get('bindings', [])

        if bindings:
            binding = bindings[0]
            data_graph = binding.get('dataGraph', {}).get('value', '')
            shapes_graph = binding.get('shapesGraph', {}).get('value', '')

            # Create new validation
            new_session = create_validation_session(shapes_graph, data_graph)

            return {
                'newValidationId': new_validation_id,
                'status': 'started',
                'originalValidationId': validation_id,
                'sessionId': new_session.get('sessionId', '')
            }
        else:
            return {'error': 'Original validation not found'}

    except Exception as e:
        logger.error(f"Error retrying validation: {str(e)}")
        return {'error': str(e)}

def parse_validation_results(raw_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse validation results from SPARQL."""
    try:
        bindings = raw_results.get('results', {}).get('bindings', [])

        parsed_results = []
        for binding in bindings:
            parsed_result = {}
            for key, value in binding.items():
                if 'value' in value:
                    parsed_result[key] = value['value']

            parsed_results.append(parsed_result)

        return parsed_results

    except Exception as e:
        logger.error(f"Error parsing validation results: {str(e)}")
        return []

def export_validation_report(session_id: str, format: str = "json") -> Dict[str, Any]:
    """Export validation report."""
    try:
        if format.lower() == "json":
            # Get validation data
            report = get_validation_report(session_id)
            history = get_validation_history(limit=1)

            export_data = {
                'session_id': session_id,
                'validation_report': report,
                'exported_at': datetime.now().isoformat(),
                'format': 'json'
            }

            return {
                'report': json.dumps(export_data, indent=2),
                'format': 'json',
                'session_id': session_id
            }
        else:
            return {'error': f'Format {format} not supported'}

    except Exception as e:
        logger.error(f"Error exporting validation report: {str(e)}")
        return {'error': str(e)}

def validate_configuration(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Validate validation configuration."""
    try:
        errors = []

        # Check severity level
        valid_severity_levels = ['Violation', 'Warning', 'Info']
        severity = config_dict.get('severity_level')
        if severity and severity not in valid_severity_levels:
            errors.append(f"Invalid severity_level: {severity}. Must be one of {valid_severity_levels}")

        # Check boolean values
        enable_inference = config_dict.get('enable_inference')
        if enable_inference is not None and not isinstance(enable_inference, bool):
            errors.append("enable_inference must be a boolean")

        abort_on_first = config_dict.get('abort_on_first')
        if abort_on_first is not None and not isinstance(abort_on_first, bool):
            errors.append("abort_on_first must be a boolean")

        include_rdfs = config_dict.get('include_rdfs')
        if include_rdfs is not None and not isinstance(include_rdfs, bool):
            errors.append("include_rdfs must be a boolean")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'configuration': config_dict
        }

    except Exception as e:
        logger.error(f"Error validating configuration: {str(e)}")
        return {
            'valid': False,
            'errors': [str(e)],
            'configuration': config_dict
        }
