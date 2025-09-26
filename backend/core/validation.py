
from pyshacl import validate

def run_validation(data_graph, shapes_graph, mode='analytics'):
    """
    Runs SHACL validation using pyshacl.

    Args:
        data_graph (rdflib.Graph): The data graph to be validated.
        shapes_graph (rdflib.Graph): The shapes graph to be used for validation.
        mode (str): The validation mode ('analytics' or 'remediation'). 
                    Currently, the validation logic is the same for both modes.
                    This can be extended in the future.

    Returns:
        A tuple containing the validation report graph and the validation results text.
    """
    conforms, results_graph, results_text = validate(
        data_graph,
        shacl_graph=shapes_graph,
        ont_graph=None,  # Optional ontology graph
        inference='none',
        abort_on_error=False,
        meta_shacl=False,
        debug=False
    )

    return conforms, results_graph, results_text