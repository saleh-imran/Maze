from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from ai_ads.models import Ad


class AdStore:
    def __init__(self, db_path: str = "ads.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        Path(self.db_path).touch(exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    owner_name TEXT NOT NULL,
                    city TEXT NOT NULL,
                    price REAL NOT NULL,
                    discount_percent REAL NOT NULL,
                    source_url TEXT NOT NULL,
                    ad_type TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def add_ad(self, ad: Ad) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO ads (
                    title, description, category, owner_name, city,
                    price, discount_percent, source_url, ad_type, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ad.title,
                    ad.description,
                    ad.category,
                    ad.owner_name,
                    ad.city,
                    ad.price,
                    ad.discount_percent,
                    ad.source_url,
                    ad.ad_type,
                    ad.created_at,
                ),
            )
            return int(cursor.lastrowid)

    def all_ads(self) -> list[sqlite3.Row]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM ads ORDER BY id DESC").fetchall()
        return list(rows)

    def search_candidates(self, text_tokens: Iterable[str], city: str | None = None) -> list[sqlite3.Row]:
        tokens = [t.lower() for t in text_tokens if t]
        rows = self.all_ads()
        filtered = []
        for row in rows:
            if city and row["city"].lower() != city.lower():
                continue
            searchable = f"{row['title']} {row['description']} {row['category']}".lower()
            if not tokens or any(token in searchable for token in tokens):
                filtered.append(row)
        return filtered
