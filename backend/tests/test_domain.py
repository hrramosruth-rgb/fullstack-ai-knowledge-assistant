import pytest
from app.domain import KnowledgeBase

@pytest.fixture
def kb(tmp_path): return KnowledgeBase(tmp_path / 'knowledge.sqlite')

def test_ingest_survives_restart_and_deduplicates(kb, tmp_path):
    doc = kb.add('Handbook','Release reviews happen every Thursday.')
    assert doc['id'] == kb.add('Handbook','Release reviews happen every Thursday.')['id']
    assert len(KnowledgeBase(tmp_path/'knowledge.sqlite').documents()) == 1

def test_supported_answer_quotes_stored_source(kb):
    doc = kb.add('Delivery','Release reviews happen every Thursday. Budget approval happens on Monday.')
    result = kb.ask('When are release reviews?')
    assert result['mode'] == 'offline-extractive'
    assert result['citations'][0]['document_id'] == doc['id']
    assert result['answer'] == 'Release reviews happen every Thursday.'
    assert result['citations'][0]['quote'] == result['answer']

def test_no_source_refuses_without_citations(kb):
    kb.add('Handbook','Release reviews happen every Thursday.')
    result = kb.ask('What is the lunar temperature?')
    assert result['supported'] is False
    assert result['citations'] == []
    assert 'source' in result['answer'].lower()

@pytest.mark.parametrize('title,text',[('', 'content'), ('Title',''), ('a'*121,'content'), ('Title','a'*50001)])
def test_invalid_document_does_not_mutate(kb,title,text):
    with pytest.raises(ValueError): kb.add(title,text)
    assert kb.documents() == []

@pytest.mark.parametrize('question',['', 'the and is', 'a'*501])
def test_invalid_question(kb, question):
    with pytest.raises(ValueError): kb.ask(question)

def test_low_overlap_refuses_instead_of_claiming_answer(kb):
    kb.add('Handbook','Release reviews happen every Thursday.')
    result = kb.ask('release solar gravitational temperature')
    assert result['supported'] is False
    assert result['citations'] == []

def test_library_limit_rejects_without_partial_write(kb):
    for index in range(100): kb.add(f'Note {index}', 'A short source passage.')
    with pytest.raises(ValueError): kb.add('Overflow','Extra source.')
    assert len(kb.documents()) == 100
    assert kb.add('Note 0','A short source passage.')['title'] == 'Note 0'


def test_multiline_notes_retrieve_unpunctuated_first_line(kb):
    source = "Release reviews happen every Thursday\nBudget approval happens on Monday"
    kb.add('Pasted notes', source)
    result = kb.ask('When are release reviews?')
    assert result['supported'] is True
    assert result['answer'] == 'Release reviews happen every Thursday'
    assert result['citations'][0]['quote'] in source


def test_long_multiline_quote_keeps_exact_source_provenance(kb):
    source = 'Release reviews ' + 'follow documented procedures ' * 99 + 'follow documented procedures' + '\nBudget approval happens on Monday'
    kb.add('Long notes', source)
    result = kb.ask('release reviews')
    assert result['supported'] is True
    assert result['mode'] == 'offline-extractive'
    assert result['answer'] == source.split('\n')[0]
    assert result['citations'][0]['quote'] == result['answer']
    assert result['citations'][0]['quote'] in source
