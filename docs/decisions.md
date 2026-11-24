# PothSathi: Decisions v2 (single source of truth)

If another document disagrees with this file, this file wins until it is changed here first.

D1 Context. University project. Deadline 9 December 2026. Solo developer, zero budget, free tiers only, no payment card. The code stays portable so the site can be launched for tourists later (hosting may need to change for commercial use).
D2 Scope. Cox's Bazar, Bangladesh. First zones: Kolatoli, Sugandha, Laboni beach. Other areas are Later.
D3 Users and roles. tourist (guest through Firebase Anonymous Auth, or Google, or email/password) and admin (role set manually in Firestore).
D4 Stack. Frontend: Next.js (App Router), TypeScript, Tailwind, shadcn/ui, next-intl, react-leaflet with OpenStreetMap (with attribution), TanStack Query. Backend: FastAPI on Python 3.11+. Firebase Auth. Cloud Firestore. The frontend talks only to FastAPI (login excepted). Firestore client access is denied by security rules. A repository layer hides Firestore. Local development and tests use the Firebase Emulator Suite.
D5 Hosting. Frontend on Vercel Hobby (allowed for non-commercial university use; before a real commercial launch move to a host that allows commercial use). Backend on Render free (Docker) with a keep-warm ping. Do not rely on Vercel-only features.
D6 AI. Gemini API behind one wrapper class (LLMClient). Model id from env GEMINI_MODEL, chosen after testing with the evaluation prompts, and it must be available on the free tier (verify). No personal data in prompts (free tier data may be used by Google; the privacy note says so). Chat pipeline: (1) safety rule engine with Bengali, English and Banglish emergency keywords answers emergencies without the LLM; (2) Gemini with function calling over the tools search_hotels, find_nearby, calculate_fare, get_beach_status, search_knowledge; (3) a grounded answer with sources. If Gemini fails or the daily AI quota is used up: keyword intent router plus RAG, then a polite "AI is resting" message.
D7 RAG. Curated knowledge base (under 300 chunks) in Firestore collection kb_chunks. Index built in memory at startup. Embeddings from a Gemini embedding model with a keyword-matching fallback. No local embedding model on free hosting. Confirm in docs/tech-stack.md.
D8 Voice. Browser Web Speech API for input and output (bn-BD and en). Text always works. Voice is P1.
D9 Data truth. The system never invents hotel names, phones, fares, coordinates or rules. Real data comes from seed files that I fill and verify. Every record has data_source, is_verified, last_updated. Unverified or sample data shows a "sample / indicative" badge. Demo dataset target: 15-25 hotels, 30-40 places, 10-15 fare routes, 40-60 KB chunks.
D10 Graceful degradation. Tier 0 static: emergency numbers, fare table, hotel and place list, beach safety guide, SOS links (tel: and wa.me) built from the seed JSON into the frontend. Tier 1 live data from FastAPI with cache. Tier 2 AI chat. If a higher tier fails, the lower tier still works and shows "last updated".
D11 Features. P0: bilingual UI; hotel explorer with recommender; nearby essentials map; fare guide and calculator; beach safety status and SOS or emergency screen; AI chat (rules, tools, RAG). P1: hotel reviews with sentiment; minimal admin page (edit data, update beach flags); voice; report-wrong-info button. P2 (only ONE if time remains): Fare Fairness Checker (route plus asked fare gives fair, high or too high with a sourced range).
D12 Later. Trip planner, photo or menu translation, scam heatmap, PWA offline, push notifications, owner dashboard, more beaches, anything that needs a card.
D13 Safety. Guidance only, not legal or medical advice. Emergency number 999. Beach flag set by admin, always shows last_updated, old status shows "may be outdated". External weather data only after it is verified in docs/tech-stack.md.
D14 Privacy. Chat history kept 30 days at most. Precise location only for SOS events, minimal. Never log chat text, request bodies or coordinates. Never send name, email or phone to Gemini.
D15 Cost and abuse control. Per-user daily chat limit (50), token limit per request, IP limit for guests, a global daily AI counter ("AI rest mode" when used up), TTL cache of public data in backend memory.
D16 Language. bn and en. One translations source. Bengali digits are parsed. Fonts: Hind Siliguri and Noto Sans Bengali.
D17 Process and timeline. Docs 20-21 Nov. Feature freeze 4 Dec. Code freeze 6 Dec. Report, slides and demo video 7-8 Dec. Submit 9 Dec. One slice per branch and per session. Documents first, then code. Scope cut order if behind: P2, voice, admin page, reviews, then AI tools beyond search_hotels, find_nearby and calculate_fare.
D18 Evaluation (for grading). 50 Bengali and English test prompts comparing plain Gemini with Gemini plus rules, tools and RAG (accuracy and hallucination rate); emergency rule accuracy; a usability test with 10-15 users and the SUS questionnaire; a comparison with Google Maps and TripAdvisor (gap analysis); architecture, data model and sequence diagrams for the report.
D19 Environments. APP_ENV is dev, test or prod. Emulator in dev and test. In prod the app fails loudly if Firestore or Gemini keys are missing.
D20 Agent models. Claude Opus 4.6 (thinking) for documents and hard slices (orchestrator, auth, security, rate limiting, RAG). Gemini Flash for scaffolding, UI, translations, simple CRUD and tests.


## Addendum 1 (24 Nov 2026): review resolutions

D21 Backend layout is by layer: backend/app/api/v1 (routers), backend/app/services, backend/app/repositories, backend/app/models, backend/app/agents, backend/app/core, backend/app/data. The modules named in docs/architecture.md are logical groups expressed as file names (for example hotel_service.py, hotel_repository.py, hotels.py router), not separate folders.
D22 The transport collection is named transport_routes everywhere. Each route has fare_basis (per_vehicle or per_person), vehicle_type, fare_min_bdt, fare_max_bdt. calculate_fare and GET /api/v1/transport/calculate take origin, destination, optional mode, optional passengers; passengers multiplies the fare only when fare_basis is per_person.
D23 Beach status is multi-zone: collection beach_status/{zone_id} with zone_ids kolatoli, sugandha, laboni (seed file beach_status.json has 3 zones). Tool get_beach_status takes optional zone; without zone it returns all three zones.
D24 A beach status older than 6 hours shows "may be outdated" (UI, tests and API all use 6 hours).
D25 All REST routes use the prefix /api/v1. Chat endpoint is POST /api/v1/chat/messages with body {message, session_id?, language?}. There is no /auth/login endpoint (login is the Firebase client SDK); use POST /api/v1/auth/register and GET /api/v1/me.
D26 Daily counters (usage/{uid_date}, ai_usage/{date}) reset by calendar date YYYY-MM-DD in Asia/Dhaka time (UTC+6).
D27 The hotel budget parameter is named max_price_bdt everywhere (tool schema, REST query, tests, examples).
D28 P2 work (Fare Fairness Checker) may only happen on 3 Dec after all P0 and P1 are done, never after the 4 Dec feature freeze.
