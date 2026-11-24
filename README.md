# PothSathi — পথসাথী

**Your bilingual AI travel companion for Cox's Bazar**

> This README describes the target design. The system is built in small slices; see [docs/build-plan.md](docs/build-plan.md).

PothSathi is a bilingual (Bengali & English) AI-powered tourism website for Cox's Bazar, Bangladesh. It helps tourists find hotels, navigate local transport fares, check beach safety, locate nearby essentials, and chat with an AI assistant — all grounded in verified local data, never hallucinated.

---

## Features

### P0 — Must have

| Feature | Description |
| --- | --- |
| **Bilingual UI** | Full Bengali (bn) and English (en) interface with `next-intl`. Bengali digit parsing. Fonts: Hind Siliguri, Noto Sans Bengali. |
| **Hotel Explorer** | Browse 15–25 verified hotels with filters, map pins, and a recommender. |
| **Nearby Essentials Map** | Find hospitals, pharmacies, ATMs, mosques, police — plotted on OpenStreetMap via react-leaflet (with attribution). |
| **Fare Guide & Calculator** | 10–15 verified local transport routes with fare ranges; calculator for custom trips. |
| **Beach Safety & SOS** | Admin-set beach flag (always shows `last_updated`; old status shows "may be outdated"). Emergency screen with SOS links (`tel:`, `wa.me`). Emergency number: **999** — *TO VERIFY before launch*. |
| **AI Chat** | Three-layer pipeline: **(1)** safety rule engine — catches emergency keywords in Bengali, English and Banglish and answers without the LLM; **(2)** Gemini with function-calling tools (`search_hotels`, `find_nearby`, `calculate_fare`, `get_beach_status`, `search_knowledge`); **(3)** grounded answer with sources. Fallback: keyword intent router + RAG, then a polite "AI is resting" message when the daily quota is used up. |

### P1 — Should have

- Hotel reviews with sentiment analysis
- Minimal admin page (edit data, update beach flags)
- Voice input / output (browser Web Speech API, bn-BD and en)
- "Report wrong info" button

### P2 — Could have (only ONE if time remains)

- **Fare Fairness Checker** — enter route + asked fare → fair / high / too high, with a sourced range.

### Later

Trip planner · photo or menu translation · scam heatmap · PWA offline · push notifications · owner dashboard · more beaches · anything that needs a payment card.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        Tourist                          │
│               (browser, bn / en)                        │
└────────────────────────┬────────────────────────────────┘
                         │
          ┌──────────────▼──────────────┐
          │   Next.js Frontend          │
          │   (Vercel Hobby)            │
          │   App Router · Tailwind     │
          │   shadcn/ui · next-intl     │
          │   react-leaflet + OSM       │
          │   TanStack Query            │
          │   Web Speech API (voice)    │
          │   Tier 0 static fallback    │
          └──────────────┬──────────────┘
                         │  all API calls
                         │  (login excepted)
          ┌──────────────▼──────────────┐
          │   FastAPI Backend           │
          │   (Render free, Docker)     │
          │                             │
          │ ┌─────────────────────────┐ │
          │ │ 1. Safety Rule Engine   │ │
          │ │    emergency keywords   │ │
          │ │    (bn, en, Banglish)   │ │
          │ ├─────────────────────────┤ │
          │ │ 2. Gemini + Tools       │ │
          │ │    LLMClient wrapper    │ │
          │ │    function calling:    │ │
          │ │    search_hotels        │ │
          │ │    find_nearby          │ │
          │ │    calculate_fare       │ │
          │ │    get_beach_status     │ │
          │ │    search_knowledge     │ │
          │ ├─────────────────────────┤ │
          │ │ 3. Grounded Answer      │ │
          │ │    with sources         │ │
          │ ├─────────────────────────┤ │
          │ │ Fallback: keyword       │ │
          │ │ intent router + RAG     │ │
          │ │ → "AI is resting"       │ │
          │ └─────────────────────────┘ │
          │                             │
          │   RAG index (in-memory)     │
          │   Repository layer          │
          │   Rate / abuse limits       │
          └──────┬────────────┬─────────┘
                 │            │
     ┌───────────▼──┐  ┌─────▼──────────┐
     │  Cloud       │  │  Gemini API    │
     │  Firestore   │  │  (free tier)   │
     │              │  │  GEMINI_MODEL  │
     │  kb_chunks   │  │  from env      │
     │  (RAG data)  │  └────────────────┘
     │              │
     │  Firebase    │
     │  Auth        │
     └──────────────┘
```

**Key architectural rules:**

- The frontend talks **only** to FastAPI (login excepted). Firestore client access is denied by security rules.
- A **repository layer** hides Firestore from the rest of the backend.
- **Firebase Emulator Suite** is used for local development and tests. In production the app **fails loudly** with a clear error if Firestore or Gemini is unreachable — it **never serves mock data**.
- **RAG index** is rebuilt in memory at startup from the Firestore collection `kb_chunks` (no persistent disk on free hosting).
- **Graceful degradation:** Tier 0 (static fallback built from seed JSON) → Tier 1 (live data with cache) → Tier 2 (AI chat). If a higher tier fails, the lower tier still works and shows "last updated".

---

## Prerequisites

- **Python 3.11+**
- **Node.js 20+**
- Firebase CLI (for the Emulator Suite)
- A Gemini API key (free tier)
- Git

---

## Project Structure

```
poth-sathi/
├── frontend/              # Next.js app
│   ├── .env.example
│   └── ...
├── backend/               # FastAPI app
│   ├── .env.example
│   └── ...
├── docs/                  # Project documentation
│   ├── decisions.md
│   ├── build-plan.md
│   ├── tech-stack.md
│   ├── firestore-schema.md
│   └── ...
├── seed/                  # Verified seed data (JSON)
└── README.md
```

> **Note:** Real `.env` files and service-account key files are git-ignored. Only `.env.example` files are committed.

---

## Quick start (backend)

Follow these exact steps from the repository root:

```bash
# 1. Create and activate Python 3.11+ virtual environment
python3.11 -m venv backend/.venv
source backend/.venv/bin/activate

# 2. Install pinned dependencies
pip install -r backend/requirements.txt

# 3. Setup environment file
cp backend/.env.example backend/.env

# 4. Start Firebase Emulators (Firestore & Auth) in a separate terminal
firebase emulators:start --only firestore,auth

# 5. Populate local emulator with verified seed data
python scripts/seed_loader.py

# 6. Start FastAPI backend development server
cd backend
uvicorn app.main:app --reload --port 8000

# 7. Run backend test suite
pytest

# 8. Run code formatting and linting check
ruff check
```

---

## Quick start (frontend)

Follow these exact steps from the repository root:

```bash
# 1. Enter frontend directory and install dependencies
cd frontend
npm install

# 2. Setup local environment file
cp .env.example .env.local

# 3. Start Next.js development server (http://localhost:3000)
npm run dev

# 4. Run linter, unit tests, and production build
npm run lint
npm test
npm run build
```

---

## How to run everything locally

Run the full stack in **3 separate terminals** from the repository root:

- **Terminal 1 — Firebase Emulators:**
  ```bash
  firebase emulators:start --only firestore,auth
  ```
  *(Optional first-time seed once emulators are ready: `source backend/.venv/bin/activate && python scripts/seed_loader.py`)*

- **Terminal 2 — FastAPI Backend (`http://localhost:8000`):**
  ```bash
  source backend/.venv/bin/activate
  cd backend
  uvicorn app.main:app --reload --port 8000
  ```

- **Terminal 3 — Next.js Frontend (`http://localhost:3000`):**
  ```bash
  cd frontend
  npm run dev
  ```

---

## Getting Started

### 1. Clone the repo

```bash
git clone <repo-url>
cd poth-sathi
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in your keys
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local  # fill in your keys
npm run dev
```

### 4. Firebase Emulators (for local development)

```bash
firebase emulators:start
```

---

## Voice

Voice input and output use the **browser Web Speech API** (bn-BD and en). No server-side speech processing is required for the core flow. Text chat always works; voice is P1.

> **Later:** Backend `/speech` endpoints and `speech_service.py` are planned for server-side speech if the Web Speech API proves insufficient on some devices. These are not part of the current build.

---

## Data Integrity

- The system **never invents** hotel names, phone numbers, fares, coordinates, or rules.
- All data comes from seed files that are manually filled and verified.
- Every record carries `data_source`, `is_verified`, and `last_updated`.
- Unverified or sample data displays a **"sample / indicative"** badge.
- Demo dataset target: 15–25 hotels, 30–40 places, 10–15 transport routes, 40–60 KB chunks.

### Emergency Numbers

| Service | Number | Status |
| --- | --- | --- |
| National Emergency | 999 | **TO VERIFY before launch** |
| Fire Service | 199 | **TO VERIFY before launch** |
| Ambulance (Red Crescent) | 199 | **TO VERIFY before launch** |
| Women & Children Helpline | 10921 | **TO VERIFY before launch** |
| Tourist Police | TBD | **TO VERIFY before launch** |

---

## Privacy & Safety

- Guidance only — not legal or medical advice.
- Chat history kept **30 days at most**.
- Precise location used only for SOS events, minimal.
- Never logs chat text, request bodies, or coordinates.
- Never sends name, email, or phone to Gemini.
- Free-tier Gemini data may be used by Google; the privacy note says so.

---

## Cost & Abuse Control

- Per-user daily chat limit (50)
- Token limit per request
- IP rate limit for guests
- Global daily AI counter — "AI rest mode" when exhausted
- TTL cache of public data in backend memory

---

## Environments

`APP_ENV` is `dev`, `test`, or `prod`.

| Environment | Firestore | Behavior on missing keys |
| --- | --- | --- |
| `dev` | Firebase Emulator | Warn |
| `test` | Firebase Emulator | Fail |
| `prod` | Cloud Firestore | **Fail loudly** — never serve mock data |

---

## Roadmap

### P0 — Must have (build first)

Bilingual UI · hotel explorer with recommender · nearby essentials map · fare guide and calculator · beach safety status and SOS / emergency screen · AI chat (safety rules → Gemini with tools → grounded answer with sources; fallback to keyword + RAG).

### P1 — Should have

Hotel reviews with sentiment · minimal admin page (edit data, update beach flags) · voice (Web Speech API) · report-wrong-info button.

### P2 — Could have (only ONE if time remains)

Fare Fairness Checker (route + asked fare → fair / high / too high with sourced range).

### Later

Trip planner · photo or menu translation · scam heatmap · PWA offline · push notifications · owner dashboard · more beaches · anything that needs a payment card.

### Scope cut order (if behind schedule)

P2 → voice → admin page → reviews → AI tools beyond `search_hotels`, `find_nearby`, and `calculate_fare`.

---

## Documentation

The following files will exist in `docs/`:

| File | Purpose |
| --- | --- |
| [decisions.md](docs/decisions.md) | Single source of truth for all project decisions |
| [build-plan.md](docs/build-plan.md) | Ordered build slices and session plan |
| [tech-stack.md](docs/tech-stack.md) | Detailed technology choices, versions, and rationale |
| [firestore-schema.md](docs/firestore-schema.md) | Firestore collections, schemas, and seed format |

---

## License

University project. Not yet licensed for commercial use.
