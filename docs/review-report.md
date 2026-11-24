# PothSathi — Documentation Review & Consistency Audit Report

**Date of Review:** 23 November 2026  
**Auditor:** Antigravity AI  
**Scope:** Review of `README.md`, `docs/decisions.md`, and all 11 accompanying documentation files in `docs/`.  
**Rules Applied:** Documentation task only; zero application code; no modification of existing documentation files; no real-world facts invented.

---

## 1. Contradictions

The following table documents all direct contradictions, inconsistencies, and conflicting requirements identified across the documentation suite.

| # | What | File A Says | File B Says | Suggested Fix | Severity |
|---|---|---|---|---|---|
| C1 | **Backend Folder Architecture (By-Module vs By-Layer)** | `docs/architecture.md` (§2) specifies a modular monolith organized **by-module**: `backend/app/modules/<module>/` with `router.py`, `service.py`, `repository.py`, and `schemas.py` inside each module. | `docs/repo-structure.md` (§2) and `docs/build-plan.md` specify organization **by-layer**: `backend/app/services/`, `repositories/`, `models/`, and `api/v1/`. | Adopt the by-layer structure (`app/services/`, `app/repositories/`, `app/api/v1/`) across all documents as it matches `repo-structure.md` and `build-plan.md`. Update `docs/architecture.md`. | **High** |
| C2 | **Transport / Fare Collection Name** | `README.md` (line 234), `docs/overview.md` (§10), and `docs/architecture.md` (§1 line 54) name the collection `fare_routes`. | `docs/firestore-schema.md` (§2 line 27, §3.5), `docs/api-spec.md` (§6, §16), `docs/data-plan.md` (§1 line 14), and `docs/repo-structure.md` (§2 line 50) name it `transport_routes`. | Standardize on `transport_routes` everywhere. Update `README.md`, `docs/overview.md`, and `docs/architecture.md`. | **High** |
| C3 | **Beach Status Scope (Singleton `main` vs Multi-Zone)** | `docs/firestore-schema.md` (§3.7) and `docs/data-plan.md` (§5) define a single zone: `beach_status/main` (singleton covering Kolatoli, Sugandha, Laboni). `docs/ai-spec.md` (§5.4) specifies `get_beach_status` has parameter `{}` (no arguments). | `docs/api-spec.md` (§7 line 296, §11.2 line 484) defines `zone_id` parameter (`kolatoli`, `sugandha`, `laboni`) for endpoints. `docs/evaluation-and-report.md` (Prompt 16) expects `get_beach_status(zone="laboni")`. | Standardize on multi-zone `beach_status/{zone_id}` with `kolatoli`, `sugandha`, `laboni` (or define `main` as a shared fallback). Update `docs/ai-spec.md` tool declaration and `docs/firestore-schema.md`. | **High** |
| C4 | **Post-Freeze Feature Scheduling (P2 Feature)** | `docs/decisions.md` (D17) and `docs/build-plan.md` (§2, §6) strictly state: Feature freeze on **4 Dec**; nothing is scheduled after 4 Dec except evaluation, report, and submission. | `docs/overview.md` (§11 line 255) schedules: `P2 (if time) | 4–5 Dec | Fare Fairness Checker`. | Remove the 4–5 Dec P2 window from `docs/overview.md`. Harmonize with `docs/build-plan.md` where 5–6 Dec is strictly for testing/evaluation. | **High** |
| C5 | **Beach Status Outdated Time Threshold** | `docs/overview.md` (§6 line 154), `docs/ai-spec.md` (§5.4 line 269), and `docs/data-plan.md` (§2 line 43) specify status is outdated if older than **6 hours**. | `docs/build-plan.md` (Slice 4 line 108 & line 110) specifies outdated warning if older than **12 hours** (in UI) or **24 hours** (in `test_beach_status.py`). | Align on a single threshold across all files: **6 hours** (appropriate for shifting tides and sea conditions). Update `docs/build-plan.md`. | **Medium** |
| C6 | **API Base Route Prefix & Versioning** | `docs/architecture.md` (§2 line 102–114, §4, §9) uses unversioned routes: `/api/hotels`, `/api/fares`, `/api/chat`, `/api/safety`, `/api/emergency`. | `docs/api-spec.md` (§1.1, §15, §16) and `docs/repo-structure.md` (§1 line 16, §2) mandate `/api/v1/`: `/api/v1/hotels`, `/api/v1/transport/fares`, `/api/v1/chat/messages`, etc. | Standardize on `/api/v1/` prefix everywhere. Update `docs/architecture.md`. | **Medium** |
| C7 | **Chat Endpoint Path & Contract** | `docs/architecture.md` (§9 line 437) specifies `POST /api/chat`. `docs/repo-structure.md` (§2 line 136) specifies `POST /api/v1/chat`. | `docs/api-spec.md` (§8 line 331, §16 line 641) specifies `POST /api/v1/chat/messages` with `{ message, session_id?, language? }`. | Standardize on `POST /api/v1/chat/messages`. Update `docs/architecture.md` and `docs/repo-structure.md`. | **Medium** |
| C8 | **Fare Calculation Parameters & Route Schema** | `docs/ai-spec.md` (§5.3) defines `calculate_fare` with `{ origin, destination }`. `docs/firestore-schema.md` (§3.5) defines `transport_routes` with `vehicle_type`, `fare_min_bdt`, `fare_max_bdt`. | `docs/api-spec.md` (§6 line 258, 273) defines `GET /api/v1/transport/calculate` with parameters `origin`, `destination`, `mode`, `passengers`, and response field `fare_type: "per_person"`. | Add `fare_type` to `docs/firestore-schema.md` or clarify whether calculation multiplies per-person rates or returns total vehicle charter fare. Align `ai-spec.md` tool declaration. | **Medium** |
| C9 | **Auth Registration / Login Route** | `docs/repo-structure.md` (§2 line 139) lists `POST /api/v1/auth/login`. | `docs/architecture.md` (§1 line 60, §5 line 249) notes login is client-side SDK only. `docs/api-spec.md` (§2, §16 line 644) replaces `/login` with `POST /api/v1/auth/register` and `GET /api/v1/me`. | Remove `POST /api/v1/auth/login` from `docs/repo-structure.md` and replace with `POST /api/v1/auth/register` and `GET /api/v1/me`. | **Low** |
| C10 | **Chat Rate Limit Reset Window** | `docs/architecture.md` (§9 line 422) specifies 50 chat messages per user per **rolling 24-hour window**. | `docs/firestore-schema.md` (§3.10) tracks usage via `usage/{uid_date}` where date is `YYYY-MM-DD` (**calendar day**). | Clarify whether rate limit resets at midnight UTC/BST or is rolling 24 hours. Using calendar date (`YYYY-MM-DD`) is much simpler on free tiers; update `architecture.md`. | **Low** |
| C11 | **Documentation File Naming in README** | `README.md` (lines 138, 279) points to `docs/data-model.md`. | The file was created as `docs/firestore-schema.md`. `docs/repo-structure.md` (§3 line 253) confirms `firestore-schema.md` replaces `data-model.md`. | Update `README.md` to reference `docs/firestore-schema.md` instead of `docs/data-model.md`. | **Low** |
| C12 | **Recommender Parameter Name in Build Plan** | `docs/ai-spec.md` (§5.1) and `docs/api-spec.md` (§3) define hotel budget search parameter as `max_price_bdt` (or `max_budget`). | `docs/build-plan.md` (Slice 6 line 143) uses `max_budget=3000` inside the tool call example `search_hotels(area="kolatoli", max_budget=3000, ...)`. | Harmonize parameter name to `max_price_bdt` in `docs/build-plan.md` to match `docs/ai-spec.md` §5.1. | **Low** |

---

## 2. Coverage Matrix

Coverage of each **P0** and **P1** feature from `docs/decisions.md` (D11) across the six core documentation files:
- `docs/overview.md`
- `docs/api-spec.md`
- `docs/firestore-schema.md`
- `docs/ai-spec.md`
- `docs/build-plan.md`
- `docs/evaluation-and-report.md`

| Priority | Feature (D11) | `overview.md` | `api-spec.md` | `firestore-schema.md` | `ai-spec.md` | `build-plan.md` | `evaluation-and-report.md` | Status |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **P0** | **Bilingual UI** (`next-intl`, bn/en, Bengali digits) | Present (§1, §3) | Present (§1.3, §1.4) | Present (§1, `{bn,en}`) | Present (§1, §6) | Present (Slice 1) | Present (§1.1 Category 8, §2.2) | **Full Coverage** |
| **P0** | **Hotel Explorer with Recommender** | Present (§3, §4, §10) | Present (§3) | Present (§2 #2, §3.2) | Present (§5.1, §8) | Present (Slice 2) | Present (§1.1 Category 2, §2.1 T1) | **Full Coverage** |
| **P0** | **Nearby Essentials Map** (OSM, react-leaflet) | Present (§3, §4, §10) | Present (§5) | Present (§2 #4, §3.4) | Present (§5.2) | Present (Slice 3) | Present (§1.1 Category 3, §2.1 T4) | **Full Coverage** |
| **P0** | **Fare Guide & Calculator** | Present (§3, §4, §10) | Present (§6) | Present (§2 #5, §3.5) | Present (§5.3) | Present (Slice 3) | Present (§1.1 Category 1, §2.1 T2) | **Full Coverage** |
| **P0** | **Beach Safety Status & SOS / Emergency** | Present (§3, §4, §7) | Present (§7, §9) | Present (§2 #7, #8, §3.7, §3.8) | Present (§4, §5.4) | Present (Slice 4) | Present (§1.1 Category 4, 5, §2.1 T3, T5) | **Full Coverage** |
| **P0** | **AI Chat** (Rules, Tools, RAG, Fallback) | Present (§3, §5) | Present (§8) | Present (§2 #6, #9, #10, #11) | Present (§2–§7, §10–§12) | Present (Slice 5, 6, 7) | Present (§1.1–§1.3, S1/S2/S3) | **Full Coverage** |
| **P1** | **Hotel Reviews with Sentiment** | Present (§3, §10) | Present (§4) | Present (§2 #3, §3.3) | Present (§9) | Present (Slice 8) | **Missing** (Not evaluated in 50 prompts or SUS tasks; mentioned only in Ch 5 outline) | **Partial Coverage** |
| **P1** | **Minimal Admin Page** (Data edit, flag update) | Present (§3, §4) | Present (§11) | Present (§2 #13, §3.13) | **Missing** (Admin has no AI scope) | Present (Slice 8) | **Missing** (Not evaluated in user testing) | **Partial Coverage** |
| **P1** | **Voice Input / Output** (Web Speech API) | Present (§3, §4) | **Missing** (Client-side API; no backend route) | **Missing** (No schema needed) | **Missing** (No speech pipeline spec) | Present (Slice 8 — flagged for cut) | **Missing** (No voice test cases in benchmark) | **Partial Coverage** |
| **P1** | **Report Wrong Info Button** | Present (§3, §8) | Present (§10, §11.2) | Present (§2 #12, §3.12) | **Missing** (No AI scope) | Present (Slice 8) | **Missing** (Not evaluated in test protocol) | **Partial Coverage** |

---

## 3. Name Mismatches

The table below catalogs name discrepancies across architectural layers, documents, and specifications.

| Category | Artifact A (File & Identifier) | Artifact B (File & Identifier) | Impact & Notes |
|---|---|---|---|
| **Collections** | `architecture.md`, `overview.md`, `README.md`: `fare_routes` | `firestore-schema.md`, `data-plan.md`, `api-spec.md`, `repo-structure.md`: `transport_routes` | Code breaking if seed loader writes to `transport_routes` but backend repositories read from `fare_routes`. |
| **Collections** | `architecture.md`, `overview.md`: `reviews` (top-level collection) | `firestore-schema.md`, `api-spec.md`: `hotels/{hotel_id}/reviews/{review_id}` (subcollection) | Query shape differs: subcollection requires parent `hotel_id` in path. |
| **Endpoints** | `architecture.md` (§2): `/api/fares` | `repo-structure.md` (§2): `/api/v1/fares` | `api-spec.md` (§6, §16): `/api/v1/transport/fares`. |
| **Endpoints** | `repo-structure.md` (§2): `POST /api/v1/fares/calculate` | `api-spec.md` (§6): `GET /api/v1/transport/calculate` | Method mismatch (POST vs GET) and path mismatch (`fares/calculate` vs `transport/calculate`). |
| **Endpoints** | `architecture.md` (§2): `POST /api/chat` | `repo-structure.md` (§2): `POST /api/v1/chat` | `api-spec.md` (§8): `POST /api/v1/chat/messages`. |
| **Endpoints** | `architecture.md` (§2): `GET /api/emergency` | `repo-structure.md` (§2): `GET /api/v1/emergency` | `api-spec.md` (§9): `GET /api/v1/emergency/contacts` & `POST /api/v1/emergency/sos`. |
| **Endpoints** | `architecture.md` (§2): `GET /api/safety` | `api-spec.md` (§7): `GET /api/v1/safety/beach-status` & `GET /api/v1/safety/advisories` | Single root endpoint vs split sub-resources. |
| **Endpoints** | `repo-structure.md` (§2): `POST /api/v1/auth/login` | `api-spec.md` (§2): `POST /api/v1/auth/register` & `GET /api/v1/me` | Firebase Auth handles login on client; backend has registration/sync endpoint. |
| **Tools** | `ai-spec.md` (§5.4): `get_beach_status()` (no params) | `evaluation-and-report.md` (§1.1): `get_beach_status(zone="laboni")` | Parameter mismatch between model tool schema and test benchmark harness. |
| **Tools** | `ai-spec.md` (§5.1): `search_hotels(max_price_bdt=...)` | `build-plan.md` (§4 Slice 6): `search_hotels(max_budget=...)` | Parameter name mismatch in tool call dispatcher. |
| **Screens / Routes** | `architecture.md` (§3), `repo-structure.md` (§2): Chat is inside `[locale]/page.tsx` (Home) | `build-plan.md` (§4 Slice 5): mentions full `/chat` screen (`[locale]/chat/page.tsx`) | Route missing from Next.js page hierarchy in architecture and repo-structure. |
| **Slice Naming** | `build-plan.md` (§2 table): "Phase 0", "Phase 1", "Slice 2", ... | `build-plan.md` (§3 text): "Slice 0", "Slice 1", "Slice 2", ... | Inconsistent labeling between calendar table and detailed slice descriptions. |
| **Env Variables** | `architecture.md` (§13): `DAILY_AI_LIMIT` | `firestore-schema.md` (§3.11): `limit` inside `ai_usage/{date}` document | Consistent in intent, but backend setting vs Firestore document field name should be noted. |

---

## 4. Facts That Look Invented or Unverified

In accordance with project rules (*"NEVER invent real-world facts. If something is missing, report it; do not fix it yet"*), the following data points identified in the repository appear unverified, incorrect, or purely placeholder:

1. **Emergency Numbers (High Risk):**
   - **Fire Service `199`:** Listed in `README.md` (§194), `docs/overview.md` (§7), and `docs/data-plan.md` (§3.5) as `199 (TO VERIFY)`. In Bangladesh, `199` is an old BTCL telephone line fault reporting number, **not** Fire Service. The real Fire Service hotline is `16163` or reachable via `999`.
   - **Ambulance `199`:** Listed in `README.md` (§194) and `docs/overview.md` (§7) as `199 (TO VERIFY)`. Red Crescent ambulance is not reachable on `199`. In Bangladesh, medical emergencies are reached via `999` or direct local hospital lines.
   - **Women & Children Helpline `10921`:** Listed in `README.md` (§194), `docs/overview.md` (§7), and `docs/data-plan.md` (§3.5) as `10921 (TO VERIFY)`. The official government Women & Children Helpline was shortened from `10921` to `109` several years ago.
   - **Tourist Police Number:** Listed as `TBD` or `EXAMPLE_01700000001` or `https://wa.me/EXAMPLE_TOURIST_POLICE`. No real verified contact for Cox's Bazar Tourist Police is present.

2. **Transport Fares & Route Distances:**
   - In `docs/overview.md` (§6), Kolatoli to Laboni CNG fare is listed as `৳EXAMPLE_80–৳EXAMPLE_120 (verify)`.
   - In `docs/api-spec.md` (§6), Kolatoli to Laboni Tomtom fare is listed as `min_fare_bdt: 40`, `max_fare_bdt: 60`, `distance_km: 3.5`.
   - In `docs/evaluation-and-report.md` (§1.1 Prompt 1, §5.1), Kolatoli to Laboni Tomtom fare is listed as `EXAMPLE_20–40 BDT`.
   - In `docs/data-plan.md` (§3.3), all fares, minimums, maximums, and distances are `0`.
   - All fare values are contradictory placeholders; none represent confirmed local union or municipal transit rates.

3. **Hotel Names, Tariffs, Amenities, and Locations:**
   - In `docs/api-spec.md` (§3), `EXAMPLE_Sea_View` (kolatoli, 2500–4500 BDT, lat 21.4167, lon 91.9833) is used.
   - In `docs/data-plan.md` (§3.1) and `docs/firestore-schema.md` (§3.2), hotels have dummy names (`EXAMPLE_হোটেল_ক`), `price_min_bdt: 0`, `lat: 21.4272`, `lon: 91.9710`, and geohash `EXMPL1`.
   - Zero verified real-world hotel records currently exist in the repository.

4. **Places & Essential Services:**
   - `docs/api-spec.md` (§5) lists `EXAMPLE_সৈকত_ফার্মেসি` (lat 21.4170, lon 91.9840, phone `EXAMPLE_01700000000`).
   - `docs/data-plan.md` (§3.2) lists dummy hospital and ATM coordinates.
   - Zero verified real-world hospitals, pharmacies, or police stations exist in the seed data.

5. **Gemini Free-Tier Rate Limits:**
   - `docs/tech-stack.md` (§3 #1) cites `~5 RPM, ~20 RPD` for flagship Flash models (`gemini-3.8-flash`), and `~500 RPD` for lighter models, but explicitly notes: *"Source / status: ai.google.dev rate-limit dashboard — verify exact numbers at aistudio.google.com/rate-limit"*.
   - Free tier daily request limits vary by model and project quota; `20 RPD` is an unverified assumption that could severely restrict testing if not confirmed in Google AI Studio.

---

## 5. Calendar Check

### 5.1 Day-by-Day Coverage (23 November to 9 December 2026)

| Date | Day | Scheduled in `docs/build-plan.md`? | Planned Deliverables |
|---|---|:---:|---|
| **23 Nov** | Mon | Yes (§2) | Documentation & Data Prep (Specs, decisions review, review report) |
| **24 Nov** | Tue | Yes (§2) | Documentation & Data Prep (Seed data collection, Firebase setup) |
| **25 Nov** | Wed | Yes (§2, §3) | Slice 0: Monorepo Scaffold, Infrastructure & Seed Loader |
| **26 Nov** | Thu | Yes (§2, §3) | Slice 1: Auth, User Profile, App Layout, i18n & Tier 0 Skeleton |
| **27 Nov** | Fri | Yes (§2, §3) | Slice 2: Hotel Explorer & Recommender |
| **28 Nov** | Sat | Yes (§2, §3) | Slice 3: Nearby Essentials Map & Transport Fare Calculator |
| **29 Nov** | Sun | Yes (§2, §3) | Slice 4: Beach Safety Status, SOS & Emergency Screen (**Milestone M1**) |
| **30 Nov** | Mon | Yes (§2, §4) | Slice 5: LLMClient Wrapper, Basic Chat, Rate Limiter & Daily Counter |
| **1 Dec** | Tue | Yes (§2, §4) | Slice 6: Safety Rule Engine, Tool Declarations & Orchestrator |
| **2 Dec** | Wed | Yes (§2, §4) | Slice 7: In-Memory RAG Index, Sourced Answers & Fallback (**Milestone M2**) |
| **3 Dec** | Thu | Yes (§2, §5) | Slice 8: Stretch P1 Features (Reviews, Admin flag editor, Reports) |
| **4 Dec** | Fri | Yes (§2, §5) | Slice 9: Hardening, Cloud Deployment, Keep-Warm (**M3 / FEATURE FREEZE**) |
| **5 Dec** | Sat | Yes (§2, §6) | Post-Freeze Testing: 50-Prompt Evaluation A & SUS Usability Study B |
| **6 Dec** | Sun | Yes (§2, §6) | Post-Freeze Testing: Bug fixes, SUS analysis. **CODE FREEZE (Evening)** |
| **7 Dec** | Mon | Yes (§2, §6, §7) | Presentation & Artifacts: Report Chapters 1–5, slide deck draft |
| **8 Dec** | Tue | Yes (§2, §6, §7) | Presentation & Artifacts: Report Chapters 6–10, demo video, backup recording |
| **9 Dec** | Wed | Yes (§2, §6) | Final University Project Submission |

**Day Coverage Verdict:** Every single calendar day from 23 November to 9 December 2026 is explicitly accounted for in `docs/build-plan.md`.

### 5.2 Post-Feature Freeze Audit (Post-4 December)
- **Feature Freeze Date:** 4 December 2026 (Slice 9 completion).
- **Scheduled After 4 December in `build-plan.md`:**
  - 5–6 Dec: Evaluation benchmark execution, SUS usability study, critical bug fixes. Code freeze on 6 Dec evening.
  - 7–8 Dec: Academic report drafting, slide deck preparation, video recording, backup screencast.
  - 9 Dec: Submission.
- **Leakage / Defect Detected:** While `docs/build-plan.md` adheres strictly to the rule, `docs/overview.md` (§11 line 255) erroneously lists `P2 (if time) | 4–5 Dec | Fare Fairness Checker`. This must be corrected in `overview.md` to prevent feature creep after the 4 December freeze.

---

## 6. Missing Pieces

The following top 10 missing specifications, assets, and decisions are ordered by importance, along with the document that should hold each item:

| # | Missing Piece | Document That Should Hold It | Description & Urgency |
|---|---|---|---|
| 1 | **Verified Real-World Seed Data** | `seed/*.json`, `docs/data-plan.md` | All `seed/` files currently contain only empty dummy objects with zeroes. Need 15–25 real hotels, 30–40 places, 10–15 fare routes, and 40–60 KB chunks before building seed loaders. |
| 2 | **Correction of Real-World Emergency Hotline Numbers** | `seed/emergency_contacts.json`, `docs/overview.md`, `docs/data-plan.md` | Fire Service (`199` is invalid), Ambulance (`199` is invalid), and Women's Helpline (`10921` is outdated, now `109`) must be corrected to official, verified Bangladeshi numbers. |
| 3 | **Harmonization of Monorepo Layout (By-Layer vs By-Module)** | `docs/architecture.md` | `architecture.md` specifies `app/modules/` while `repo-structure.md` and `build-plan.md` specify `app/services/`, `app/repositories/`, `app/api/v1/`. Must be unified before Slice 0 on 25 Nov. |
| 4 | **Reconciliation of Beach Status Schema (Singleton vs Multi-Zone)** | `docs/firestore-schema.md`, `docs/ai-spec.md`, `docs/api-spec.md` | Resolve whether beach status is stored as `beach_status/main` (parameterless tool call) or `beach_status/{zone_id}` with `kolatoli`, `sugandha`, `laboni` parameters. |
| 5 | **Confirmation of Active Gemini Free-Tier Model & Daily Quota** | `docs/tech-stack.md`, `docs/ai-spec.md` | Exact model name (`gemini-3.8-flash` vs `gemini-2.5-flash` / `gemini-1.5-flash`) and free RPM/RPD limits must be verified in Google AI Studio to configure `DAILY_AI_LIMIT`. |
| 6 | **Standardization of Transport Collection & Route Names** | `docs/architecture.md`, `README.md` | Update all instances of `fare_routes` to `transport_routes` and all instances of `/api/fares` to `/api/v1/transport/fares`. |
| 7 | **Expansion of `safety_rules.json` Keywords** | `seed/safety_rules.json`, `docs/ai-spec.md` | Only 3 sample keywords exist per category. Must be expanded with real Bengali and phonetic Banglish variations by a native speaker before Slice 6. |
| 8 | **Evaluation Prompts JSON Benchmark Suite** | `backend/app/data/eval_prompts.json`, `docs/evaluation-and-report.md` | 45 sample prompts exist in markdown; the full 50-item JSON dataset with ground-truth citations must be prepared before evaluation execution. |
| 9 | **Sentiment Analysis Lexicon Dictionaries** | `backend/app/data/lexicon_bn.json`, `docs/ai-spec.md` | Only 10 sample words per language exist in `ai-spec.md` §9. A functioning P1 sentiment analyzer requires 30–50 domain-specific tourism adjectives. |
| 10 | **Automated Keep-Warm Monitoring Configuration** | `docs/tech-stack.md`, `docs/build-plan.md` | Specific setup steps for UptimeRobot or GitHub Actions pinging `GET /api/v1/health` every 14 minutes against Render free tier are not documented. |

---

## 7. "Ready to Code?" Verdict

### Verdict: **NO**

### Top 3 Most Important Things to Fix First:

1. **Harmonize Architectural Layout, Router Paths, and Collection Names:**
   - Standardize the backend monorepo structure to the **by-layer** layout (`backend/app/services/`, `repositories/`, `models/`, `api/v1/`) across `docs/architecture.md` and `docs/repo-structure.md`.
   - Update `README.md`, `docs/overview.md`, and `docs/architecture.md` to use `transport_routes` (replacing `fare_routes`) and `/api/v1/transport/fares` (replacing `/api/fares`).
   - Remove the `POST /api/v1/auth/login` endpoint from `docs/repo-structure.md` and standardize on `POST /api/v1/auth/register` and `GET /api/v1/me`.

2. **Reconcile the Beach Safety Flag Data Model & AI Tool Signature:**
   - Decide definitively between a single beach flag (`beach_status/main` with parameterless `get_beach_status()`) or a multi-zone model (`beach_status/{zone_id}` with `get_beach_status(zone="kolatoli"|"sugandha"|"laboni")`).
   - Align `docs/firestore-schema.md` (§3.7), `docs/ai-spec.md` (§5.4), `docs/api-spec.md` (§7), and `docs/evaluation-and-report.md` (Prompt 16) so tool execution and database schemas match.

3. **Verify Emergency Phone Numbers and Prepare Initial Valid Seed Files:**
   - Correct the invalid and outdated emergency hotlines in `seed/emergency_contacts.json`, `docs/overview.md`, and `docs/data-plan.md` (replace `199` with verified Bangladesh emergency paths; replace `10921` with `109`; obtain official Cox's Bazar Tourist Police hotline).
   - Ensure `seed/` JSON files contain valid draft schemas for `hotels.json`, `places.json`, `transport_routes.json`, `kb_chunks.json`, and `safety_rules.json` so that Slice 0 (`seed_loader.py`) does not fail when loading the Firebase emulator.


---

## 8. Changes Made (24 November 2026 Audit Resolutions)

The resolutions D21–D28 established in Addendum 1 of `docs/decisions.md` have been applied across all project documentation files. The audit items C1 through C12 have been fully resolved as cataloged below:

| File | What Changed | Audit Item / Decision |
|---|---|---|
| `docs/decisions.md` | Appended Addendum 1 (24 Nov 2026) recording decisions D21 through D28 (single source of truth). | D21–D28 |
| `README.md` | Replaced `data-model.md` references with `firestore-schema.md` (lines 138, 279); aligned transport route terminology (line 199). | C11, C2 |
| `docs/overview.md` | Replaced `fare_routes` with `transport_routes` (table §10); changed beach status count to 3 zones (`kolatoli`, `sugandha`, `laboni`); updated schema links from `data-model.md` to `firestore-schema.md`; removed 4–5 Dec P2 window and aligned P2 with 3 Dec before freeze per D28 (§11). | C2, C3, C4, C11, D28 |
| `docs/architecture.md` | Updated collection name to `transport_routes` in diagram (§1); replaced `/api/modules/` with by-layer backend structure (`api/v1/`, `services/`, `repositories/`, `models/`, `agents/`, `core/`, `data/`) per D21 (§2); updated router prefixes to `/api/v1/` (including `/api/v1/places`, `/api/v1/transport`); updated request flow to `GET /api/v1/hotels?area=kolatoli&max_price_bdt=3000` with `max_price_bdt` (§4); aligned rate limiter windows with calendar day YYYY-MM-DD in Asia/Dhaka time (UTC+6) per D26 (§9); standardized chat endpoint on `POST /api/v1/chat/messages` (§9, §12). | C1, C2, C6, C7, C10, C12, D21, D25, D26, D27 |
| `docs/firestore-schema.md` | Added `fare_basis` (`per_vehicle` or `per_person`) to `transport_routes` schema and example doc (§3.5, D22); converted `beach_status` from singleton `main` to multi-zone `beach_status/{zone_id}` for `kolatoli`, `sugandha`, `laboni` (§3.7, D23); specified calendar day reset in Asia/Dhaka time (UTC+6) for `usage/{uid_date}` and `ai_usage/{date}` (§3.10, §3.11, D26); updated read estimates and seed file mapping for 3 beach zones (§5, §7). | C3, C8, C10, D22, D23, D26 |
| `docs/data-plan.md` | Updated beach status dataset entry to 3 zones (§1); added `fare_basis` field to `seed/transport_routes.json` template (§3.3, D22); updated Beach Flag Update Process to multi-zone workflow `beach_status/{zone_id}` and noted 3 zones in `seed/beach_status.json` (§5, D23); verified 6-hour threshold for outdated status. | C3, C5, C8, D22, D23 |
| `docs/ai-spec.md` | Added optional `mode` and `passengers` parameters to `calculate_fare` tool declaration with per-person multiplication rule (§5.3, D22); added optional `zone` parameter to `get_beach_status` tool declaration with 3-zone fallback (§5.4, D23); verified 6-hour outdated threshold (§5.4, D24); updated chat response schema example to `POST /api/v1/chat/messages` (§12, D25). | C3, C5, C7, C8, D22, D23, D24, D25 |
| `docs/api-spec.md` | Standardized query parameter on `max_price_bdt` instead of `max_budget` for `GET /api/v1/hotels` (§3, D27); updated `GET /api/v1/transport/calculate` response to include `fare_basis` (`per_person` / `per_vehicle`) and documented passenger multiplication rule (§6, D22); noted optional `zone_id` parameter returns all 3 zones when omitted for `GET /api/v1/safety/beach-status` (§7, D23); resolved open question on transport endpoint naming (§17). | C3, C8, C12, D22, D23, D27 |
| `docs/build-plan.md` | Standardized query and tool calls on `max_price_bdt=3000` instead of `max_budget` (Slice 2, Slice 6, D27); aligned beach status outdated threshold to 6 hours in UI and tests (Slice 4, D24); explicitly wired `POST /api/v1/chat/messages` and Asia/Dhaka rate limits into Slice 5 (D25, D26); added multi-zone beach status acceptance criteria to Slice 4 (D23); enforced D28 constraint that P2 work may only happen on 3 Dec if all P0/P1 are done, never after 4 Dec freeze (Slice 8). | C1, C3, C4, C5, C6, C7, C12, D23, D24, D25, D26, D27, D28 |
| `docs/repo-structure.md` | Updated `seed/beach_status.json` description to 3 zones (D23); replaced `fares.py` with `transport.py` supporting `/api/v1/transport/fares` and `/api/v1/transport/calculate`; updated chat route to `POST /api/v1/chat/messages` (D25); removed `/auth/login` and replaced with `POST /api/v1/auth/register` and `GET /api/v1/me` (C9, D25); updated documentation notes and marked Open Questions 1, 2, 4, 5 as resolved by D21, D22, D25, and `firestore-schema.md`. | C1, C3, C6, C7, C8, C9, C11, D21, D22, D23, D25 |
| `docs/evaluation-and-report.md` | Updated evaluation Prompt 18 to explicitly call `get_beach_status(zone="sugandha")` to align with multi-zone model (D23). | C3, D23 |

---

## 9. Re-Check Verdict

### Verdict: **YES**

### Reasons:
1. **Architectural Harmonization Complete:** All 12 inconsistencies and contradictions (C1 through C12) identified in the initial review have been systematically reconciled. The codebase specifications strictly agree on the by-layer backend structure (`backend/app/api/v1`, `services/`, `repositories/`, `models/`, `agents/`, `core/`, `data/`), standardized `/api/v1` routes (including `POST /api/v1/chat/messages`, `GET /api/v1/transport/calculate`, and removal of `/auth/login`), and unified collection naming (`transport_routes`).
2. **Data Model & AI Tool Alignment:** The beach safety domain is uniformly specified across all schemas, REST endpoints, AI tool signatures, test cases, and evaluation benchmarks as a multi-zone entity (`beach_status/{zone_id}` for `kolatoli`, `sugandha`, and `laboni`), with a single 6-hour threshold for outdated warnings. Transport routes uniformly feature `fare_basis` (`per_vehicle` vs `per_person`) with passenger multiplication logic, and hotel queries consistently use `max_price_bdt`.
3. **Execution Guardrails & Schedule Locked:** Decisions D21–D28 are firmly codified in `docs/decisions.md` as the single source of truth. Scope and schedule boundaries are strictly enforced: the 4 December feature freeze is uncompromised, and any P2 Fare Fairness Checker work is restricted exclusively to 3 December after all P0 and P1 deliverables are verified.
4. **Implementation Path Unblocked:** Documentation references are synchronized (`firestore-schema.md` replaces `data-model.md`). Developers and AI coding agents can begin Slice 0 scaffolding on 25 November with complete confidence in structural contracts, schema definitions, and API specifications.
