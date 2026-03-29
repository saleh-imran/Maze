# AI Ads / Offers Prototype (Apple + Android ready backend)

This repo now includes a **working backend prototype** for your idea:
- Public users search offers like chatting with an AI assistant.
- Businesses and personal profiles can post ads for free.
- Search combines local posted ads + live external product offers (free API source).
- Architecture is designed to evolve toward a multi-agent shopping broker.

## 1) Product structure (step-by-step)

### Phase 1 — MVP (what is implemented here)
1. **Ad ingestion API** (`POST /ads`) for businesses/personal profiles.
2. **Search API** (`POST /search`) with AI-like query input.
3. **Local storage** in SQLite for fast prototyping.
4. **Offer crawler adapter** from free sources (`dummyjson`) to simulate internet shopping crawl.
5. **Ranking engine** that prioritizes keyword match, discount, city match, budget fit.

### Phase 2 — Mobile apps
- Build with **React Native + Expo** for one codebase to ship to iOS and Android.
- Screens:
  - Home feed (TikTok-style ad cards)
  - AI search chat bar
  - Nearby offers map/list
  - Business profile dashboard
  - Saved/following profiles

### Phase 3 — Scalable backend
- Replace SQLite with PostgreSQL + Redis caching.
- Add queue workers (Celery/RQ + Redis) for continuous crawling and profile indexing.
- Add vector search (pgvector / Qdrant) for semantic matching.

### Phase 4 — Agentic shopping support
- Split orchestrator into specialized agents:
  - Query understanding agent
  - Deal discovery agent
  - Price comparison agent
  - Local inventory agent
  - Personalization agent
- One supervisor agent coordinates them and returns the best action plan.

## 2) Current prototype architecture

- `app.py` : HTTP API server.
- `ai_ads/models.py` : core models (`Ad`, `SearchRequest`).
- `ai_ads/storage.py` : SQLite storage and filtering.
- `ai_ads/agents.py` : orchestrator, ranking, external crawl adapter.
- `tests/test_agents.py` : ranking/search test.

## 3) Run locally

```bash
python3 app.py
```

Server starts on `http://localhost:8000`.

## 4) API usage

### Health
```bash
curl http://localhost:8000/health
```

### Create ad (free ad posting)
```bash
curl -X POST http://localhost:8000/ads \
  -H "Content-Type: application/json" \
  -d '{
    "title":"50% Off Salon Package",
    "description":"Hair spa + haircut this weekend",
    "category":"beauty",
    "owner_name":"Glow Studio",
    "city":"San Jose",
    "price":79,
    "discount_percent":50,
    "source_url":"https://glow.example",
    "ad_type":"business"
  }'
```

### AI-like search
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query":"cheap running shoes discounts",
    "city":"San Jose",
    "budget":100,
    "limit":10
  }'
```

## 5) Open-source + free API strategy

Use free tiers first, then upgrade only when needed:
- Crawling/search seeds: `dummyjson`, `fakestoreapi`, public merchant feeds.
- Maps/local discovery: OpenStreetMap/Nominatim.
- Identity: Auth.js/Clerk free tiers or Supabase auth.
- Storage: Supabase/Postgres free tier.
- Push notifications: Firebase Cloud Messaging.
- LLM layer: open-source models via Ollama/vLLM for cost control.

## 6) Immediate next build steps

1. Add user accounts (public, business, personal creator).
2. Add follow/unfollow profiles and personalized feed ranking.
3. Add moderation and anti-spam checks for ad uploads.
4. Add location-aware retrieval + deduplicated offers.
5. Add a React Native client hitting these endpoints.

This gives you a realistic path to launch quickly, then evolve into a true AI shopping broker platform.

## 7) Live test now (end-to-end)

### Fastest smoke test (one command)

```bash
bash scripts/live_test.sh
```

This script will:
1. Start the API server.
2. Call `/health`.
3. Create a sample ad.
4. List ads.
5. Run `/search` and print JSON responses.

### Manual live test (step-by-step)

Terminal A:
```bash
python3 app.py
```

Terminal B:
```bash
curl http://127.0.0.1:8000/health
```

```bash
curl -X POST http://127.0.0.1:8000/ads \
  -H "Content-Type: application/json" \
  -d '{
    "title":"50% Off Coffee",
    "description":"Local cafe weekend offer",
    "category":"food",
    "owner_name":"Cafe One",
    "city":"Austin",
    "price":10,
    "discount_percent":50,
    "source_url":"https://cafe.example",
    "ad_type":"business"
  }'
```

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query":"cheap coffee discounts",
    "city":"Austin",
    "budget":20,
    "limit":5
  }'
```

### Test from a real phone (iOS/Android)
- Keep backend running on your laptop.
- Expose localhost with a tunnel tool (for example `ngrok` or `cloudflared`).
- Open the tunnel URL from your phone browser or your React Native app and call the same endpoints.
