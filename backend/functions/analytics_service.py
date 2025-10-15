from typing import List, Dict, Any
from functions.xpshacl_engine.xpshacl_architecture import ConstraintViolation
from . import virtuoso_service

def prioritize_violations(violations: List[ConstraintViolation]) -> List[ConstraintViolation]:
    """Prioritize violations by severity."""
    return sorted(violations, key=lambda v: v.severity or '', reverse=True)

def get_violation_statistics(session_id: str) -> List[Dict[str, Any]]:
    """Get violation statistics grouped by constraint type."""
    query = f"""
    SELECT ?constraintType (COUNT(?violation) as ?count) WHERE {{
        GRAPH <http://ex.org/ValidationReport/Session_{session_id}> {{
            ?violation a <http://www.w3.org/ns/shacl#ValidationResult> .
            ?violation <http://www.w3.org/ns/shacl#sourceConstraintComponent> ?constraintType .
        }}
    }}
    GROUP BY ?constraintType
    ORDER BY DESC(?count)
    """

    result = virtuoso_service.execute_sparql_query(query)
    return format_analytics_response(result.get('results', {}).get('bindings', []))

def get_property_distribution(session_id: str) -> List[Dict[str, Any]]:
    """Get property distribution analysis for violations."""
    query = f"""
    SELECT ?propertyPath (COUNT(?violation) as ?violationCount) WHERE {{
        GRAPH <http://ex.org/ValidationReport/Session_{session_id}> {{
            ?violation a <http://www.w3.org/ns/shacl#ValidationResult> .
            ?violation <http://www.w3.org/ns/shacl#resultPath> ?propertyPath .
        }}
    }}
    GROUP BY ?propertyPath
    ORDER BY DESC(?violationCount)
    """

    result = virtuoso_service.execute_sparql_query(query)
    return format_analytics_response(result.get('results', {}).get('bindings', []))

def get_severity_analysis(session_id: str) -> List[Dict[str, Any]]:
    """Get severity analysis of violations."""
    query = f"""
    SELECT ?severity (COUNT(?violation) as ?count) WHERE {{
        GRAPH <http://ex.org/ValidationReport/Session_{session_id}> {{
            ?violation a <http://www.w3.org/ns/shacl#ValidationResult> .
            ?violation <http://www.w3.org/ns/shacl#severity> ?severity .
        }}
    }}
    GROUP BY ?severity
    ORDER BY DESC(?count)
    """

    result = virtuoso_service.execute_sparql_query(query)
    return format_analytics_response(result.get('results', {}).get('bindings', []))

def get_temporal_trends(session_id: str, days: int = 7) -> List[Dict[str, Any]]:
    """Get temporal violation trends over specified days."""
    # This is a simplified implementation - in practice would need timestamp data
    query = f"""
    SELECT ?date (COUNT(?violation) as ?count) WHERE {{
        GRAPH <http://ex.org/ValidationReport/Session_{session_id}> {{
            ?violation a <http://www.w3.org/ns/shacl#ValidationResult> .
            BIND(NOW() as ?date)
        }}
    }}
    GROUP BY ?date
    LIMIT {days}
    """

    result = virtuoso_service.execute_sparql_query(query)
    return format_analytics_response(result.get('results', {}).get('bindings', []))

def get_shape_complexity_metrics() -> List[Dict[str, Any]]:
    """Get shape complexity metrics."""
    query = """
    SELECT ?shape (COUNT(?constraint) as ?constraintCount) WHERE {
        GRAPH <http://ex.org/ShapesGraph> {
            ?shape a <http://www.w3.org/ns/shacl#NodeShape> .
            ?shape ?predicate ?constraint .
            FILTER(?predicate IN (<http://www.w3.org/ns/shacl#property>,
                                 <http://www.w3.org/ns/shacl#node>,
                                 <http://www.w3.org/ns/shacl#class>))
        }
    }
    GROUP BY ?shape
    ORDER BY DESC(?constraintCount)
    """

    result = virtuoso_service.execute_sparql_query(query)
    return format_analytics_response(result.get('results', {}).get('bindings', []))

def get_focus_node_analysis(session_id: str) -> List[Dict[str, Any]]:
    """Get focus node violation analysis."""
    query = f"""
    SELECT ?focusNode (COUNT(?violation) as ?violationCount) WHERE {{
        GRAPH <http://ex.org/ValidationReport/Session_{session_id}> {{
            ?violation a <http://www.w3.org/ns/shacl#ValidationResult> .
            ?violation <http://www.w3.org/ns/shacl#focusNode> ?focusNode .
        }}
    }}
    GROUP BY ?focusNode
    ORDER BY DESC(?violationCount)
    LIMIT 50
    """

    result = virtuoso_service.execute_sparql_query(query)
    return format_analytics_response(result.get('results', {}).get('bindings', []))

def get_repair_success_rate(session_id: str) -> List[Dict[str, Any]]:
    """Get repair success rate analytics by constraint type."""
    query = f"""
    SELECT ?constraintType (COUNT(?repair) as ?attempted)
           (SUM(IF(?success = true, 1, 0)) as ?successful) WHERE {{
        GRAPH <http://ex.org/ValidationReport/Session_{session_id}> {{
            ?repair a <http://xpshacl.org/#RepairAttempt> .
            ?repair <http://xpshacl.org/#constraintType> ?constraintType .
            ?repair <http://xpshacl.org/#success> ?success .
        }}
    }}
    GROUP BY ?constraintType
    """

    result = virtuoso_service.execute_sparql_query(query)
    bindings = result.get('results', {}).get('bindings', [])

    # Calculate success rate
    formatted = []
    for binding in bindings:
        attempted = int(binding.get('attempted', {}).get('value', 0))
        successful = int(binding.get('successful', {}).get('value', 0))
        success_rate = successful / attempted if attempted > 0 else 0

        formatted.append({
            'constraintType': binding.get('constraintType', {}).get('value', ''),
            'attempted': attempted,
            'successful': successful,
            'successRate': success_rate
        })

    return formatted

def get_data_quality_score(session_id: str) -> Dict[str, Any]:
    """Calculate overall data quality score."""
    # Get total triples and violations
    total_query = f"""
    SELECT (COUNT(*) as ?totalTriples) WHERE {{
        GRAPH <http://ex.org/ValidationReport/Session_{session_id}> {{
            ?s ?p ?o .
        }}
    }}
    """

    violation_query = f"""
    SELECT (COUNT(?violation) as ?violations) WHERE {{
        GRAPH <http://ex.org/ValidationReport/Session_{session_id}> {{
            ?violation a <http://www.w3.org/ns/shacl#ValidationResult> .
        }}
    }}
    """

    total_result = virtuoso_service.execute_sparql_query(total_query)
    violation_result = virtuoso_service.execute_sparql_query(violation_query)

    total_triples = int(total_result.get('results', {}).get('bindings', [{}])[0].get('totalTriples', {}).get('value', 0))
    violations = int(violation_result.get('results', {}).get('bindings', [{}])[0].get('violations', {}).get('value', 0))

    # Calculate quality score (0-100)
    quality_score = max(0, 100 - (violations / max(1, total_triples) * 100))

    return {
        'totalTriples': total_triples,
        'violations': violations,
        'qualityScore': round(quality_score, 2)
    }

def get_constraint_correlation_matrix(session_id: str) -> List[Dict[str, Any]]:
    """Get constraint correlation matrix."""
    # Simplified correlation analysis
    query = f"""
    SELECT ?constraint1 ?constraint2 (COUNT(*) as ?cooccurrence) WHERE {{
        GRAPH <http://ex.org/ValidationReport/Session_{session_id}> {{
            ?focusNode <http://www.w3.org/ns/shacl#sourceConstraintComponent> ?constraint1 .
            ?focusNode <http://www.w3.org/ns/shacl#sourceConstraintComponent> ?constraint2 .
            FILTER(?constraint1 != ?constraint2)
        }}
    }}
    GROUP BY ?constraint1 ?constraint2
    LIMIT 20
    """

    result = virtuoso_service.execute_sparql_query(query)
    bindings = result.get('results', {}).get('bindings', [])

    # Calculate correlation (simplified)
    formatted = []
    for binding in bindings:
        cooccurrence = int(binding.get('cooccurrence', {}).get('value', 0))
        # Simple correlation calculation - in practice would use proper statistical method
        correlation = min(1.0, cooccurrence / 10.0)

        formatted.append({
            'constraint1': binding.get('constraint1', {}).get('value', ''),
            'constraint2': binding.get('constraint2', {}).get('value', ''),
            'correlation': str(correlation)
        })

    return formatted

def calculate_quality_metrics(data: Dict[str, Any]) -> Dict[str, float]:
    """Calculate quality metrics from raw data."""
    total_items = data.get('total_items', 1)

    return {
        'violation_rate': data.get('total_violations', 0) / total_items,
        'warning_rate': data.get('total_warnings', 0) / total_items,
        'repair_success_rate': data.get('repairs_successful', 0) / max(1, data.get('repairs_attempted', 1)),
        'overall_score': 100 - (data.get('total_violations', 0) + data.get('total_warnings', 0)) / total_items * 100
    }

def get_session_comparison(session_ids: List[str]) -> List[Dict[str, Any]]:
    """Compare multiple validation sessions."""
    if not session_ids:
        return []

    # Build query for multiple sessions
    session_filters = " UNION ".join([
        f'{{ GRAPH <http://ex.org/ValidationReport/Session_{sid}> {{ ?violation a <http://www.w3.org/ns/shacl#ValidationResult> . BIND("{sid}" as ?sessionId) }} }}'
        for sid in session_ids
    ])

    query = f"""
    SELECT ?sessionId (COUNT(?violation) as ?violationCount) WHERE {{
        {session_filters}
    }}
    GROUP BY ?sessionId
    """

    result = virtuoso_service.execute_sparql_query(query)
    formatted = format_analytics_response(result.get('results', {}).get('bindings', []))

    # Add quality scores
    for session in formatted:
        session_id = session['sessionId']
        quality_data = get_data_quality_score(session_id)
        session['qualityScore'] = quality_data['qualityScore']

    return formatted

def get_top_violating_resources(session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get top violating resources."""
    query = f"""
    SELECT ?focusNode (COUNT(?violation) as ?violationCount) WHERE {{
        GRAPH <http://ex.org/ValidationReport/Session_{session_id}> {{
            ?violation a <http://www.w3.org/ns/shacl#ValidationResult> .
            ?violation <http://www.w3.org/ns/shacl#focusNode> ?focusNode .
        }}
    }}
    GROUP BY ?focusNode
    ORDER BY DESC(?violationCount)
    LIMIT {limit}
    """

    result = virtuoso_service.execute_sparql_query(query)
    raw_data = result.get('results', {}).get('bindings', [])

    # Format and map focusNode to resource for compatibility
    formatted = []
    for item in raw_data:
        formatted_item = {}
        for key, value in item.items():
            if isinstance(value, dict) and 'value' in value:
                str_value = value['value']
                try:
                    if str_value.isdigit():
                        formatted_item[key] = int(str_value)
                    else:
                        formatted_item[key] = float(str_value)
                except ValueError:
                    formatted_item[key] = str_value
            else:
                formatted_item[key] = value

        # Map focusNode to resource for test compatibility
        if 'focusNode' in formatted_item:
            formatted_item['resource'] = formatted_item['focusNode']

        formatted.append(formatted_item)

    return formatted

def get_validation_performance_metrics() -> List[Dict[str, Any]]:
    """Get validation performance metrics."""
    query = """
    SELECT ?validationId ?duration ?triplesValidated WHERE {
        ?validation a <http://xpshacl.org/#ValidationExecution> .
        ?validation <http://xpshacl.org/#validationId> ?validationId .
        ?validation <http://xpshacl.org/#duration> ?duration .
        ?validation <http://xpshacl.org/#triplesValidated> ?triplesValidated .
    }
    ORDER BY DESC(?duration)
    LIMIT 50
    """

    result = virtuoso_service.execute_sparql_query(query)
    bindings = result.get('results', {}).get('bindings', [])

    # Calculate throughput
    formatted = []
    for binding in bindings:
        duration = float(binding.get('duration', {}).get('value', 0)) / 1000  # Convert ms to seconds
        triples = int(binding.get('triplesValidated', {}).get('value', 0))
        throughput = triples / duration if duration > 0 else 0

        formatted.append({
            'validationId': binding.get('validationId', {}).get('value', ''),
            'duration': int(binding.get('duration', {}).get('value', 0)),
            'triplesValidated': triples,
            'throughput': round(throughput, 2)
        })

    return formatted

def format_analytics_response(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format raw SPARQL results into analytics response."""
    formatted = []
    for item in raw_data:
        formatted_item = {}
        for key, value in item.items():
            if isinstance(value, dict) and 'value' in value:
                # Try to convert to appropriate type
                str_value = value['value']
                try:
                    if str_value.isdigit():
                        formatted_item[key] = int(str_value)
                    else:
                        formatted_item[key] = float(str_value)
                except ValueError:
                    formatted_item[key] = str_value
            else:
                formatted_item[key] = value
        formatted.append(formatted_item)
    return formatted

def calculate_trend_direction(data: List[float]) -> str:
    """Calculate trend direction from data series."""
    if len(data) < 3:
        return 'insufficient_data'

    # Simple trend calculation
    first_half = data[:len(data)//2]
    second_half = data[len(data)//2:]

    first_avg = sum(first_half) / len(first_half)
    second_avg = sum(second_half) / len(second_half)

    if second_avg > first_avg * 1.1:
        return 'increasing'
    elif second_avg < first_avg * 0.9:
        return 'decreasing'
    else:
        return 'stable'

def get_improvement_recommendations(session_id: str) -> List[Dict[str, Any]]:
    """Get improvement recommendations based on violation patterns."""
    # Get most frequent violation types
    violations = get_violation_statistics(session_id)

    recommendations = []
    for violation in violations[:5]:  # Top 5 violation types
        constraint_type = violation['constraintType']

        # Generate recommendations based on constraint type
        if 'MinCount' in constraint_type:
            recommendations.append({
                'constraintType': constraint_type,
                'frequency': violation['count'],
                'recommendation': 'Consider making these properties optional or providing default values'
            })
        elif 'Pattern' in constraint_type:
            recommendations.append({
                'constraintType': constraint_type,
                'frequency': violation['count'],
                'recommendation': 'Improve data validation at input stage or provide clearer format guidelines'
            })
        elif 'MaxCount' in constraint_type:
            recommendations.append({
                'constraintType': constraint_type,
                'frequency': violation['count'],
                'recommendation': 'Review data entry processes to prevent duplicate values'
            })
        else:
            recommendations.append({
                'constraintType': constraint_type,
                'frequency': violation['count'],
                'recommendation': 'Review constraint definition and data requirements'
            })

    return recommendations

def get_recommendations(session_id: str) -> List[Dict[str, Any]]:
    """Alias for get_improvement_recommendations to maintain compatibility."""
    return get_improvement_recommendations(session_id)
