# PothSathi — Build Plan & Calendar

> Binding decisions: [decisions.md](decisions.md).  
> Architecture: [architecture.md](architecture.md).  
> API specification: [api-spec.md](api-spec.md).  
> Firestore schema: [firestore-schema.md](firestore-schema.md).

---

## 1 Principles & Build Methodology

- **Approach:** Vertical slices, walking skeleton first, end-to-end tests with every slice.
- **Workflow:** One Git branch per slice, documents written before code, one coding-agent session per slice.
- **Agent Roles (D20):** Claude Opus (thinking) for documents, orchestrator, auth, security, rate limiting, and RAG. Gemini Flash for scaffolding, UI components, seed loading, simple CRUD, and unit tests.
- **Scope Discipline:** Strict MVP focus. Must-have slices (P0) take priority. Stretch slices (P1, P2) are implemented only if ahead of schedule.

---

## 2 Target Calendar & Day Plan

**Today is 23 November 2026. Final university submission deadline is 9 December 2026.**

| Date | Phase / Slices | Model (D20) | Target by Evening | Priority |
| --- | --- | --- | --- | --- |
| **23–24 Nov** | Documentation & Data Prep | Opus | Docs finished (`api-spec`, `build-plan`, `risks`, `eval`); seed data verified; Firebase project & Gemini key ready | P0 (Must) |
| **25 Nov** | Phase 0: Monorepo & Infra | Flash | Next.js + FastAPI scaffold, Firebase Emulator Suite running, seed loader scripts active | P0 (Must) |
| **26 Nov** | Phase 1: Auth, Layout, i18n | Opus / Flash | Anonymous + Google login, bilingual UI shell, Tier 0 static fallback build script | P0 (Must) |
| **27 Nov** | Slice 2: Hotel Explorer | Flash / Opus | Hotel filtering by area and budget, recommender scoring function verified | P0 (Must) |
| **28 Nov** | Slice 3: Nearby & Transport | Flash | OpenStreetMap nearby markers, fare calculator responding with seed routes | P0 (Must) |
| **29 Nov** | Slice 4: Safety & SOS | Opus / Flash | **Milestone M1**: Beach flag status, emergency directory, SOS logging working end to end | P0 (Must) |
| **30 Nov** | Slice 5: LLMClient & Rate Limiter | Opus | `LLMClient` wrapper calling Gemini, in-memory rate limiting (50/day user, 100/hr IP, global rest cap) | P0 (Must) |
| **1 Dec** | Slice 6: Safety Rules & Tools | Opus | Safety rule engine catches emergencies without LLM; function-calling tools wired | P0 (Must) |
| **2 Dec** | Slice 7: RAG & Grounded Chat | Opus | **Milestone M2**: In-memory vector RAG, grounded citations, fallback chain ("AI is resting") | P0 (Must) |
| **3 Dec** | Slice 8: Stretch P1 Features / P2 | Flash / Opus | Hotel reviews with sentiment, minimal admin CRUD, report wrong info button; P2 (Fare Fairness Checker) only if all P0/P1 done (D28) | P1 (Stretch) / P2 |
| **4 Dec** | Slice 9: Hardening & Deploy | Opus / Flash | **Milestone M3 (FEATURE FREEZE)**: Deployed to Vercel and Render, keep-warm ping, CI pass | P0 (Must) |
| **5–6 Dec** | Testing & Evaluation | Opus / Flash | 50-prompt evaluation run, SUS usability testing (10–15 users), bug fixes. **CODE FREEZE (6 Dec evening)** | P0 (Must) |
| **7–8 Dec** | Presentation & Artifacts | Opus | Final report, slide deck, demo recording, and backup screencast | P0 (Must) |
| **9 Dec** | Final Submission | — | University submission package delivered | P0 (Must) |

> [!WARNING]
> **P1 & P2 Reality Check:** Voice input/output (Web Speech API) and the P2 Fare Fairness Checker will almost certainly be cut to preserve buffer for evaluation and reporting.

---

## 3 Slices: Phase 0 & Phase 1 (M1 Foundation)

### Slice 0: Monorepo Scaffold, Infrastructure & Seed Loader (25 Nov)
- **Goal:** Set up reproducible repository workspace, FastAPI backend, Next.js frontend, Docker config, Firebase Emulator, and verified seed data loader.
- **Priority:** P0 (Must) | **Model:** Gemini Flash | **Estimate:** 7 hours (ASSUMPTION)
- **Depends on:** Git repository initialization, verified JSON seed files in `seed/`.
- **Backend tasks:** FastAPI project structure, Pydantic settings loading `APP_ENV`, Firestore emulator connector, `seed_loader.py` script populating local emulator collections.
- **Frontend tasks:** Next.js App Router scaffold, Tailwind CSS, shadcn/ui components (`Button`, `Card`, `Dialog`), base layout.
- **Tests & Concrete Acceptance:**
  - `test_seed_loader.py`: Loading `seed/hotels.json` inserts exactly N docs into emulator `hotels` collection.
  - Acceptance example: `python scripts/seed_loader.py` runs without error and prints `Loaded EXAMPLE_20 hotels, EXAMPLE_35 places, EXAMPLE_12 routes`.
- **Manual checks:** Open Firestore Emulator UI (`http://localhost:4000`), verify collections `hotels`, `places`, `transport_routes`, `kb_chunks`.
- **Done criteria:** `npm run dev` and `uvicorn app.main:app` launch cleanly without errors.

---

### Slice 1: Auth, User Profile, App Layout, i18n & Tier 0 Skeleton (26 Nov)
- **Goal:** Provide seamless tourist identity (anonymous guest or Google/email), bilingual layout toggle, and offline Tier 0 static JSON fallback.
- **Priority:** P0 (Must) | **Model:** Claude Opus (Auth/Security) + Gemini Flash (UI/i18n) | **Estimate:** 8 hours (ASSUMPTION)
- **Depends on:** Slice 0.
- **Backend tasks:** `auth_service.py` verifying Firebase ID tokens, `POST /api/v1/auth/register`, `GET /api/v1/me`, `PATCH /api/v1/me`.
- **Frontend tasks:** Firebase Auth client SDK integration, `AuthProvider`, `next-intl` configuration (`/bn` and `/en` routing), `LangToggle`, `toBengaliDigits()` helper, `build_tier0.py` generating committed fallback files.
- **Tests & Concrete Acceptance:**
  - `test_auth.py`: Submitting an expired token returns HTTP 401 with `{ "error": { "code": "INVALID_TOKEN" } }`.
  - Acceptance example: Request with `Authorization: Bearer EXAMPLE_VALID_ANON_TOKEN` to `GET /api/v1/me` returns `200 OK` and `{ "uid": "EXAMPLE_UID_123", "role": "tourist", "auth_provider": "anonymous" }`.
- **Manual checks:** Toggle language button; ensure header nav switches between Bengali and English instantly. Sign in anonymously and check Firestore `users/{uid}` created.
- **Done criteria:** User can browse public pages as guest, switch languages, and view persistent session.

---

### Slice 2: Hotel Explorer & Recommender (27 Nov)
- **Goal:** Filter and browse verified hotels with match scoring based on area, budget, and amenities.
- **Priority:** P0 (Must) | **Model:** Gemini Flash (UI/CRUD) + Claude Opus (Recommender algorithm) | **Estimate:** 7 hours (ASSUMPTION)
- **Depends on:** Slice 1.
- **Backend tasks:** `hotel_service.py`, `GET /api/v1/hotels` with in-memory TTL caching, recommender scoring formula implementation (§8 of `ai-spec.md`).
- **Frontend tasks:** Hotel list view, filter drawer (area select, budget slider, amenities checkboxes), hotel card with "Verified" badge or "Sample / Indicative" badge.
- **Tests & Concrete Acceptance:**
  - `test_hotel_recommender.py`: Verifies formula `(budget × 0.3) + (area × 0.25) + (amenities × 0.25) + (rating × 0.2)`.
  - Acceptance example: Query `GET /api/v1/hotels?area=kolatoli&max_price_bdt=3000&amenities=pool` returns matching hotels sorted by descending `match_score`, where `EXAMPLE_hotel_001` (price 2500, kolatoli, pool) scores `> 0.85`.
- **Manual checks:** Filter for Kolatoli with budget 2000 BDT; verify list updates without page reload and Bengali digits render in price tags.
- **Done criteria:** Hotel list and detail modal render verified data accurately from backend.

---

### Slice 3: Nearby Essentials Map & Transport Fare Calculator (28 Nov)
- **Goal:** Display essential places on OpenStreetMap and allow tourists to estimate local transit fares.
- **Priority:** P0 (Must) | **Model:** Gemini Flash | **Estimate:** 8 hours (ASSUMPTION)
- **Depends on:** Slice 1.
- **Backend tasks:** `nearby_service.py` with haversine distance filtering (`GET /api/v1/nearby`), `transport_service.py` (`GET /api/v1/transport/fares`, `GET /api/v1/transport/calculate`).
- **Frontend tasks:** `react-leaflet` map component with OpenStreetMap tiles and mandatory attribution, custom pins for hospitals/pharmacies/police, transport fare calculator widget (origin, destination, transit mode selector).
- **Tests & Concrete Acceptance:**
  - `test_nearby.py`: Passing lat=21.4167, lng=91.9833, radius_km=1.0 returns only items within 1 km, sorted by distance.
  - Acceptance example: `GET /api/v1/transport/calculate?origin=kolatoli&destination=laboni&mode=tomtom&passengers=2` returns `200 OK` with `min_fare_bdt: 40`, `max_fare_bdt: 60`.
- **Manual checks:** Pan map across Cox's Bazar coastline; verify pin popups show verified phone and address. Select route in fare calculator and verify calculated total.
- **Done criteria:** Nearby map and fare calculator render accurately with zero external paid map keys.

---

### Slice 4: Beach Safety Status, SOS & Emergency Screen (29 Nov — MILESTONE M1)
- **Goal:** Live beach flag warning display, emergency numbers screen, and SOS event logger across 3 zones (kolatoli, sugandha, laboni; D23).
- **Priority:** P0 (Must) | **Model:** Claude Opus (Safety rules) + Gemini Flash (UI) | **Estimate:** 7 hours (ASSUMPTION)
- **Depends on:** Slice 1.
- **Backend tasks:** `safety_service.py` (`GET /api/v1/safety/beach-status`, `GET /api/v1/safety/advisories`; multi-zone `beach_status/{zone_id}` for `kolatoli`, `sugandha`, `laboni` per D23), `emergency_service.py` (`GET /api/v1/emergency/contacts`, `POST /api/v1/emergency/sos`).
- **Frontend tasks:** Beach flag banner on homepage (green/yellow/red with `last_updated` and outdated badge if >6h old per D24), dedicated `/emergency` screen with one-tap `tel:999` and `wa.me` links, SOS modal.
- **Tests & Concrete Acceptance:**
  - `test_beach_status.py`: Returns flag color and advisory text per zone. If `last_updated` is older than 6h, `is_outdated` flag is `true` (D24).
  - Acceptance example: `POST /api/v1/emergency/sos` with `{ "trigger_type": "button", "lat": 21.4167, "lng": 91.9833 }` returns HTTP 201 with `sos_id: "EXAMPLE_sos_101"` and creates record in emulator `sos_events`.
- **Manual checks:** Tap SOS button in emergency screen; confirm immediate dialer prompt (`tel:999`) and confirmation message.
- **Done criteria:** **MILESTONE M1 ACHIEVED:** Auth + Hotels + Nearby Map + Fares + Beach Safety working end to end.


---

## 4 Slices: Phase 2 (AI Intelligence & M2)

### Slice 5: LLMClient Wrapper, Basic Chat, Rate Limiting & Daily Counter (30 Nov)
- **Goal:** Robust wrapper around Gemini API with strict in-memory user limits and daily budget protection.
- **Priority:** P0 (Must) | **Model:** Claude Opus | **Estimate:** 8 hours (ASSUMPTION)
- **Depends on:** Slice 1, Slice 4.
- **Backend tasks:** `POST /api/v1/chat/messages`, `llm_client.py` wrapping Gemini SDK, PII regex stripping, input length validation (≤2000 chars), `rate_limiter.py` tracking per-user (50/day in Asia/Dhaka time), per-IP (100/hr), and global daily AI requests (D25, D26).
- **Frontend tasks:** Chat floating drawer and full `/chat` screen, optimistic message rendering, typing indicator, daily limit counter badge.
- **Tests & Concrete Acceptance:**
  - `test_rate_limiter.py`: Calling chat 51 times for one user UID raises HTTP 429 `RATE_LIMITED`.
  - Acceptance example: Input exceeding 2,000 characters returns HTTP 400 with `{ "error": { "code": "INPUT_TOO_LONG" } }`.
- **Manual checks:** Send test messages in chat; verify rate-limit headers decrement; trigger limit and verify user-facing localized message.
- **Done criteria:** Clean bilingual conversation exchange with backend verifying token limits.

---

### Slice 6: Safety Rule Engine, Tool Declarations & Orchestrator (1 Dec)
- **Goal:** Intercept emergencies pre-LLM and equip Gemini with verified local search tools.
- **Priority:** P0 (Must) | **Model:** Claude Opus | **Estimate:** 9 hours (ASSUMPTION)
- **Depends on:** Slice 2, Slice 3, Slice 4, Slice 5.
- **Backend tasks:** `safety_rules.py` keyword matcher (Bengali, English, Banglish: e.g. "drowning", "ডুবে যাচ্ছে", "dube jacche"), Gemini function calling declarations (`search_hotels`, `find_nearby`, `calculate_fare`, `get_beach_status`), tool execution dispatcher.
- **Frontend tasks:** Dynamic structured card renderers in chat window (`HotelCard`, `PlaceCard`, `FareCard`, `BeachStatusBanner`).
- **Tests & Concrete Acceptance:**
  - `test_safety_engine.py`: Emergency prompt returns immediate pre-written 999 card with zero LLM API calls.
  - Acceptance example: "I am drowning near Kolatoli" (or "ami dube jacchi") returns `safety_triggered: true` with emergency contacts and guidance.
  - Acceptance example: "hotels in Kolatoli under 3000 with wifi" triggers Gemini tool call `search_hotels(area="kolatoli", max_price_bdt=3000, amenities=["wifi"])` and returns verified hotel cards.
- **Manual checks:** Type both Bengali and Banglish emergency queries; verify immediate response. Ask for hotel recommendations and verify card rendering.
- **Done criteria:** Safety rules trigger reliably, and Gemini successfully invokes backend tools.

---

### Slice 7: In-Memory RAG Index, Sourced Answers & Fallback Chain (2 Dec — MILESTONE M2)
- **Goal:** Ground answers with verified citations; execute fallback chain when Gemini or quota fails.
- **Priority:** P0 (Must) | **Model:** Claude Opus | **Estimate:** 9 hours (ASSUMPTION)
- **Depends on:** Slice 6.
- **Backend tasks:** Pre-compute chunk embeddings at startup into in-memory vector index, cosine similarity search, source citation formatter (`sources` array), fallback orchestrator (Keyword intent router → RAG chunk search → "AI is resting" message).
- **Frontend tasks:** Source pills below chat messages linking to verified records, "AI is resting" banner with quick buttons to Tier 0 static pages.
- **Tests & Concrete Acceptance:**
  - `test_rag_pipeline.py`: Knowledge query retrieves top-3 matching chunks from `kb_chunks`.
  - Acceptance example: Mocking Gemini 429 quota exhaustion routes query to keyword RAG fallback; if empty, returns `is_ai_resting: true` and polite Bengali rest message.
- **Manual checks:** Ask specific Cox's Bazar factual question (e.g. beach flag colors); verify response displays source badge. Disconnect Gemini API key; confirm graceful fallback.
- **Done criteria:** **MILESTONE M2 ACHIEVED:** Full AI chat pipeline functioning with verified sources, tool invocation, and graceful degradation.

---

## 5 Slices: Phase 3 (Stretch Features, Hardening & Milestones M3)

### Slice 8: Stretch P1 Features (3 Dec)
- **Goal:** Implement lightweight hotel reviews with sentiment, minimal admin data editor, and report-wrong-info button. P2 work (Fare Fairness Checker) may only happen on 3 Dec after all P0 and P1 are done, never after the 4 Dec feature freeze (D28).
- **Priority:** P1 (Stretch — high probability of partial cut) | **Model:** Gemini Flash (Admin/Reports) + Claude Opus (Sentiment) | **Estimate:** 8 hours (ASSUMPTION)
- **Depends on:** Slice 2, Slice 4, Slice 7.
- **Backend tasks:** `review_service.py` with lexicon-based sentiment analysis (§9 of `ai-spec.md`), `PUT /api/v1/admin/beach-status/{zone_id}`, `POST /api/v1/admin/cache/refresh`, `POST /api/v1/reports`.
- **Frontend tasks:** Review submission modal with star rating, admin dashboard view (`/admin`) for beach flag updating and cache clearing, "Report wrong info" button on hotel cards.
- **Tests & Concrete Acceptance:**
  - `test_sentiment.py`: "Room was clean and great" yields `overall: "positive"`; "ঘর নোংরা এবং গন্ধ" yields `overall: "negative"`.
  - Acceptance example: Admin PUT to `/api/v1/admin/beach-status/kolatoli` with `{ "flag": "red" }` updates flag and triggers in-memory cache refresh.
- **Manual checks:** Post a test review; verify sentiment aspect breakdown. Log in as admin and change beach flag; verify public site reflects change instantly.
- **Done criteria:** Working review submission, admin flag control, and feedback reporting.

---

### Slice 9: Hardening, Cloud Deployment, CI & Verification (4 Dec — MILESTONE M3 / FEATURE FREEZE)
- **Goal:** Production deployment to Vercel (frontend) and Render (backend) with keep-warm ping, strict environment validation, and passing CI.
- **Priority:** P0 (Must) | **Model:** Claude Opus & Gemini Flash | **Estimate:** 8 hours (ASSUMPTION)
- **Depends on:** Slice 0 through Slice 7.
- **Backend tasks:** Production Dockerfile, Render deployment, UptimeRobot keep-warm ping configuration (`GET /api/v1/health` every 14 min), missing key loud failure verification (`APP_ENV=prod`).
- **Frontend tasks:** Vercel deployment, production environment variables configuration, global error boundary, offline static page hydration.
- **Tests & Concrete Acceptance:**
  - `test_prod_config.py`: Missing `GEMINI_API_KEY` in `prod` environment throws startup error and refuses to start.
  - Acceptance example: `curl -I https://api-pothsathi.onrender.com/api/v1/health` returns `200 OK` with JSON `{ "status": "ok", "environment": "prod" }`.
- **Manual checks:** Access live public URL on mobile phone; run full user journey (browse hotels, check nearby map, calculate fare, send chat message, test SOS link).
- **Done criteria:** **MILESTONE M3 ACHIEVED & FEATURE FREEZE:** Site live, demo-safe, and stable in production.

---

## 6 Post-Freeze Execution (5–9 December)

### 5–6 December: Evaluation, Usability Testing & Code Freeze
- **Tasks:**
  1. Execute automated evaluation suite: 50 test prompts (25 Bengali, 25 English) comparing plain Gemini vs. PothSathi pipeline (hallucination rate, source adherence).
  2. Measure emergency rule accuracy across 30 stress prompts (Bengali, English, Banglish).
  3. Conduct System Usability Scale (SUS) test with 10–15 target users.
  4. Fix critical high-severity bugs only.
- **CODE FREEZE:** Evening of 6 December 2026. Zero code changes permitted thereafter.

### 7–8 December: Final Report, Slides, Demo Video & Backup
- **Tasks:**
  1. Draft academic report with architecture diagrams, data flow diagrams, and evaluation tables.
  2. Prepare 10-slide presentation deck.
  3. Record 3-minute video demonstration highlighting key features (bilingual chat, safety rules, nearby map, hotel recommendations).
  4. Record local backup screencast in case live internet fails during presentation.

### 9 December: Final Submission
- Deliver repository link, report PDF, slide deck, and video demo before the university deadline.

---

## 7 Summary Timeline & Milestones

### Summary Timeline Table
| Dates | Focus Area | Deliverables | Milestone |
| --- | --- | --- | --- |
| 23–24 Nov | Documentation & Preparation | Complete specs, seed data, API keys | Pre-build |
| 25–26 Nov | Infrastructure & Shell | Monorepo, Emulator, Auth, Layout, i18n | Phase 0–1 |
| 27–29 Nov | Core Travel Features | Hotels, Nearby Map, Fares, Safety, SOS | **Milestone M1 (29 Nov)** |
| 30 Nov – 2 Dec | AI Intelligence Pipeline | LLMClient, Rules, Tools, RAG, Fallback | **Milestone M2 (2 Dec)** |
| 3 Dec | Stretch Features | Reviews, Admin flag editor, Reports | P1 Buffer |
| 4 Dec | Production Deployment | Vercel, Render, CI, Keep-warm | **Milestone M3 (4 Dec — Feature Freeze)** |
| 5–6 Dec | Verification & Testing | 50 Evals, SUS testing, Bug fixes | **Code Freeze (6 Dec evening)** |
| 7–8 Dec | Documentation & Media | Academic report, slides, demo video | Final Pack |
| 9 Dec | Submission | Final university project delivery | Submission |

### Master Build Order
`Slice order: Slice 0 (Scaffold & Emulator) -> Slice 1 (Auth & Layout) -> Slice 2 (Hotels) -> Slice 3 (Nearby & Fares) -> Slice 4 (Safety & SOS) -> Slice 5 (LLMClient & Limits) -> Slice 6 (Rules & Tools) -> Slice 7 (RAG & Sourced Chat) -> Slice 8 (Stretch P1) -> Slice 9 (Hardening & Deploy)`

### Milestones Defined
- **M1 (29 Nov):** Login, fares, hotels, nearby map, and beach safety working end to end in emulator.
- **M2 (2 Dec):** First real AI answer grounded in verified seed data with sources and automatic fallback.
- **M3 (4 Dec):** Fully deployed on Render and Vercel, demo-safe, keep-warm verified, and feature frozen.

### Scope Cut Order (Binding Rule from D17)
If development falls behind schedule, cut features in this exact order:
1. **P2 Feature:** Fare Fairness Checker.
2. **Voice:** Web Speech API voice input and synthesis.
3. **Admin Page:** Minimal admin UI (use direct seed files / manual Firestore updates instead).
4. **Reviews:** Hotel reviews and sentiment analysis.
5. **AI Tools:** Secondary tools, leaving only `search_hotels`, `find_nearby`, and `calculate_fare`.
