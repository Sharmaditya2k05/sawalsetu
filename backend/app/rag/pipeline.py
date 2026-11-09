"""Orchestrates sync (fetch -> documents -> index) and question answering."""
from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import AsyncIterator

from ..config import Settings
from ..margbooks.source import build_source, load_snapshot, save_snapshot
from .documents import Document, build_documents
from .embeddings import build_embedder
from .index import HybridIndex
from .llm import build_answerer
from .query import expand_time_phrases

log = logging.getLogger(__name__)


class Pipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.data_dir: Path = settings.data_dir
        self.snapshot_path = self.data_dir / "snapshot.json"
        self.meta_path = self.data_dir / "meta.json"
        self.index_dir = self.data_dir / "index"
        self.embedder = build_embedder(settings)
        self.answerer = build_answerer(settings)
        self.index: HybridIndex | None = None
        self.kpis: dict = {}
        self.meta: dict = {}
        self._sync_lock = asyncio.Lock()
        self.syncing = False
        self._load()

    # -- state ------------------------------------------------------------------
    def _load(self) -> None:
        if self.meta_path.exists():
            self.meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
            self.kpis = self.meta.get("kpis", {})
        if self.meta and self.kpis:
            self.index = HybridIndex.load(self.index_dir, self.embedder)
        # No usable index/meta pair on disk: rebuild everything from the last snapshot if we have one.
        if self.index is None and (snap := load_snapshot(self.snapshot_path)):
            self._build_index(snap)
            self._write_meta(snap, source="snapshot", duration_s=0.0,
                             last_sync=self.meta.get("last_sync") or datetime.now(timezone.utc).isoformat())

    def _write_meta(self, data: dict[str, list[dict]], source: str, duration_s: float, last_sync: str | None = None) -> None:
        start, end = self.settings.sync_window
        self.meta = {
            "last_sync": last_sync or datetime.now(timezone.utc).isoformat(),
            "sync_window": self.meta.get("sync_window") or {"from": start.isoformat(), "to": end.isoformat()},
            "source": source,
            "counts": {k: len(v) for k, v in data.items() if isinstance(v, list)},
            "kpis": self.kpis,
            "duration_s": round(duration_s, 2),
        }
        self.meta_path.write_text(json.dumps(self.meta, ensure_ascii=False, default=str), encoding="utf-8")

    def _build_index(self, data: dict[str, list[dict]]) -> None:
        docs, kpis = build_documents(data, self.settings.company_name, date.today())
        self.index = HybridIndex(docs, embedder=self.embedder)
        self.index.save(self.index_dir)
        self.kpis = kpis

    def status(self) -> dict:
        counts = self.meta.get("counts", {})
        return {
            "company": self.settings.company_name,
            "mode": self.settings.margbooks_mode,
            "source": "MargBooks Open API" if self.settings.margbooks_mode == "live" else "Demo dataset (MargBooks schema)",
            "base_url": self.settings.margbooks_base_url if self.settings.margbooks_mode == "live" else None,
            "llm": {"provider": self.answerer.name, "model": getattr(self.answerer, "model", None)},
            "embeddings": self.embedder.name if self.embedder else "bm25-only",
            "documents": len(self.index.documents) if self.index else 0,
            "last_sync": self.meta.get("last_sync"),
            "sync_window": self.meta.get("sync_window"),
            "counts": counts,
            "syncing": self.syncing,
            "ready": self.index is not None and len(self.index.documents) > 0,
        }

    # -- sync -------------------------------------------------------------------
    async def sync(self) -> dict:
        async with self._sync_lock:
            self.syncing = True
            started = time.perf_counter()
            try:
                source = build_source(self.settings)
                start, end = self.settings.sync_window
                data = await asyncio.to_thread(source.fetch, start, end)
                save_snapshot(data, self.snapshot_path)
                await asyncio.to_thread(self._build_index, data)
                self.meta["sync_window"] = {"from": start.isoformat(), "to": end.isoformat()}
                self._write_meta(data, source=source.name, duration_s=time.perf_counter() - started)
                return self.status()
            finally:
                self.syncing = False

    # -- answer -----------------------------------------------------------------
    def retrieve(self, question: str, k: int | None = None) -> list[tuple[Document, float]]:
        if not self.index:
            return []
        return self.index.search(expand_time_phrases(question), k or self.settings.top_k)

    async def answer(self, question: str, history: list[dict]) -> AsyncIterator[dict]:
        hits = self.retrieve(question)
        docs = [d for d, _ in hits]
        yield {
            "type": "sources",
            "sources": [
                {"n": i + 1, "id": d.id, "title": d.title, "kind": d.kind, "text": d.text, "score": round(score, 4),
                 "metadata": d.metadata}
                for i, (d, score) in enumerate(hits)
            ],
        }
        async for event in self.answerer.stream(question, docs, history):
            yield event
