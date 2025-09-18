from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from app.domain import KnowledgeBase

ROOT = Path(__file__).resolve().parents[2]

class DocumentInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    title: str = Field(min_length=1, max_length=120)
    text: str = Field(min_length=1, max_length=50000)

class QuestionInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    question: str = Field(min_length=1, max_length=500)

def create_app(path: Path | None = None, seed: bool = True) -> FastAPI:
    kb = KnowledgeBase(path or ROOT / 'data/knowledge.sqlite')
    if seed:
        kb.add('Demo delivery handbook', (ROOT / 'fixtures/handbook.txt').read_text())
    app = FastAPI(title='Offline knowledge assistant', version='1.0.0')

    @app.get('/api/documents')
    def documents():
        return kb.documents()

    @app.post('/api/documents', status_code=201)
    def ingest(body: DocumentInput):
        try:
            return kb.add(body.title, body.text)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post('/api/ask')
    def ask(body: QuestionInput):
        try:
            return kb.ask(body.question)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    return app
