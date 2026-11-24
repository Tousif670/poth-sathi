# PothSathi — Architecture

> Binding decisions live in [decisions.md](decisions.md).
> Technology choices in [tech-stack.md](tech-stack.md).
> AI details in [ai-spec.md](ai-spec.md).

---

## 1  System Overview

```
┌───────────────────────────────────────────────────────────────┐
│                     Tourist (browser, bn / en)                │
└──────────────────────────────┬────────────────────────────────┘
                               │ HTTPS
              ┌────────────────▼────────────────┐
              │  Next.js Frontend (Vercel Hobby) │
              │  App Router · Tailwind · shadcn  │
              │  next-intl · react-leaflet + OSM │
              │  TanStack Query · Web Speech API │
              │  Tier 0 static fallback pages    │
              └───────┬──────────────┬──────────┘
                      │ REST / JSON  │ Firebase Auth
                      │              │ (login only)
              ┌───────▼──────────┐   │
              │  FastAPI Backend  │   │
              │  (Render free)   │   │
              │                  │   │
              │ ┌──────────────┐ │   │
              │ │ Safety Rules │ │   │   ┌──────────────────┐
              │ │ (pre-LLM)   │ │   │   │ Firebase Auth    │
              │ ├──────────────┤ │   └──►│ (Anonymous,      │
              │ │ Chat Orch.   │ │       │  Google, Email)  │
              │ │  Gemini +    │◄├───────┤                  │
              │ │  Tools       │ │       └──────────────────┘
              │ ├──────────────┤ │
              │ │ RAG Index    │ │       ┌──────────────────┐
              │ │ (in-memory)  │ │       │ Gemini API       │
              │ ├──────────────┤ │◄─────►│ (free tier)      │
              │ │ Repository   │ │       │ GEMINI_MODEL env │
              │ │ Layer        │ │       └──────────────────┘
              │ ├──────────────┤ │
              │ │ TTL Cache    │ │
              │ │ Rate Limiter │ │
              │ └──────────────┘ │
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │ Cloud Firestore  │
              │ (Spark plan)     │
              │                  │
              │ hotels           │
              │ places           │
              │ transport_routes │
              │ beach_status     │
              │ kb_chunks        │
              │ users            │
              │ chat_sessions    │
              │ reviews (P1)     │
              └──────────────────┘
```

### Three tiers (D10)

| Tier | What works | Depends on |
| --- | --- | --- |
| **Tier 0 — Static** | Emergency numbers, fare table, hotel list, place list, beach safety guide, SOS links. Built from `seed/` JSON at Next.js build time. | Nothing — always available. |
| **Tier 1 — Live data** | All Tier 0 data served fresh from FastAPI + Firestore with TTL cache. | Backend up. |
| **Tier 2 — AI Chat** | Full conversational AI with tools and grounded answers. | Backend + Gemini API both up and under quota. |

If a higher tier fails, the lower tier still works and shows "last updated".

---

## 2  Backend Layering (Modular Monolith)

### Layers and dependency direction

```
Allowed direction: top → bottom only.

  ┌──────────────┐
  │  Routers     │   FastAPI route handlers (thin)
  ├──────────────┤
  │  Services    │   Business logic, orchestration
  ├──────────────┤
  │  Repositories│   Firestore reads / writes
  ├──────────────┤
  │  Models      │   Pydantic schemas, shared types
  └──────────────┘
```

**Rules:**
- Routers import Services, never Repositories directly.
- Services import Repositories and Models.
- Repositories import only Models and `google.cloud.firestore`.
- No layer imports from a layer above it.
- Cross-module calls go through Services, never Repositories.

### Module list

| Module | Owns | Key service | Key router prefix |
| --- | --- | --- | --- |
| **auth_profile** | Firebase token verification, user CRUD, role check | `auth_service` | `/api/v1/auth` |
| **chat** | Chat orchestration, message history, AI pipeline | `chat_service` | `/api/v1/chat` |
| **hotels** | Hotel CRUD, recommender, search | `hotel_service` | `/api/v1/hotels` |
| **reviews** | Review CRUD, sentiment analysis (P1) | `review_service` | `/api/v1/hotels/{id}/reviews` |
| **nearby** | Nearby-places search by category and location | `nearby_service` | `/api/v1/places` |
| **transport** | Fare routes, fare calculator | `transport_service` | `/api/v1/transport` |
| **safety** | Beach status, safety rules engine, emergency data | `safety_service` | `/api/v1/safety` |
| **emergency** | Emergency contacts, SOS data | `emergency_service` | `/api/v1/emergency` |
| **admin** | Admin-only data edits, beach flag updates (P1) | `admin_service` | `/api/v1/admin` |
| **health** | Liveness and readiness probes, keep-warm ping | `health_service` | `/api/v1/health` |

### File layout (by layer)

Backend layout is organized by layer (D21):
`backend/app/api/v1` (routers), `backend/app/services`, `backend/app/repositories`, `backend/app/models`, `backend/app/agents`, `backend/app/core`, `backend/app/data`.
The modules named above are logical groups expressed as file names (for example `hotel_service.py`, `hotel_repository.py`, `hotels.py` router), not separate folders.

```
backend/app/
├── api/v1/          # FastAPI routers (e.g. hotels.py, chat.py, transport.py)
├── services/        # Business logic (e.g. hotel_service.py, chat_service.py)
├── repositories/    # Firestore access (e.g. hotel_repository.py)
├── models/          # Pydantic schemas (e.g. hotel.py, chat.py)
├── agents/          # AI tool declarations and executor
├── core/            # Config, auth dependency, LLMClient, rate limiter, errors
└── data/            # Static JSON files (safety_rules.json, lexicons)
```

Shared code lives in `backend/app/core/` (config, auth dependency, LLMClient,
rate limiter, cache, error handling, logging).

---

## 3  Frontend Structure

### Pages (App Router)

```
frontend/src/app/
├── [locale]/
│   ├── page.tsx              # Home — chat panel + quick links
│   ├── hotels/
│   │   ├── page.tsx          # Hotel list with filters
│   │   └── [id]/page.tsx     # Hotel detail + recommender
│   ├── nearby/page.tsx       # Nearby essentials map
│   ├── fares/page.tsx        # Fare table + calculator
│   ├── safety/page.tsx       # Beach safety status
│   ├── emergency/page.tsx    # SOS / emergency screen
│   ├── login/page.tsx        # Login / guest entry
│   └── admin/page.tsx        # Admin panel (P1, protected)
├── layout.tsx
└── not-found.tsx
```

### Component folders

```
frontend/src/components/
├── chat/            # ChatPanel, ChatBubble, VoiceButton
├── hotels/          # HotelCard, HotelFilters, HotelMap
├── nearby/          # NearbyMap, CategoryChips
├── fares/           # FareTable, FareCalculator
├── safety/          # BeachFlag, SafetyTips
├── emergency/       # SOSCard, EmergencyList
├── ui/              # shadcn/ui primitives
└── layout/          # Navbar, BottomTabs, LangToggle, Footer
```

### Context providers

| Provider | Purpose |
| --- | --- |
| `AuthProvider` | Firebase Auth state, current user, role |
| `LocaleProvider` | Current language (bn / en), `next-intl` integration |
| `QueryProvider` | TanStack Query client |

### lib/api

`frontend/src/lib/api.ts` — single fetch wrapper. All calls go to
`NEXT_PUBLIC_API_URL` (the FastAPI backend). Attaches Firebase ID token
in `Authorization: Bearer <token>` header.

### Data fetching pattern

- **TanStack Query** for all API calls (caching, retries, stale-while-revalidate).
- Query keys follow: `[module, action, ...params]`, e.g. `["hotels", "list", { area }]`.
- Mutations use `useMutation` with `onSuccess` cache invalidation.

### Tier 0 static data build

At `next build` time a script reads `seed/*.json` and writes JSON files to
`frontend/public/static/`. Pages like Emergency and Fares import this data
as a fallback when the API is unreachable. The UI shows "last updated" from
the seed file's `last_updated` field.

### State management

No global state library. State lives in:
- TanStack Query cache (server state).
- React context (auth, locale).
- Local component state (form inputs, UI toggles).


---

## 4  Request Flow (one REST call)

Example: `GET /api/v1/hotels?area=kolatoli&max_price_bdt=3000`

```
1. Browser → GET /api/v1/hotels?area=kolatoli&max_price_bdt=3000
   Header: Authorization: Bearer <firebase_id_token>

2. FastAPI middleware: verify Firebase ID token
   → extracts uid, role
   → attaches to request.state

3. Router: api/v1/hotels.py → hotel_service.search(area, max_price_bdt)

4. Service: hotel_service checks TTL cache first
   → cache hit? return cached list (filtered)
   → cache miss? call hotel_repository.find_by_filters(area, max_price_bdt)

5. Repository: hotel_repository queries Firestore
   → SELECT from "hotels" WHERE area == kolatoli AND price_bdt <= 3000
   → returns list[HotelDoc]

6. Service: filters, sorts, converts to response schema
   → updates TTL cache

7. Router: returns 200 with JSON body
   → { "hotels": [...], "count": 3, "cached": false }

8. Frontend: TanStack Query caches the response
```

---

## 5  Authentication Flow

### Auth methods (D3)

| Method | How | When |
| --- | --- | --- |
| Guest | Firebase Anonymous Auth | First visit, no sign-up |
| Google | Firebase Google sign-in | One-tap login |
| Email/password | Firebase email auth | Manual sign-up |

### Token flow

```
1. Frontend calls Firebase Auth SDK (login or anonymous sign-in)
2. Firebase returns an ID token (JWT)
3. Frontend stores the token (Firebase SDK manages refresh)
4. Every API call: frontend attaches
      Authorization: Bearer <id_token>
5. FastAPI auth dependency:
      token = request.headers["Authorization"].split("Bearer ")[1]
      decoded = firebase_admin.auth.verify_id_token(token)
      request.state.uid = decoded["uid"]
      request.state.role = get_user_role(decoded["uid"])  # from Firestore
6. If token is missing or invalid → 401 Unauthorized
7. If role check fails (e.g. admin-only route) → 403 Forbidden
```

### Role check pseudocode

```python
# backend/app/core/auth.py

async def require_auth(request: Request) -> UserContext:
    """FastAPI dependency. Runs on every protected route."""
    token = extract_bearer_token(request)
    if not token:
        raise HTTPException(401, detail={"en": "Login required", "bn": "লগইন প্রয়োজন"})
    try:
        decoded = auth.verify_id_token(token)
    except Exception:
        raise HTTPException(401, detail={"en": "Invalid token", "bn": "অবৈধ টোকেন"})
    role = await user_repository.get_role(decoded["uid"])
    return UserContext(uid=decoded["uid"], role=role)


async def require_admin(user: UserContext = Depends(require_auth)) -> UserContext:
    """FastAPI dependency. Admin-only routes."""
    if user.role != "admin":
        raise HTTPException(403, detail={"en": "Admin only", "bn": "শুধুমাত্র অ্যাডমিন"})
    return user
```

---

## 6  Chat Orchestration Flow

Full step-by-step. See [ai-spec.md](ai-spec.md) for details on each stage.

```
1. VALIDATE    → input length ≤ 2000 chars
               → strip PII patterns (email, phone regex)
               → detect language (Bengali Unicode range check)

2. RATE LIMIT  → check per-user daily counter (≤ 50 / day)
               → check per-IP counter for guests
               → check global daily AI counter
               → if any limit hit → return limit message, no LLM call

3. SAFETY      → run safety rule engine (§4 in ai-spec.md)
               → if match → return pre-written emergency response
               → no Gemini call

4. LLM CALL    → build messages: system prompt + last 10 history + user msg
               → attach tool declarations
               → call LLMClient.chat()

5. TOOL EXEC   → if Gemini returns tool_calls:
                    for each tool_call:
                      validate parameters against JSON schema
                      call the corresponding Service method
                      collect results
                    send tool results back to Gemini
                    Gemini produces final answer

6. GROUNDED    → Gemini answer includes source citations
               → build response JSON (§12 in ai-spec.md)
               → attach cards[] if tool returned structured data

7. SAVE        → save user message + assistant response to chat_sessions
               → async (do not block response)
               → increment per-user and global AI counters

8. RETURN      → send response JSON to frontend
```

### Fallback chain

```
Primary:  Gemini + tools → grounded answer
     ↓ on LLMQuotaError / LLMUnavailableError / LLMTimeoutError
Fallback 1: keyword intent router
     → extract intent from keywords (hotel, fare, nearby, beach, emergency)
     → call the matching Service directly (no LLM)
     → combine with RAG search results
     → return structured answer with "AI-limited" flag
     ↓ if no intent matched or Service fails
Fallback 2: RAG-only search
     → search kb_chunks for relevant content
     → return top chunks as answer
     ↓ if RAG returns nothing above threshold
Fallback 3: "AI is resting" message
     → polite message in detected language
     → bn: "আমাদের AI সহকারী এখন বিশ্রামে আছে। নিচের তথ্যগুলো দেখুন।"
     → en: "Our AI assistant is resting right now. Please browse the
            information below."
     → severity: "info"
     → point user to Tier 0 / Tier 1 static pages
```

---

## 7  Caching Strategy

All caching is in-memory on the backend (no Redis — free tier constraint).

| Data | Cache type | TTL | Invalidation |
| --- | --- | --- | --- |
| Hotel list | Dict with expiry | 10 min | Admin update clears cache |
| Place list | Dict with expiry | 10 min | Admin update clears cache |
| Fare routes | Dict with expiry | 30 min | Admin update clears cache |
| Beach status | Dict with expiry | 2 min | Admin update clears cache |
| KB chunk index | In-memory vectors | Until restart | Restart rebuilds from Firestore |
| User role | Per-request lookup | None | Always fresh |
| Chat history | Not cached | — | Read from Firestore per session |

**Implementation:** A simple `TTLCache` class (dict subclass with timestamps).

```python
class TTLCache:
    def __init__(self, ttl_seconds: int): ...
    def get(self, key: str) -> Any | None: ...
    def set(self, key: str, value: Any) -> None: ...
    def clear(self) -> None: ...
```

---

## 8  Geospatial Search

Used by `find_nearby` to find places near a user's location.

### Haversine distance

```python
import math

def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Return distance in km between two lat/lon points."""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
```

### Search flow

1. Load all places from cache (≤40 documents — small enough for brute force).
2. Filter by category (hospital, pharmacy, ATM, mosque, police).
3. Compute haversine distance from user coordinates to each place.
4. Sort by distance ascending.
5. Return top 5 within a 5 km radius.

**Geohash:** Not needed for MVP. With ≤40 places, brute-force haversine over
the full list is fast enough (<1 ms). Geohash would add complexity without
benefit at this scale. Revisit if the dataset grows past 500 places (Later).

---

## 9  Rate Limiting and Abuse Control

| Limit | Scope | Value | Window | Action when hit |
| --- | --- | --- | --- | --- |
| Chat messages | Per user (uid) | 50 | Calendar day YYYY-MM-DD (Asia/Dhaka UTC+6; D26) | 429 + "daily limit reached" |
| API requests | Per IP (guests) | 100 | 1 h | 429 + "slow down" |
| AI calls | Global (all users) | Configurable via env `DAILY_AI_LIMIT` | Calendar day YYYY-MM-DD (Asia/Dhaka UTC+6; D26) | "AI is resting" for all users |
| Input length | Per message | 2 000 chars | — | 400 + "message too long" |
| Token budget | Per LLM call | 4 096 input / 1 024 output | — | Truncate or reject |

### Implementation

In-memory counters (dict keyed by uid or IP, with timestamps/date strings resetting by calendar date in Asia/Dhaka time per D26). Resets on
backend restart — acceptable for a demo. No Redis needed.

```python
# Pseudocode
rate_limiter = RateLimiter()

@router.post("/api/v1/chat/messages")
async def chat(request: Request, user: UserContext = Depends(require_auth)):
    rate_limiter.check_user(user.uid, limit=50, date_str=today_dhaka)
    rate_limiter.check_ip(request.client.host, limit=100, window_hours=1)
    rate_limiter.check_global_ai(limit=settings.DAILY_AI_LIMIT, date_str=today_dhaka)
    # ... proceed with chat pipeline
```


---

## 10  Error Handling

### Standard error format

Every error response uses one JSON shape:

```json
{
  "error": {
    "code": "GEMINI_UNAVAILABLE",
    "message_en": "Our AI assistant is temporarily unavailable. Please try again shortly.",
    "message_bn": "আমাদের AI সহকারী সাময়িকভাবে অনুপলব্ধ। অনুগ্রহ করে কিছুক্ষণ পর আবার চেষ্টা করুন।",
    "severity": "warning",
    "fallback_available": true
  }
}
```

Fields: `code` (machine-readable), `message_en`, `message_bn` (user-facing),
`severity` (info | warning | error), `fallback_available` (bool).

### Fallback table

| Scenario | Code | Severity | User sees (en) | Fallback |
| --- | --- | --- | --- | --- |
| Gemini down / 503 | `GEMINI_UNAVAILABLE` | warning | "AI assistant is temporarily unavailable." | Keyword + RAG |
| Gemini quota hit / 429 | `GEMINI_QUOTA` | info | "AI assistant is resting. Browse info below." | Keyword + RAG |
| Firestore down | `DB_UNAVAILABLE` | error | "Service temporarily unavailable." | Tier 0 static data |
| RAG returns nothing | `RAG_EMPTY` | info | "I don't have verified info for that." | Gemini answers without RAG context |
| GPS denied by browser | `GPS_DENIED` | info | "Location access denied. Showing all places." | Return full list, no distance sort |
| Speech API unsupported | `SPEECH_UNSUPPORTED` | info | "Voice not supported on this browser. Use text." | Text input always works |
| Rate limit hit | `RATE_LIMITED` | warning | "You've reached the daily limit. Try again tomorrow." | Tier 0/1 pages still work |
| Input too long | `INPUT_TOO_LONG` | warning | "Message too long. Keep it under 2000 characters." | None — user must shorten |

### D19 rule

In `prod`: if Firestore or Gemini keys are missing or invalid, the app
**fails loudly** at startup with a clear error log. It never serves mock
data or silently falls back to empty results in production.

---

## 11  Localization Approach

| Concern | Solution |
| --- | --- |
| UI strings | `next-intl` with JSON files: `messages/bn.json`, `messages/en.json` |
| Route structure | `[locale]/` prefix in App Router (e.g. `/bn/hotels`, `/en/hotels`) |
| Language toggle | `LangToggle` component in nav — switches locale instantly |
| Bengali digits | `next-intl` number formatting + a small `toBengaliDigits()` helper |
| Fonts | Hind Siliguri (primary), Noto Sans Bengali (fallback) via `next/font/google` |
| Backend error messages | Every error includes `message_en` and `message_bn` |
| AI responses | System prompt instructs Gemini to respond in the user's language |
| Safety rule responses | Pre-written in both bn and en, keyed by `response_key` + locale |
| Seed data | Fields like `name` and `description` stored as `{ "bn": "...", "en": "..." }` |
| Date/time display | `Intl.DateTimeFormat` with locale-aware formatting |

One source of truth for translations: `messages/bn.json` and
`messages/en.json`. No other translation files. Backend safety responses
are part of these files (or a shared `translations.json` loaded by both).

---

## 12  Logging and Monitoring

### What we log

| Logged | Example |
| --- | --- |
| Request path and method | `POST /api/v1/chat/messages` |
| Response status code | `200`, `429`, `500` |
| Response time (ms) | `342` |
| Error codes | `GEMINI_UNAVAILABLE` |
| User uid (hashed) | `sha256(uid)[:12]` |
| AI counter values | `global_ai_count: 142 / 500` |
| Cache hit / miss | `hotels_cache: HIT` |
| Startup events | `RAG index built: 58 chunks in 3.2s` |

### What we NEVER log (D14)

| Never logged | Reason |
| --- | --- |
| Chat text / message content | Privacy |
| Request bodies | May contain user input |
| GPS coordinates | Location privacy |
| Email, phone, name | PII |
| Firebase ID tokens | Security |

### Monitoring

- **Health endpoint:** `GET /api/health` returns `{ "status": "ok", "rag_chunks": 58, "ai_quota_remaining": 358 }`.
- **Vercel Analytics:** Built-in (Hobby plan includes Web Analytics).
- **Render logs:** Available in Render dashboard (free tier keeps 7 days).
- **Firebase console:** Auth usage, Firestore read/write counts.
- **AI Studio dashboard:** Gemini API usage, RPM/RPD tracking.
- No external monitoring service (zero budget). Manual dashboard checks.

---

## 13  Deployment View

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Vercel Hobby    │     │  Render Free     │     │  Firebase        │
│                  │     │  (Docker)        │     │  (Spark plan)    │
│  Next.js app     │────►│  FastAPI app     │────►│  Cloud Firestore │
│  Static assets   │     │  RAG in memory   │     │  Firebase Auth   │
│  Tier 0 fallback │     │  TTL cache       │     │                  │
│                  │     │  Rate limiter    │     │                  │
└──────────────────┘     └────────┬─────────┘     └──────────────────┘
                                  │
                         ┌────────▼─────────┐
                         │  Gemini API      │
                         │  (free tier)     │
                         └──────────────────┘
```

### Keep-warm

Render free tier sleeps after 15 min of inactivity. A keep-warm ping
(via UptimeRobot free or similar) hits `GET /api/health` every 14 min
to prevent cold starts. First cold start after deploy: ~1 min (Docker
build + RAG index rebuild).

### Environment variables (names only)

**Backend (`backend/.env.example`):**

| Variable | Purpose |
| --- | --- |
| `APP_ENV` | `dev`, `test`, or `prod` |
| `GEMINI_API_KEY` | Gemini API key |
| `GEMINI_MODEL` | Chat model id |
| `GEMINI_EMBEDDING_MODEL` | Embedding model id |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to Firebase service account JSON |
| `FIREBASE_PROJECT_ID` | Firebase project id |
| `FIRESTORE_EMULATOR_HOST` | Emulator host (dev/test only) |
| `FIREBASE_AUTH_EMULATOR_HOST` | Auth emulator host (dev/test only) |
| `DAILY_AI_LIMIT` | Global daily AI call cap |
| `CORS_ORIGINS` | Allowed frontend origins |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

**Frontend (`frontend/.env.example`):**

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | Backend API base URL |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | Firebase client API key |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | Firebase auth domain |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | Firebase project id |

> **Security:** Real `.env` files and service-account keys are `.gitignore`d.
> Only `.env.example` files are committed.

---

## Open Questions

1. **Keep-warm service:** UptimeRobot free or Vercel cron (Hobby allows 2
   daily cron jobs only, not every 14 min)? Need to pick one. This is not
   addressed in decisions.md.
2. **Admin cache invalidation:** When admin updates data, should it
   invalidate cache via an internal signal or a separate admin endpoint?
   Not specified in decisions.md.
3. **Chat session storage limit:** decisions.md says "30 days at most" but
   does not specify max messages per session or max sessions per user.

---

*End of architecture. ~300 lines.*
