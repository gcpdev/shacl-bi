# upload_routes.py
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import datetime
from config import SRG_MODEL, OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, USERNAME, PASSWORD
from functions import virtuoso_service
import rdflib
import requests
from requests.auth import HTTPBasicAuth

# Define SHACL namespace manually since it's not available in rdflib.namespace
SHACL = rdflib.Namespace("http://www.w3.org/ns/shacl#")

upload_bp = Blueprint('upload', __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'ttl', 'rdf', 'n3', 'nt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/api/upload/files', methods=['POST'])
def upload_files():
    """
    Upload data and shapes files for validation
    Uses backend configuration for AI settings
    Implements tenant isolation using session-specific graphs
    """
    try:
        # Check if files are present in the request
        if 'dataFile' not in request.files or 'shapesFile' not in request.files:
            return jsonify({'error': 'Both dataFile and shapesFile are required'}), 400

        data_file = request.files['dataFile']
        shapes_file = request.files['shapesFile']

        # Check if filenames are empty
        if data_file.filename == '' or shapes_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Check if files have allowed extensions
        if not (allowed_file(data_file.filename) and allowed_file(shapes_file.filename)):
            return jsonify({'error': 'Invalid file extension. Allowed: ttl, rdf, n3, nt'}), 400

        # Generate unique session ID for tenant isolation
        import uuid
        session_id = str(uuid.uuid4())[:8]  # Short session ID

        # Create tenant-specific graph URIs
        validation_graph_uri = f"http://ex.org/ValidationReport/Session_{session_id}"
        data_graph_uri = f"http://ex.org/Data/Session_{session_id}"
        shapes_graph_uri = f"http://ex.org/Shapes/Session_{session_id}"

        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads', session_id)
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        # Save files
        data_filename = secure_filename(data_file.filename)
        shapes_filename = secure_filename(shapes_file.filename)

        data_path = os.path.join(upload_dir, f"data_{data_filename}")
        shapes_path = os.path.join(upload_dir, f"shapes_{shapes_filename}")

        data_file.save(data_path)
        shapes_file.save(shapes_path)

        # Perform SHACL validation on uploaded files
        try:
            print(f"Starting validation for session {session_id}")
            print(f"Data file: {data_path}")
            print(f"Shapes file: {shapes_path}")

            # Load the data and shapes graphs
            data_graph = rdflib.Graph()
            shapes_graph = rdflib.Graph()

            data_graph.parse(data_path, format='turtle')
            shapes_graph.parse(shapes_path, format='turtle')
            print(f"Parsed {len(data_graph)} data triples and {len(shapes_graph)} shape triples")

            # Perform SHACL validation
            from pyshacl import validate
            print("Starting PySHACL validation...")

            # Validate data against shapes
            conforms, results_graph, results_text = validate(
                data_graph,
                shacl_graph=shapes_graph,
                ont_graph=None,
                inference='rdfs',
                abort_on_first=False,
                allow_infos=False,
                allow_warnings=False,
                meta_shacl=False,
                debug=False
            )
            print(f"Validation result: conforms={conforms}, has_results={results_graph is not None}")

            # Extract violations from results graph for background processing
            violations_for_background = []
            if results_graph:
                violations_query = """
                SELECT ?focusNode ?resultMessage ?resultPath ?resultSeverity ?sourceConstraintComponent ?value ?sourceShape
                WHERE {
                    ?violation a <http://www.w3.org/ns/shacl#ValidationResult> ;
                             <http://www.w3.org/ns/shacl#resultMessage> ?resultMessage ;
                             <http://www.w3.org/ns/shacl#resultSeverity> ?resultSeverity ;
                             <http://www.w3.org/ns/shacl#sourceConstraintComponent> ?sourceConstraintComponent .
                    OPTIONAL { ?violation <http://www.w3.org/ns/shacl#focusNode> ?focusNode . }
                    OPTIONAL { ?violation <http://www.w3.org/ns/shacl#resultPath> ?resultPath . }
                    OPTIONAL { ?violation <http://www.w3.org/ns/shacl#value> ?value . }
                    OPTIONAL { ?violation <http://www.w3.org/ns/shacl#sourceShape> ?sourceShape . }
                }
                """
                try:
                    violation_results = results_graph.query(violations_query)
                    for result in violation_results:
                        violation = {
                            'focus_node': str(result['focusNode']) if result['focusNode'] else None,
                            'result_path': str(result['resultPath']) if result['resultPath'] else None,
                            'value': str(result['value']) if result['value'] else None,
                            'message': str(result['resultMessage']),
                            'constraint_component': str(result['sourceConstraintComponent']),
                            'source_shape': str(result['sourceShape']) if result['sourceShape'] else None
                        }
                        violations_for_background.append(violation)
                    print(f"Extracted {len(violations_for_background)} violations for background processing")
                except Exception as e:
                    print(f"Error extracting violations for background processing: {e}")

            # Load validation results and shapes graph into tenant-specific Virtuoso graphs
            if results_graph:
                print(f"Storing validation results in Virtuoso graph: {validation_graph_uri}")
                print(f"DEBUG: About to store shapes graph in Virtuoso graph: {shapes_graph_uri}")

                # Use virtuoso_service to store the validation results and shapes graph
                # This uses direct SPARQL INSERT to avoid permission issues
                try:
                    # Store validation results
                    nt_data = results_graph.serialize(format='nt')
                    insert_query = f"""
                    INSERT DATA {{
                        GRAPH <{validation_graph_uri}> {{
                            {nt_data}
                        }}
                    }}
                    """
                    virtuoso_service.execute_sparql_update(insert_query)
                    print(f"Successfully stored validation results in Virtuoso using direct INSERT for session {session_id}")

                    # Store shapes graph for dashboard statistics
                    try:
                        shapes_nt_data = shapes_graph.serialize(format='nt')
                        shapes_insert_query = f"""
                        INSERT DATA {{
                            GRAPH <{shapes_graph_uri}> {{
                                {shapes_nt_data}
                            }}
                        }}
                        """
                        virtuoso_service.execute_sparql_update(shapes_insert_query)
                        print(f"Successfully stored shapes graph in Virtuoso using direct INSERT for session {session_id}")
                    except Exception as shapes_error:
                        print(f"Error storing shapes graph in Virtuoso: {shapes_error}")
                        # Continue without storing shapes graph

                    # Extract violation count from the results graph
                    try:
                        violation_query = """
                        SELECT (COUNT(?violation) AS ?violationCount)
                        WHERE {
                            ?violation a <http://www.w3.org/ns/shacl#ValidationResult> .
                        }
                        """
                        violation_results = results_graph.query(violation_query)
                        violation_count = int(list(violation_results)[0][0])
                        print(f"Found {violation_count} violations in validation graph")
                    except Exception as e:
                        print(f"Error counting violations: {e}")
                        violation_count = 0

                except Exception as e:
                    print(f"Error storing validation results in Virtuoso: {e}")
                    print(f"Exception type: {type(e)}")
                    import traceback
                    traceback.print_exc()
                    # Continue without storing in Virtuoso - still return validation results
                    violation_count = 0

                # Trigger background AI explanation processing if violations found
                if violation_count > 0:
                    try:
                        from functions.background_processor import submit_explanation_job
                        submit_explanation_job(session_id, violations_for_background)
                        print(f"Submitted background AI explanation job for session {session_id} with {len(violations_for_background)} violations")
                    except Exception as bg_error:
                        print(f"Error starting background processing: {bg_error}")

                return jsonify({
                    'message': 'Files validated successfully',
                    'data_file': data_filename,
                    'shapes_file': shapes_filename,
                    'conforms': conforms,
                    'violation_count': violation_count,
                    'validation_results': results_text,
                    'session_id': session_id,
                    'validation_graph_uri': validation_graph_uri
                }), 200
            else:
                return jsonify({
                    'message': 'Validation completed - no violations found',
                    'data_file': data_filename,
                    'shapes_file': shapes_filename,
                    'conforms': conforms,
                    'violation_count': 0,
                    'validation_results': 'No violations found',
                    'session_id': session_id,
                    'validation_graph_uri': validation_graph_uri
                }), 200

        except Exception as validation_error:
            print(f"Validation error: {validation_error}")
            # If validation fails, still return upload success but note the validation issue
            return jsonify({
                'message': 'Files uploaded but validation failed',
                'data_file': data_filename,
                'shapes_file': shapes_filename,
                'validation_error': str(validation_error),
                'session_id': session_id
            }), 500

    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

# Note: /api/violations route is handled by simple_routes.py to avoid conflicts

def _get_default_api_key():
    """
    Get the first available API key from environment variables
    Priority: OpenAI > Anthropic > Gemini
    """
    if OPENAI_API_KEY:
        return OPENAI_API_KEY
    elif ANTHROPIC_API_KEY:
        return ANTHROPIC_API_KEY
    elif GEMINI_API_KEY:
        return GEMINI_API_KEY
    else:
        raise ValueError("No API key found in environment variables. Please set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY in your .env file.")