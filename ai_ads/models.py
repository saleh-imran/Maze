from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

AdType = Literal["business", "personal", "brand", "celebrity"]


@dataclass(slots=True)
class Ad:
    title: str
    description: str
    category: str
    owner_name: str
    city: str
    price: float
    discount_percent: float
    source_url: str
    ad_type: AdType = "business"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(slots=True)
class SearchRequest:
    query: str
    city: str | None = None
    budget: float | None = None
    limit: int = 10
