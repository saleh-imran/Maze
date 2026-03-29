from ai_ads.agents import SearchAgentOrchestrator
from ai_ads.models import Ad, SearchRequest
from ai_ads.storage import AdStore


def test_local_search_ranks_discount_and_city(tmp_path):
    db_file = tmp_path / "test_ads.db"
    store = AdStore(str(db_file))
    orchestrator = SearchAgentOrchestrator(store)

    orchestrator.ingest_ad(
        Ad(
            title="Nike Running Shoes",
            description="Comfort sneakers with spring discount",
            category="shoes",
            owner_name="FitMart",
            city="Austin",
            price=80,
            discount_percent=15,
            source_url="https://fitmart.example",
        )
    )
    orchestrator.ingest_ad(
        Ad(
            title="Local sneaker deal",
            description="Budget shoes for running",
            category="shoes",
            owner_name="BudgetShop",
            city="Austin",
            price=50,
            discount_percent=5,
            source_url="https://budget.example",
        )
    )

    result = orchestrator.search(SearchRequest(query="running shoes", city="Austin", budget=90, limit=5))

    assert result["results"], "Expected at least one search result"
    assert result["results"][0]["city"] == "Austin"
    assert result["explain"]["local_ads_found"] == 2
