from rdflib import Graph
from functions.xpshacl_engine.extended_shacl_validator import ExtendedShaclValidator
from functions import virtuoso_service
import config

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
