"""Data source abstraction: live MargBooks API or the built-in demo dataset."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from ..config import Settings
from . import demo
from .client import MargBooksClient


class DataSource:
    name = "base"

    def fetch(self, start: date, end: date) -> dict[str, list[dict]]:  # pragma: no cover - interface
        raise NotImplementedError


class LiveMargBooksSource(DataSource):
    name = "margbooks-live"

    def __init__(self, settings: Settings):
        self.client = MargBooksClient(
            settings.margbooks_base_url, settings.margbooks_mb_key, settings.margbooks_partner_id
        )

    def fetch(self, start: date, end: date) -> dict[str, list[dict]]:
        return self.client.fetch_everything(start, end)


class DemoSource(DataSource):
    name = "demo"

    def fetch(self, start: date, end: date) -> dict[str, list[dict]]:
        return demo.generate(start, end)


def build_source(settings: Settings) -> DataSource:
    if settings.margbooks_mode.lower() == "live":
        return LiveMargBooksSource(settings)
    return DemoSource()


def save_snapshot(data: dict[str, list[dict]], path: Path) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, default=str), encoding="utf-8")


def load_snapshot(path: Path) -> dict[str, list[dict]] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
