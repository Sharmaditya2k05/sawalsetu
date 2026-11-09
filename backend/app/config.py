"""Runtime configuration, read once from environment variables (.env supported)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(BACKEND_DIR.parent / ".env")


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    return default if value is None or value == "" else value


@dataclass
class Settings:
    # MargBooks Open API
    margbooks_mode: str = field(default_factory=lambda: _env("MARGBOOKS_MODE", "demo"))  # demo | live
    margbooks_base_url: str = field(
        default_factory=lambda: _env("MARGBOOKS_BASE_URL", "https://openapi.margbooks.com/")
    )
    margbooks_mb_key: str = field(default_factory=lambda: _env("MARGBOOKS_MB_KEY"))
    margbooks_partner_id: str = field(default_factory=lambda: _env("MARGBOOKS_PARTNER_ID"))
    sync_months_back: int = field(default_factory=lambda: int(_env("MARGBOOKS_SYNC_MONTHS", "18")))

    # Business identity shown in the UI and used in prompts
    company_name: str = field(default_factory=lambda: _env("COMPANY_NAME", "Shree Balaji Distributors"))

    # LLM provider: auto (groq if GROQ_API_KEY, else claude if ANTHROPIC_API_KEY, else offline) | groq | claude | offline
    llm_provider: str = field(default_factory=lambda: _env("LLM_PROVIDER", "auto"))

    # Groq (free tier at https://console.groq.com) – OpenAI-compatible chat completions
    groq_api_key: str = field(default_factory=lambda: _env("GROQ_API_KEY"))
    groq_model: str = field(default_factory=lambda: _env("GROQ_MODEL", "llama-3.3-70b-versatile"))

    # Claude
    anthropic_api_key: str = field(default_factory=lambda: _env("ANTHROPIC_API_KEY"))
    claude_model: str = field(default_factory=lambda: _env("CLAUDE_MODEL", "claude-opus-5-5"))
    claude_effort: str = field(default_factory=lambda: _env("CLAUDE_EFFORT", "medium"))

    # Embeddings: none (BM25 only) | voyage | local (sentence-transformers)
    embeddings_provider: str = field(default_factory=lambda: _env("EMBEDDINGS_PROVIDER", "none"))
    voyage_api_key: str = field(default_factory=lambda: _env("VOYAGE_API_KEY"))
    voyage_model: str = field(default_factory=lambda: _env("VOYAGE_MODEL", "voyage-3.5-lite"))
    local_embedding_model: str = field(
        default_factory=lambda: _env("LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    )

    # Storage
    data_dir: Path = field(default_factory=lambda: Path(_env("DATA_DIR", str(BACKEND_DIR / "data"))))

    # Retrieval
    top_k: int = field(default_factory=lambda: int(_env("RAG_TOP_K", "12")))

    @property
    def sync_window(self) -> tuple[date, date]:
        today = date.today()
        start = (today.replace(day=1) - timedelta(days=30 * self.sync_months_back)).replace(day=1)
        return start, today

    @property
    def resolved_llm_provider(self) -> str:
        p = self.llm_provider.lower()
        if p == "auto":
            if self.groq_api_key:
                return "groq"
            if self.anthropic_api_key:
                return "claude"
            return "offline"
        if p == "groq" and not self.groq_api_key:
            return "offline"
        if p == "claude" and not self.anthropic_api_key:
            return "offline"
        return p

    @property
    def llm_available(self) -> bool:
        return self.resolved_llm_provider != "offline"


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
