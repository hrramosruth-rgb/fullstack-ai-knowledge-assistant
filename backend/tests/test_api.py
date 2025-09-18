import pytest
from fastapi.testclient import TestClient
from app.main import create_app

@pytest.fixture
def client(tmp_path): return TestClient(create_app(tmp_path/'test.sqlite',seed=False))

def test_ingest_ask_and_list_contract(client):
    response=client.post('/api/documents',json={'title':'Handbook','text':'Support hours are Monday to Friday.'})
    assert response.status_code == 201
    doc=response.json()
    answer=client.post('/api/ask',json={'question':'What are support hours?'}).json()
    assert answer['citations'][0]['document_id'] == doc['id']
    assert answer['answer'] == 'Support hours are Monday to Friday.'
    assert len(client.get('/api/documents').json()) == 1

@pytest.mark.parametrize('payload,code',[
    ({'title':'','text':'x'},422), ({'title':'x','text':'   '},400),
    ({'title':'x','text':'a'*50001},422), ({'title':'x'},422)])
def test_rejected_ingest_keeps_state(client,payload,code):
    assert client.post('/api/documents',json=payload).status_code == code
    assert client.get('/api/documents').json() == []

def test_empty_library_refusal(client):
    result=client.post('/api/ask',json={'question':'What is the budget?'}).json()
    assert result['supported'] is False
    assert result['citations'] == []

@pytest.mark.parametrize('question,code',[('',422),('   ',400),('the and is',400),('a'*501,422)])
def test_invalid_question(client,question,code):
    assert client.post('/api/ask',json={'question':question}).status_code == code

def test_missing_route(client):
    assert client.get('/api/documents/missing').status_code == 404
