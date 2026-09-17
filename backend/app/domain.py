"""Local SQLite ingestion and deterministic lexical retrieval; no model calls."""
import hashlib
from pathlib import Path
import re
import sqlite3
from typing import Protocol

STOP = set('a an the and or is are was were be to of in on for with what when where how who why does do happen happens every'.split())

def terms(text: str) -> set[str]:
    return {word for word in re.findall(r'[a-z0-9]+', text.lower()) if word not in STOP}

class AnswerProvider(Protocol):
    def answer(self, citations: list[dict]) -> dict: ...

class ExtractiveProvider:
    def answer(self, citations: list[dict]) -> dict:
        return {'answer': '\n'.join(item['quote'] for item in citations) if citations else 'No relevant source found. Try a question about the ingested documents.',
                'citations': citations, 'supported': bool(citations), 'mode': 'offline-extractive'}

class KnowledgeBase:
    def __init__(self, path: Path, provider: AnswerProvider | None = None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.provider = provider or ExtractiveProvider()
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, title TEXT NOT NULL, text TEXT NOT NULL)')

    def add(self, title: str, text: str) -> dict:
        title, text = title.strip(), text.strip()
        if not 1 <= len(title) <= 120 or not 1 <= len(text) <= 50000:
            raise ValueError('Title must be 1–120 characters and text 1–50,000 characters')
        identity = hashlib.sha256((title + '\0' + text).encode()).hexdigest()[:24]
        with sqlite3.connect(self.path, timeout=10) as db:
            db.execute('BEGIN IMMEDIATE')
            if not db.execute('SELECT 1 FROM documents WHERE id = ?', (identity,)).fetchone() and db.execute('SELECT COUNT(*) FROM documents').fetchone()[0] >= 100:
                raise ValueError('Library limit of 100 documents reached')
            db.execute('INSERT OR IGNORE INTO documents VALUES (?, ?, ?)', (identity, title, text))
        return {'id': identity, 'title': title, 'characters': len(text)}

    def documents(self) -> list[dict]:
        with sqlite3.connect(self.path) as db:
            rows = db.execute('SELECT id, title, text FROM documents ORDER BY title, id').fetchall()
        return [{'id': identity, 'title': title, 'characters': len(text)} for identity, title, text in rows]

    def ask(self, question: str) -> dict:
        question = question.strip()
        query = terms(question)
        if not 1 <= len(question) <= 500 or not query:
            raise ValueError('Question must be 1–500 characters and contain meaningful search terms')
        with sqlite3.connect(self.path) as db:
            rows = db.execute('SELECT id, title, text FROM documents ORDER BY id').fetchall()
        hits = []
        for identity, title, text in rows:
            for index, match in enumerate(re.finditer(r'[^.!?\n]+(?:[.!?]|(?=\n|$))', text)):
                quote = match.group().strip()
                overlap = query & terms(quote)
                if len(overlap) / len(query) >= 0.5:
                    hits.append((len(overlap) / len(query), identity, index, {'document_id': identity, 'title': title, 'chunk': index, 'quote': quote}))
        hits.sort(key=lambda item: (-item[0], item[1], item[2]))
        # One best passage keeps every word of the answer directly attributable.
        citations = [hits[0][3]] if hits else []
        return self.provider.answer(citations)
