import pytest
from rdflib import Graph
from backend.core.validation import run_validation

@pytest.fixture
def data_graph():
    g = Graph()
    g.parse(data='''
        @prefix ex: <http://example.com/> .
        ex:MyResource a ex:MyClass .
    ''', format='turtle')
    return g

@pytest.fixture
def shapes_graph():
    g = Graph()
    g.parse(data='''
        @prefix ex: <http://example.com/> .
        @prefix sh: <http://www.w3.org/ns/shacl#> .

        ex:MyShape
            a sh:NodeShape ;
            sh:targetClass ex:MyClass ;
            sh:property [
                sh:path ex:myProperty ;
                sh:minCount 1 ;
            ] .
    ''', format='turtle')
    return g

def test_run_validation(data_graph, shapes_graph):
    conforms, results_graph, results_text = run_validation(data_graph, shapes_graph)
    assert not conforms
    assert "sh:Violation" in results_text
