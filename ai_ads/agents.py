from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import asdict

from ai_ads.models import Ad, SearchRequest
from ai_ads.storage import AdStore


class SearchAgentOrchestrator:
    """One orchestrator that can later split into specialist agents."""

    def __init__(self, store: AdStore) -> None:
        self.store = store

    def ingest_ad(self, ad: Ad) -> int:
        return self.store.add_ad(ad)

    def search(self, request: SearchRequest) -> dict:
        tokens = [part.strip() for part in request.query.lower().split() if part.strip()]
        local_candidates = self.store.search_candidates(tokens, city=request.city)

        ranked_local = []
        for row in local_candidates:
            score = self._score_local(row=row, request=request, tokens=tokens)
            ranked_local.append({"source": "local", "score": score, **dict(row)})

        ranked_local.sort(key=lambda item: item["score"], reverse=True)

        external_offers = self._crawl_external_offers(request.query, request.limit)
        merged = ranked_local[: request.limit] + external_offers
        merged.sort(key=lambda item: item.get("score", 0.0), reverse=True)

        return {
            "query": request.query,
            "city": request.city,
            "results": merged[: request.limit],
            "explain": {
                "local_ads_found": len(local_candidates),
                "external_offers_found": len(external_offers),
                "ranking": "keyword overlap + discount + city match + budget fitness",
            },
        }

    def _score_local(self, row: dict, request: SearchRequest, tokens: list[str]) -> float:
        text = f"{row['title']} {row['description']} {row['category']}".lower()
        overlap = sum(1 for token in tokens if token in text)
        discount_boost = float(row["discount_percent"]) / 10.0
        city_boost = 1.5 if request.city and row["city"].lower() == request.city.lower() else 0.0

        budget_boost = 0.0
        if request.budget is not None:
            budget_gap = max(0.0, request.budget - float(row["price"]))
            budget_boost = min(2.0, budget_gap / 50.0)

        return overlap + discount_boost + city_boost + budget_boost

    def _crawl_external_offers(self, query: str, limit: int) -> list[dict]:
        """Free-source example: DummyJSON product search (no API key)."""
        try:
            encoded_q = urllib.parse.quote_plus(query)
            url = f"https://dummyjson.com/products/search?q={encoded_q}&limit={max(1, limit)}"
            with urllib.request.urlopen(url, timeout=4) as response:
                payload = json.load(response)

            offers = []
            for item in payload.get("products", []):
                offers.append(
                    {
                        "source": "external",
                        "provider": "dummyjson",
                        "title": item.get("title", "Unknown"),
                        "description": item.get("description", ""),
                        "price": item.get("price", 0),
                        "discount_percent": item.get("discountPercentage", 0),
                        "score": float(item.get("rating", 0)) + float(item.get("discountPercentage", 0)) / 10.0,
                        "source_url": "https://dummyjson.com/",
                    }
                )
            return offers
        except Exception:
            return []


def ad_from_dict(payload: dict) -> Ad:
    return Ad(
        title=payload["title"],
        description=payload.get("description", ""),
        category=payload.get("category", "general"),
        owner_name=payload.get("owner_name", "anonymous"),
        city=payload.get("city", "global"),
        price=float(payload.get("price", 0)),
        discount_percent=float(payload.get("discount_percent", 0)),
        source_url=payload.get("source_url", "https://example.com"),
        ad_type=payload.get("ad_type", "business"),
    )


def search_from_dict(payload: dict) -> SearchRequest:
    return SearchRequest(
        query=payload["query"],
        city=payload.get("city"),
        budget=float(payload["budget"]) if payload.get("budget") is not None else None,
        limit=int(payload.get("limit", 10)),
    )


def to_json(data: dict) -> bytes:
    return json.dumps(data, indent=2, default=lambda obj: asdict(obj)).encode("utf-8")
