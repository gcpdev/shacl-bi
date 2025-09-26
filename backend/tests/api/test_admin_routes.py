import json

def test_login(client):
    data = {'user_id': 'test_user'}
    response = client.post('/api/admin/login', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'token' in json_data

def test_load_ontology_no_token(client):
    response = client.post('/api/admin/load_ontology')
    assert response.status_code == 401

def test_load_ontology_with_token(client):
    data = {'user_id': 'test_user'}
    response = client.post('/api/admin/login', data=json.dumps(data), content_type='application/json')
    token = response.get_json()['token']

    response = client.post('/api/admin/load_ontology', headers={'x-access-token': token})
    assert response.status_code == 200
