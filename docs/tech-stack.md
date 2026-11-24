# PothSathi — Technology Stack

> Binding decisions live in [decisions.md](decisions.md). This file adds
> detail, rationale, and risk analysis.

---

## 1  Stack table

| Part | Choice | Details | Status |
| --- | --- | --- | --- |
| **Language (FE)** | TypeScript | Strict mode | Fixed |
| **Framework (FE)** | Next.js (App Router) | React 18+, SSR/SSG | Fixed |
| **Styling** | Tailwind CSS + shadcn/ui | Utility-first; accessible components | Fixed |
| **i18n** | next-intl | bn / en; Bengali digit parsing | Fixed |
| **Fonts** | Hind Siliguri, Noto Sans Bengali | Via `next/font/google` | Fixed |
| **Map** | react-leaflet + OpenStreetMap tiles | With mandatory attribution | Fixed |
| **Tile provider** | OSM `tile.openstreetmap.org` | See §3; CARTO Positron as lighter fallback | Recommended |
| **Data fetching (FE)** | TanStack Query | Caching, retries, stale-while-revalidate | Fixed |
| **Voice** | Web Speech API (browser) | bn-BD, en; P1 feature | Recommended |
| **Hosting (FE)** | Vercel Hobby | Non-commercial / personal use only | Fixed |
| **Language (BE)** | Python 3.11+ | Type hints throughout | Fixed |
| **Framework (BE)** | FastAPI | Async, OpenAPI docs | Fixed |
| **Hosting (BE)** | Render free (Docker) | 512 MB RAM, sleeps after 15 min inactivity | Fixed |
| **Database** | Cloud Firestore (Spark plan) | 1 GiB storage, 50 k reads/day | Fixed |
| **Auth** | Firebase Auth | Anonymous, Google, email/password | Fixed |
| **LLM** | Gemini API (free tier) | Model id from env `GEMINI_MODEL`; wrapped by `LLMClient` | Fixed |
| **Embeddings** | `gemini-embedding-001` (free tier) | 3072-dim; keyword fallback if quota hit | Recommended |
| **RAG index** | In-memory at startup | From `kb_chunks` collection; see §4 | Recommended |
| **Weather / marine** | Open-Meteo API | No key, free for non-commercial use | Recommended |
| **Tide data** | None confirmed | See §3 — no reliable free source verified | Later |
| **Emulator** | Firebase Emulator Suite | Local dev and tests | Fixed |

---

## 2  Why Firestore and how we lock it down

### Why Firestore

- Generous free tier (Spark): 1 GiB storage, 50 k reads / 20 k writes per day — plenty for a demo with ≤100 daily users.
- Firebase Auth integrates natively.
- Firebase Emulator Suite allows fully offline development and tests.
- JSON-document model matches our data shape (hotels, places, fare routes, KB chunks).

### Security rules — deny all client access

```javascript
// firestore.rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if false;   // all access goes through FastAPI
    }
  }
}
```

Only the FastAPI backend (using a service-account key) reads and writes
Firestore. The frontend never touches Firestore directly (login excepted —
Firebase Auth is a separate product).

### Repository layer

A Python `Repository` class wraps every Firestore call. The rest of the
backend imports `Repository`, never `google.cloud.firestore` directly.
This keeps Firestore swappable and testable.

### Cached public data

The backend holds a TTL cache (in-memory dict with expiry) for public
collections (hotels, places, fare routes, beach status). This reduces
Firestore reads and speeds up responses after a cold start.

### Emulator Suite

`APP_ENV=dev` or `test` → all Firestore and Auth calls hit the local
emulator. In `prod` the app **fails loudly** if the emulator env var is
set — it never accidentally talks to the emulator in production.

---

## 3  Things that change the plan

Each row was checked via web search in November 2026.
"Verify" = confirm before relying on it; "UNVERIFIED" = could not confirm.

| # | Issue | What it means | Plan | Source / status |
| --- | --- | --- | --- | --- |
| 1 | **Gemini API free-tier limits** | ~5 RPM, ~20 RPD for flagship Flash models (e.g. `gemini-3.8-flash`); lighter models like Flash-Lite may allow ~500 RPD. Limits are per-project, checked in AI Studio dashboard. | Use `gemini-3.8-flash` or the latest free Flash model. Set `GEMINI_MODEL` in env. Keep the global daily AI counter (D15) to stay under RPD. Build Tier 1 fallback. | ai.google.dev rate-limit dashboard — verify exact numbers at aistudio.google.com/rate-limit |
| 2 | **Gemini free-tier data use** | Google may use free-tier prompts and responses to improve products; human reviewers may read them. | Never send PII (name, email, phone) to Gemini. Show privacy note in the UI. Acceptable for a university demo. | ai.google.dev/gemini-api/terms — verify |
| 3 | **Free Flash models** | `gemini-3.8-flash` and `gemini-3.8-flash-lite` are available on the free tier. Model names change with new releases. | Pin `GEMINI_MODEL` in env, test with evaluation prompts (D18), update if a newer free model appears. | ai.google.dev/pricing — verify |
| 4 | **Gemini embedding model** | `gemini-embedding-001` is available on the free tier (3072 dims, 2048 input tokens). `gemini-embedding-2` also exists. Free-tier RPM/RPD limits apply. | Use `gemini-embedding-001`. Pre-compute embeddings for ≤300 KB chunks and store in Firestore. Keyword fallback if quota hit. | ai.google.dev/docs/embeddings — verify |
| 5 | **Firestore Spark limits** | 1 GiB storage, 50 k reads/day, 20 k writes/day, 20 k deletes/day, 10 GiB egress/month. One free DB per project. Resets ~midnight PT. Hard stop when quota hit. | Enough for MVP demo data. TTL cache in backend reduces reads. Monitor usage in Firebase console. | firebase.google.com/pricing — verify |
| 6 | **Render free-tier sleep** | 512 MB RAM, 0.1 CPU. Sleeps after 15 min of no traffic. Cold start ~1 min. 750 instance-hours/month. | Add a keep-warm cron ping (e.g. UptimeRobot free, or Vercel cron — Hobby allows 2 cron jobs/day only). Accept slow first load in demo. RAG index must rebuild quickly (≤300 chunks). | render.com/docs/free — verify |
| 7 | **Vercel Hobby terms** | Personal / non-commercial use only. 100 GB bandwidth, 1 M function invocations, 100 deploys/day, 2 cron jobs (daily only). No commercial use — Vercel can shut down violating projects. | Fine for university project. Before any commercial launch, migrate to Vercel Pro or another host. Do not rely on Vercel-only features (D5). | vercel.com/docs/limits — verify |
| 8 | **OSM tile usage policy** | Free `tile.openstreetmap.org` tiles require: custom User-Agent header, proper attribution ("© OpenStreetMap contributors"), no bulk downloading, no SLA. Traffic spikes can get the app blocked without notice. | Set correct User-Agent in react-leaflet. Add attribution. For a small university demo traffic is fine. If blocked, switch to CARTO Positron raster tiles (`basemaps.cartocdn.com/light_all/...`) — also free, no key, with CARTO + OSM attribution. | wiki.openstreetmap.org/wiki/Tile_usage_policy — verify |
| 9 | **Web Speech API — bn-BD** | Chrome: full support for recognition and synthesis (uses Google cloud, needs internet). Safari: recognition requires the user to enable Dictation and download the Bengali language pack; may fail silently if missing. Firefox: not supported. | Voice is P1. Target Chrome primarily. Show a "voice not supported" message on unsupported browsers. Text chat always works. | caniuse.com — Web Speech API — verify |
| 10 | **Weather / marine API** | Open-Meteo provides free weather and marine data (wave height, direction, period) for Cox's Bazar coords (21.43°N, 91.97°E). No API key needed for non-commercial use. No sign-up. | Use Open-Meteo Marine API for wave data as a beach-safety input. Cache responses (hourly). Not a replacement for admin-set beach flag — supplementary only. | open-meteo.com/en/docs/marine-weather-api — verify |
| 11 | **Tide data** | No reliable, free, no-key API for Cox's Bazar tides was confirmed. TidesAtlas exists but requires a key; reliability UNVERIFIED. Government tide gauges (BMD/BIWTA) have no public API. | Do not include tide data in MVP. If needed later, consider TidesAtlas free tier or manual data entry by admin. | UNVERIFIED |

---

## 4  RAG decision

The knowledge base has ≤300 curated text chunks stored in `kb_chunks`.
Three options for search:

| Option | How it works | Pros | Cons |
| --- | --- | --- | --- |
| **(A) In-memory vector index at startup** | Load all chunks + pre-computed embeddings from Firestore into a Python list at startup. Cosine similarity via numpy. | Simple. Fast search (<10 ms for 300 vectors). No external service. Survives Gemini-embedding downtime (uses cached embeddings). | Rebuild on every cold start (~5–15 s for 300 chunks). Uses some of the 512 MB RAM (small — ~5 MB for 300 × 3072-dim float32 vectors). |
| **(B) Numpy cosine over Firestore-loaded embeddings** | Same as A but loads embeddings on each search request instead of at startup. | No startup cost. | Slower per request (Firestore read latency). More Firestore reads. Worse UX. |
| **(C) Keyword search only** | TF-IDF or simple keyword match over chunk text. | No embedding model needed. | Much lower relevance. Fails on paraphrased or cross-language queries. |

### Recommendation: Option A — in-memory vector index

- 300 chunks × 3072 dims × 4 bytes = ~3.5 MB RAM — well within 512 MB.
- Startup rebuild: read 300 docs from Firestore (one batch query), load
  pre-computed embeddings. No Gemini call needed at startup.
- Embeddings are pre-computed offline (or via a seed script) using
  `gemini-embedding-001` and stored in `kb_chunks.embedding`.
- At search time: embed the query (1 Gemini embedding call), cosine
  similarity against 300 vectors, return top-k.
- If the embedding call fails at search time: fall back to keyword matching.

---

## 5  Cost table

| Item | Expected monthly cost | Notes |
| --- | --- | --- |
| Vercel Hobby | \$0 | Non-commercial, within limits |
| Render free | \$0 | 750 instance-hours; keep-warm ping |
| Firestore Spark | \$0 | Under 50 k reads/day for demo |
| Firebase Auth | \$0 | Under 50 k MAU |
| Gemini API free tier | \$0 | Under daily RPD; free-tier data-use terms |
| Open-Meteo | \$0 | Non-commercial, no key |
| OSM tiles | \$0 | Low traffic, with attribution |
| Domain name | \$0 | Use `*.vercel.app` subdomain |
| **Total** | **\$0** | |

### What would cost money later

| Item | Trigger | Estimated cost |
| --- | --- | --- |
| Vercel Pro | Commercial use or higher traffic | ~\$20/month (verify) |
| Render paid | Need always-on backend or more RAM | ~\$7/month (verify) |
| Firestore Blaze | >50 k reads/day sustained | Pay-as-you-go (verify) |
| Gemini paid tier | Need more RPD or data privacy | Pay-per-token (verify) |
| Custom domain | Branding | ~\$10–15/year (verify) |

---

## 6  Open questions

1. **Gemini RPD for Flash models** — the exact free-tier RPD for `gemini-3.8-flash` varies by project and may change. Must check the AI Studio dashboard before launch.
2. **Tide data** — no confirmed free API. Decide whether to skip entirely or add manual admin entry for high/low tide times.
3. **Keep-warm strategy** — Vercel Hobby allows only 2 daily cron jobs. Use an external free ping service (UptimeRobot) or accept cold starts?
4. **Embedding model choice** — `gemini-embedding-001` vs `gemini-embedding-2`: the newer model supports multimodal input but may have different free-tier limits. Test both.
5. **CARTO tile fallback** — CARTO's free raster tile service has no documented rate limit for small apps, but no SLA either. Confirm it still works without a key.

---

*End of tech-stack. ~120 lines.*
