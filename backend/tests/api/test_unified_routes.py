import json

def test_index(client):
    response = client.get('/api/')
    assert response.status_code == 200
    assert response.data == b'Hello, World!'

def test_validate(client):
    data = {
        'data_graph': '@prefix ex: <http://example.com/> . ex:MyResource a ex:MyClass .',
        'shapes_graph': '@prefix ex: <http://example.com/> . @prefix sh: <http://www.w3.org/ns/shacl#> . ex:MyShape a sh:NodeShape ; sh:targetClass ex:MyClass ; sh:property [ sh:path ex:myProperty ; sh:minCount 1 ; ] .'
    }
    response = client.post('/api/validate', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 200
    json_data = response.get_json()
    assert not json_data['conforms']

def test_validate_missing_data(client):
    data = {
        'shapes_graph': '@prefix ex: <http://example.com/> . @prefix sh: <http://www.w3.org/ns/shacl#> . ex:MyShape a sh:NodeShape ; sh:targetClass ex:MyClass ; sh:property [ sh:path ex:myProperty ; sh:minCount 1 ; ] .'
    }
    response = client.post('/api/validate', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 400

def test_violations_route(client):
    response = client.get('/api/violations')
    assert response.status_code == 200

def test_violation_route_not_found(client):
    response = client.get('/api/violations/invalid_id')
    assert response.status_code == 404

def test_statistics_route(client):
    response = client.get('/api/statistics')
    assert response.status_code == 200
