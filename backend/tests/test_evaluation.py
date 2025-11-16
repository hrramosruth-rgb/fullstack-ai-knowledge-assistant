from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import pytest
from app.domain import KnowledgeBase
ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT/'eval/cases.json').read_text())

@pytest.mark.parametrize('case', CASES, ids=lambda case: case['question'])
def test_fixture_citation_evaluation(tmp_path, case):
    kb=KnowledgeBase(tmp_path/'eval.sqlite')
    source=(ROOT/'fixtures/handbook.txt').read_text()
    doc=kb.add('Demo delivery handbook',source)
    result=kb.ask(case['question'])
    assert result['supported'] is case['supported']
    assert case['contains'] in result['answer']
    for citation in result['citations']:
        assert citation['quote'] in source
        assert citation['document_id'] == doc['id']
        assert citation['quote'] == result['answer']
    if not case['supported']: assert result['citations'] == []

def test_concurrent_duplicate_ingest_remains_one_record(tmp_path):
    kb=KnowledgeBase(tmp_path/'parallel.sqlite')
    with ThreadPoolExecutor(max_workers=8) as pool:
        results=list(pool.map(lambda _:kb.add('Handbook','Reviews happen every Thursday.'), range(16)))
    assert len({result['id'] for result in results}) == 1
    assert len(kb.documents()) == 1

def test_concurrent_limit_enforced_atomically(tmp_path):
    kb=KnowledgeBase(tmp_path/'limit.sqlite')
    for index in range(99): kb.add(f'Existing {index}', 'Original source.')
    def add(index):
        try: return kb.add(f'New {index}','New source.')
        except ValueError: return None
    with ThreadPoolExecutor(max_workers=8) as pool: results=list(pool.map(add, range(16)))
    assert sum(result is not None for result in results) == 1
    assert len(kb.documents()) == 100
