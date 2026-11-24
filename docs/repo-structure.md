# PothSathi — Repository Structure

> Binding decisions: [decisions.md](decisions.md).
> Architecture: [architecture.md](architecture.md).

---

## 1  Naming Conventions

| Item | Convention | Example |
| --- | --- | --- |
| Folders | `snake_case` (backend), `kebab-case` or `camelCase` (frontend per Next.js convention) | `auth_profile/`, `components/chat/` |
| Python files | `snake_case.py` | `hotel_service.py` |
| TypeScript files | `camelCase.ts` for utils, `PascalCase.tsx` for components | `api.ts`, `HotelCard.tsx` |
| Pydantic models | `PascalCase` class name in `schemas.py` | `HotelResponse` |
| API routes | `/api/v1/{resource}` | `/api/v1/hotels` |
| Env files | `.env.example` committed; `.env` and `.env.local` git-ignored | `backend/.env.example` |
| Seed files | `snake_case.json` in `seed/` | `hotels.json` |
| Test files | `test_*.py` (backend), `*.test.ts` (frontend) | `test_hotel_service.py` |

---

## 2  Full Monorepo Tree

```
poth-sathi/
│
├── README.md                           # Project overview, setup instructions
├── .gitignore                          # Ignores .env, .venv, node_modules, service-account keys
├── firebase.json                       # Firebase project config (emulators, rules, indexes)
├── firestore.rules                     # Security rules: deny all client access
├── firestore.indexes.json              # Composite index definitions
├── .firebaserc                         # Firebase project alias
│
├── docs/                               # All project documentation
│   ├── decisions.md                    # Single source of truth for all decisions
│   ├── overview.md                     # Bird's-eye project overview
│   ├── tech-stack.md                   # Technology choices, versions, rationale
│   ├── architecture.md                 # System architecture, layers, flows
│   ├── ai-spec.md                      # AI pipeline, tools, RAG, prompts, guardrails
│   ├── firestore-schema.md             # Firestore collections, fields, indexes, estimates
│   ├── data-plan.md                    # Data inventory, seed templates, collection checklist
│   ├── repo-structure.md               # This file — repo layout and conventions
│   ├── build-plan.md                   # Ordered build slices and session plan (TODO)
│   └── evaluation-and-report.md        # Evaluation plan, test prompts, metrics (TODO)
│
├── seed/                               # Verified seed data (JSON)
│   ├── hotels.json                     # Hotel reference data (15–25 entries)
│   ├── places.json                     # Nearby essentials (30–40 entries)
│   ├── transport_routes.json           # Fare routes (10–15 entries)
│   ├── kb_chunks.json                  # Knowledge-base chunks without embeddings
│   ├── beach_status.json               # Initial beach flags (3 zones: kolatoli, sugandha, laboni; D23)
│   ├── emergency_contacts.json         # Emergency numbers for Tier 0 static build
│   └── safety_rules.json              # Safety rule engine keywords and categories
│
├── scripts/                            # Utility scripts
│   ├── seed_loader.py                  # Reads seed/*.json, writes to Firestore (or emulator)
│   ├── compute_embeddings.py           # Computes embeddings for kb_chunks via Gemini API
│   ├── build_tier0.py                  # Builds Tier 0 static JSON for frontend/public/static/
│   ├── cleanup_expired_chats.py        # Deletes chat messages past expires_at (manual run)
│   └── verify_seed.py                  # Validates seed files against expected schema
│
├── backend/                            # FastAPI application
│   ├── .env.example                    # Template: API keys, project id, model names
│   ├── Dockerfile                      # Docker build for Render deployment
│   ├── requirements.txt                # Python dependencies (pinned versions)
│   ├── pyproject.toml                  # Project metadata and tool config
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI app factory, startup events, middleware
│   │   │
│   │   ├── core/                       # Shared infrastructure (no business logic)
│   │   │   ├── __init__.py
│   │   │   ├── config.py               # Settings from env (APP_ENV, keys, limits)
│   │   │   ├── auth.py                 # require_auth, require_admin dependencies
│   │   │   ├── firebase.py             # Firebase Admin SDK init, Firestore client
│   │   │   ├── llm_client.py           # LLMClient wrapper for Gemini API
│   │   │   ├── cache.py                # TTLCache class (in-memory dict with expiry)
│   │   │   ├── rate_limiter.py         # RateLimiter (per-user, per-IP, global AI)
│   │   │   ├── errors.py               # Custom exceptions, standard error format
│   │   │   └── logging.py              # Structured logging setup (never logs PII)
│   │   │
│   │   ├── models/                     # Pydantic schemas shared across modules
│   │   │   ├── __init__.py
│   │   │   ├── common.py               # BilingualText, MetadataFields, ErrorResponse
│   │   │   ├── hotel.py                # HotelDoc, HotelResponse, HotelSearchParams
│   │   │   ├── place.py                # PlaceDoc, PlaceResponse
│   │   │   ├── transport.py            # RouteDoc, FareResponse, FareCalcRequest
│   │   │   ├── chat.py                 # ChatRequest, ChatResponse, Message
│   │   │   ├── safety.py               # BeachStatusDoc, SOSEvent, SafetyRule
│   │   │   ├── user.py                 # UserDoc, UserContext
│   │   │   ├── review.py               # ReviewDoc, ReviewResponse, SentimentResult
│   │   │   └── admin.py                # AuditLog, ReportDoc
│   │   │
│   │   ├── services/                   # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── hotel_service.py        # Hotel search, recommender scoring
│   │   │   ├── nearby_service.py       # Nearby places search, haversine distance
│   │   │   ├── transport_service.py    # Fare lookup, calculate_fare logic
│   │   │   ├── chat_service.py         # Chat orchestration: validate → safety → LLM → save
│   │   │   ├── safety_service.py       # Beach status, safety rule engine
│   │   │   ├── rag_service.py          # RAG index build, search, keyword fallback
│   │   │   ├── review_service.py       # Review CRUD, sentiment analysis (P1)
│   │   │   ├── auth_service.py         # User upsert on login, role check
│   │   │   ├── emergency_service.py    # SOS event creation, emergency contacts
│   │   │   ├── admin_service.py        # Admin data edits, audit logging (P1)
│   │   │   └── health_service.py       # Health check, RAG status, quota remaining
│   │   │
│   │   ├── agents/                     # AI tool declarations for Gemini function calling
│   │   │   ├── __init__.py
│   │   │   ├── tool_declarations.py    # search_hotels, find_nearby, calculate_fare,
│   │   │   │                           #   get_beach_status, search_knowledge
│   │   │   └── tool_executor.py        # Dispatches tool calls to service methods
│   │   │
│   │   ├── repositories/              # Firestore access layer
│   │   │   ├── __init__.py
│   │   │   ├── hotel_repository.py     # Hotels collection CRUD
│   │   │   ├── place_repository.py     # Places collection CRUD
│   │   │   ├── transport_repository.py # Transport routes collection CRUD
│   │   │   ├── chat_repository.py      # Chat sessions + messages subcollection
│   │   │   ├── safety_repository.py    # Beach status + SOS events
│   │   │   ├── kb_repository.py        # KB chunks read (startup load)
│   │   │   ├── user_repository.py      # Users collection CRUD
│   │   │   ├── usage_repository.py     # Usage + AI usage counters
│   │   │   ├── review_repository.py    # Reviews subcollection (P1)
│   │   │   ├── report_repository.py    # Reports collection (P1)
│   │   │   └── admin_repository.py     # Admin audit log (P1)
│   │   │
│   │   ├── api/
│   │   │   └── v1/                     # Versioned API routes
│   │   │       ├── __init__.py
│   │   │       ├── hotels.py           # GET /api/v1/hotels, GET /api/v1/hotels/{id}
│   │   │       ├── nearby.py           # GET /api/v1/places
│   │   │       ├── transport.py        # GET /api/v1/transport/fares, GET /api/v1/transport/calculate
│   │   │       ├── chat.py             # POST /api/v1/chat/messages
│   │   │       ├── safety.py           # GET /api/v1/safety/beach-status
│   │   │       ├── emergency.py        # GET /api/v1/emergency/contacts, POST /api/v1/emergency/sos
│   │   │       ├── auth.py             # POST /api/v1/auth/register, GET /api/v1/me
│   │   │       ├── reviews.py          # GET/POST /api/v1/hotels/{id}/reviews (P1)
│   │   │       ├── admin.py            # Admin endpoints (P1, require_admin)
│   │   │       ├── reports.py          # POST /api/v1/reports (P1)
│   │   │       └── health.py           # GET /api/v1/health
│   │   │
│   │   └── data/                       # Static data loaded at startup
│   │       ├── safety_rules.json       # Copy of seed/safety_rules.json for runtime
│   │       ├── lexicon_en.json         # Sentiment lexicon — English (P1)
│   │       └── lexicon_bn.json         # Sentiment lexicon — Bengali (P1)
│   │
│   └── tests/                          # Backend tests
│       ├── __init__.py
│       ├── conftest.py                 # Shared fixtures, FakeLLMClient, emulator setup
│       ├── test_hotel_service.py       # Hotel search + recommender tests
│       ├── test_transport_service.py   # Fare calculation tests
│       ├── test_chat_service.py        # Chat pipeline tests (safety, tools, fallback)
│       ├── test_safety_service.py      # Safety rule engine tests
│       ├── test_rag_service.py         # RAG search + keyword fallback tests
│       ├── test_rate_limiter.py        # Rate limiting tests
│       └── test_auth.py               # Auth dependency tests
│
├── frontend/                           # Next.js application
│   ├── .env.example                    # Template: API URL, Firebase client config
│   ├── package.json                    # Node dependencies
│   ├── tsconfig.json                   # TypeScript config (strict mode)
│   ├── tailwind.config.ts              # Tailwind config with Hind Siliguri font
│   ├── next.config.ts                  # Next.js config (i18n, images, rewrites)
│   │
│   ├── public/
│   │   ├── static/                     # Tier 0 static JSON (built by scripts/build_tier0.py)
│   │   │   ├── hotels.json
│   │   │   ├── places.json
│   │   │   ├── fares.json
│   │   │   └── emergency.json
│   │   └── icons/                      # Favicon, map markers, PWA icons (Later)
│   │
│   └── src/
│       ├── app/
│       │   ├── layout.tsx              # Root layout: fonts, metadata, providers
│       │   ├── not-found.tsx           # 404 page
│       │   └── [locale]/              # Locale-prefixed routes (bn, en)
│       │       ├── page.tsx            # Home — chat panel + quick links
│       │       ├── layout.tsx          # Locale layout with next-intl provider
│       │       ├── hotels/
│       │       │   ├── page.tsx        # Hotel list with filters
│       │       │   └── [id]/
│       │       │       └── page.tsx    # Hotel detail + recommender
│       │       ├── nearby/
│       │       │   └── page.tsx        # Nearby essentials map
│       │       ├── fares/
│       │       │   └── page.tsx        # Fare table + calculator
│       │       ├── safety/
│       │       │   └── page.tsx        # Beach safety status
│       │       ├── emergency/
│       │       │   └── page.tsx        # SOS / emergency screen
│       │       ├── login/
│       │       │   └── page.tsx        # Login / guest entry
│       │       └── admin/
│       │           └── page.tsx        # Admin panel (P1, protected route)
│       │
│       ├── components/
│       │   ├── chat/
│       │   │   ├── ChatPanel.tsx       # Main chat container
│       │   │   ├── ChatBubble.tsx      # Single message bubble
│       │   │   └── VoiceButton.tsx     # Voice input toggle (P1)
│       │   ├── hotels/
│       │   │   ├── HotelCard.tsx       # Hotel summary card
│       │   │   ├── HotelFilters.tsx    # Area, price, amenity filters
│       │   │   └── HotelMap.tsx        # Map with hotel pins
│       │   ├── nearby/
│       │   │   ├── NearbyMap.tsx       # Full-width OSM map
│       │   │   └── CategoryChips.tsx   # Category filter chips
│       │   ├── fares/
│       │   │   ├── FareTable.tsx       # Route/fare table
│       │   │   └── FareCalculator.tsx  # Origin + destination fare calc
│       │   ├── safety/
│       │   │   ├── BeachFlag.tsx       # Flag colour display
│       │   │   └── SafetyTips.tsx      # Safety advice cards
│       │   ├── emergency/
│       │   │   ├── SOSCard.tsx         # Emergency number card with tel: link
│       │   │   └── EmergencyList.tsx   # List of emergency contacts
│       │   ├── ui/                     # shadcn/ui primitives (Button, Card, Input…)
│       │   └── layout/
│       │       ├── Navbar.tsx          # Top navigation (desktop)
│       │       ├── BottomTabs.tsx      # Bottom tab bar (mobile)
│       │       ├── LangToggle.tsx      # Language switch button (bn ↔ en)
│       │       └── Footer.tsx          # Footer with attribution and disclaimer
│       │
│       ├── context/
│       │   ├── AuthProvider.tsx        # Firebase Auth state, current user, role
│       │   ├── LocaleProvider.tsx      # Current language, next-intl integration
│       │   └── QueryProvider.tsx       # TanStack Query client setup
│       │
│       ├── lib/
│       │   ├── api.ts                  # Single fetch wrapper, attaches Bearer token
│       │   ├── firebase.ts             # Firebase client SDK init (Auth only)
│       │   ├── utils.ts                # toBengaliDigits(), formatDate(), etc.
│       │   └── staticData.ts           # Loads Tier 0 JSON from public/static/
│       │
│       └── messages/
│           ├── bn.json                 # Bengali UI translations (single source)
│           └── en.json                 # English UI translations (single source)
│
└── .github/
    └── workflows/
        ├── ci.yml                      # Lint + test on push/PR (backend + frontend)
        └── deploy.yml                  # Deploy backend to Render, frontend to Vercel (TODO)
```

---

## 3  Notes

- **Documentation files:** `build-plan.md` and `firestore-schema.md` are complete (C11).
- **`backend/app/data/`** holds runtime copies of `safety_rules.json` and sentiment lexicons. These are loaded at startup, not at build time.
- **`frontend/public/static/`** is generated by `scripts/build_tier0.py` from `seed/` files. These files are committed so the Tier 0 fallback works even without running the script.
- **`api/v1/`** prefix: Standardized on `/api/v1/` across all documents per D25.
- **The `admin/` route** is protected by `require_admin` on the backend and a role check in the frontend `AuthProvider`.

---

## 4  Coding Agent Rules

Proposed content for a rules file (e.g., `.gemini/rules.md` or `.cursor/rules.md`) that guides AI coding agents working on this project:

```markdown
# PothSathi — Coding Agent Rules

1. Read docs/decisions.md before every session. It is the single source of truth.
2. Never invent hotel names, phone numbers, fares, coordinates, prices, or hours.
   Use EXAMPLE placeholders or seed data only.
3. The frontend talks ONLY to FastAPI. Never import or use the Firestore client
   SDK in frontend code. Firebase Auth SDK is the only Firebase import allowed.
4. Follow the layer rule: Routers → Services → Repositories → Models.
   No layer imports from a layer above it. No skipping layers.
5. Every Firestore call goes through a Repository class. Never use
   google.cloud.firestore directly in Services or Routers.
6. All human-readable text fields use bilingual maps: { "bn": "...", "en": "..." }.
7. Every reference record must have data_source, is_verified, and last_updated.
8. Never log chat text, request bodies, GPS coordinates, or PII. See D14.
9. Never send user name, email, or phone number to Gemini. See D6 and D14.
10. Use APP_ENV to switch between emulator (dev/test) and production Firestore.
    In prod, fail loudly if keys are missing — never serve mock data. See D19.
11. Keep all API responses bilingual: error messages include message_en and message_bn.
12. Free tier only. No paid APIs, no paid services, no payment card required.
13. Run tests against the Firebase Emulator, never against production Firestore.
14. One feature per branch. Commit messages: "feat:", "fix:", "docs:", "test:".
15. When in doubt, check decisions.md. If it does not cover the question, ask.
```

---

## Resolutions to Previous Questions

1. **API path prefix:** Standardized on `/api/v1/` everywhere per D25.
2. **Schema documentation:** Standardized on `firestore-schema.md` everywhere; updated README and documentation references.
3. **Coding agent rules file location:** Tool-agnostic rules documented in §4.
4. **Module layout: by-module vs by-layer:** Resolved by D21: layout is by layer (`app/api/v1`, `app/services`, `app/repositories`, `app/models`, `app/agents`, `app/core`, `app/data`). Modules are logical file name groupings.
5. **Collection name:** Standardized on `transport_routes` everywhere per D22.

---

*End of repo-structure. ~150 lines.*
