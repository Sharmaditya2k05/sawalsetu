"""Hybrid retrieval index: BM25 (always) + optional dense vectors, fused with RRF."""
from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

from .documents import Document
from .embeddings import Embedder

TOKEN_RE = re.compile(r"[a-z0-9₹%]+")
STOP = {"the", "a", "an", "of", "for", "in", "on", "at", "to", "and", "is", "are", "was", "were", "my", "our", "me",
        "what", "which", "who", "how", "much", "many", "show", "tell", "give", "list", "please", "with", "from", "by",
        "this", "that", "it", "be", "do", "did", "does", "i", "we", "you", "your", "about", "all"}

SYNONYMS = {
    "udhaar": ["outstanding", "pending", "receivable"],
    "udhar": ["outstanding", "pending", "receivable"],
    "dues": ["outstanding", "pending", "receivable"],
    "outstanding": ["pending", "receivable", "unpaid"],
    "receivables": ["outstanding", "pending", "unpaid"],
    "unpaid": ["pending", "outstanding"],
    "revenue": ["sales"],
    "turnover": ["sales"],
    "sale": ["sales"],
    "bikri": ["sales"],
    "kharid": ["purchase", "purchases"],
    "buying": ["purchase", "purchases"],
    "vendor": ["supplier"],
    "vendors": ["supplier"],
    "suppliers": ["supplier"],
    "customers": ["customer"],
    "client": ["customer"],
    "clients": ["customer"],
    "party": ["customer", "supplier"],
    "parties": ["customer", "supplier"],
    "debtors": ["receivables", "outstanding"],
    "creditors": ["payable", "supplier"],
    "payables": ["payable"],
    "stock": ["item", "catalogue"],
    "inventory": ["item", "catalogue"],
    "products": ["item"],
    "product": ["item"],
    "sku": ["item"],
    "margin": ["margin", "mrp", "cost"],
    "profit": ["margin", "gap"],
    "online": ["e-commerce", "amazon", "flipkart", "meesho"],
    "ecommerce": ["e-commerce"],
    "marketplace": ["e-commerce"],
    "ageing": ["ageing", "receivables"],
    "aging": ["ageing", "receivables"],
    "overdue": ["overdue", "pending", "outstanding"],
    "biggest": ["top", "rank"],
    "largest": ["top", "rank"],
    "best": ["top", "rank"],
    "highest": ["top", "rank"],
    "growth": ["versus", "previous", "month"],
    "trend": ["monthly", "summary"],
    "summary": ["snapshot", "summary"],
    "overview": ["snapshot", "summary"],
    "business": ["snapshot"],
    "performance": ["summary", "snapshot"],
    "month": ["monthly"],
    "returns": ["return"],
}

MONTH_WORDS = {"jan": "january", "feb": "february", "mar": "march", "apr": "april", "jun": "june", "jul": "july",
               "aug": "august", "sep": "september", "sept": "september", "oct": "october", "nov": "november",
               "dec": "december"}


def _stem(token: str) -> str:
    """Truncation stemming: consistent on both sides, so 'pharma' matches 'pharmaceutical',
    'customer' matches 'customers', 'purchase' matches 'purchases'."""
    return token[:6] if len(token) > 6 and not token.isdigit() else token


def tokenize(text: str, expand: bool = False) -> list[str]:
    tokens = [t for t in TOKEN_RE.findall(text.lower()) if t not in STOP]
    if not expand:
        return [_stem(t) for t in tokens]
    out: list[str] = []
    for t in tokens:
        out.append(_stem(MONTH_WORDS.get(t, t)))
        out.extend(_stem(s) for s in SYNONYMS.get(t, []))
    return out


class HybridIndex:
    def __init__(self, documents: list[Document], embedder: Embedder | None = None, vectors: np.ndarray | None = None):
        self.documents = documents
        self.embedder = embedder
        self._bm25 = BM25Okapi([tokenize(d.title + " " + d.text) for d in documents]) if documents else None
        self.vectors = vectors
        if embedder is not None and vectors is None and documents:
            self.vectors = embedder.embed([d.title + ". " + d.text for d in documents])

    # -- persistence ------------------------------------------------------------
    def save(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "documents.json").write_text(
            json.dumps([asdict(d) for d in self.documents], ensure_ascii=False), encoding="utf-8"
        )
        if self.vectors is not None:
            np.save(directory / "vectors.npy", self.vectors)
        elif (directory / "vectors.npy").exists():
            (directory / "vectors.npy").unlink()

    @classmethod
    def load(cls, directory: Path, embedder: Embedder | None = None) -> "HybridIndex | None":
        path = directory / "documents.json"
        if not path.exists():
            return None
        docs = [Document(**d) for d in json.loads(path.read_text(encoding="utf-8"))]
        vectors = None
        if embedder is not None and (directory / "vectors.npy").exists():
            vectors = np.load(directory / "vectors.npy")
            if vectors.shape[0] != len(docs):
                vectors = None
        return cls(docs, embedder=embedder, vectors=vectors)

    # -- search ----------------------------------------------------------------
    def search(self, query: str, k: int = 12) -> list[tuple[Document, float]]:
        """Hybrid search with a two-tier result set.

        Aggregate questions ("top customers", "sales last month") are answered by the
        pre-computed analytics documents, while specifics ("bill SB/26/2606") live in record
        documents. Scoring both together lets hundreds of near-identical invoices crowd out
        the one summary that holds the answer, so we rank each tier separately and reserve
        roughly half of k for each, back-filling when one tier has too few hits.
        """
        if not self.documents or self._bm25 is None:
            return []
        n = len(self.documents)
        pool = min(n, max(60, k * 6))

        bm25_scores = self._bm25.get_scores(tokenize(query, expand=True))
        fused: dict[int, float] = {}
        for rank, idx in enumerate(np.argsort(-bm25_scores)[:pool]):
            if bm25_scores[idx] <= 0:
                break
            fused[int(idx)] = fused.get(int(idx), 0.0) + 1.0 / (60 + rank)

        if self.vectors is not None and self.embedder is not None:
            q = self.embedder.embed([query], kind="query")[0]
            sims = self.vectors @ q
            for rank, idx in enumerate(np.argsort(-sims)[:pool]):
                fused[int(idx)] = fused.get(int(idx), 0.0) + 1.0 / (60 + rank)

        ranked = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)
        analytics = [(i, s) for i, s in ranked if self.documents[i].kind == "analytics"]
        records = [(i, s) for i, s in ranked if self.documents[i].kind != "analytics"]

        k_analytics = min(len(analytics), (k + 1) // 2)
        k_records = min(len(records), k - k_analytics)
        k_analytics = min(len(analytics), k - k_records)  # back-fill if few records matched
        chosen = analytics[:k_analytics] + records[:k_records]
        return [(self.documents[i], score) for i, score in chosen]
