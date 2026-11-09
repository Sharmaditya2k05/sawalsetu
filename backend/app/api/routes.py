from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from ..rag.pipeline import Pipeline

router = APIRouter(prefix="/api")

SUGGESTIONS = [
    "How did sales do last month compared to the month before?",
    "Who are my top 5 customers and how much udhaar is pending from each?",
    "Which invoices are overdue by more than 60 days?",
    "What did we buy from Sun Pharma this year, and how much is still payable?",
    "Which items give the best margin on MRP?",
    "How are our Amazon and Flipkart orders performing?",
    "Give me a snapshot of the business right now.",
    "Why were purchase returns raised recently?",
]


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(default_factory=list)


def _pipeline(request: Request) -> Pipeline:
    return request.app.state.pipeline


@router.get("/health")
async def health():
    return {"ok": True}


@router.get("/status")
async def status(request: Request):
    return _pipeline(request).status()


@router.get("/metrics")
async def metrics(request: Request):
    p = _pipeline(request)
    if not p.kpis:
        raise HTTPException(status_code=409, detail="No data synced yet. POST /api/sync first.")
    return p.kpis


@router.get("/suggestions")
async def suggestions():
    return {"suggestions": SUGGESTIONS}


@router.post("/sync")
async def sync(request: Request):
    p = _pipeline(request)
    if p.syncing:
        raise HTTPException(status_code=409, detail="A sync is already running.")
    try:
        return await p.sync()
    except Exception as exc:  # surface connector errors to the UI
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/search")
async def search(request: Request, q: str, k: int = 8):
    hits = _pipeline(request).retrieve(q, k)
    return {"query": q, "results": [{"id": d.id, "title": d.title, "kind": d.kind, "score": round(s, 4), "text": d.text}
                                    for d, s in hits]}


@router.post("/chat")
async def chat(request: Request, body: ChatRequest):
    p = _pipeline(request)
    if not p.index or not p.index.documents:
        raise HTTPException(status_code=409, detail="No data synced yet. Run a sync first.")

    async def gen():
        try:
            async for event in p.answer(body.question, [m.model_dump() for m in body.history]):
                yield {"event": event["type"], "data": json.dumps(event, ensure_ascii=False)}
        except Exception as exc:  # pragma: no cover - surfaced to the client
            yield {"event": "error", "data": json.dumps({"type": "error", "message": str(exc)})}

    return EventSourceResponse(gen())
