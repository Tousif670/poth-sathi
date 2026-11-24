# PothSathi — Project Overview

> This document gives a bird's-eye view of PothSathi.
> For binding decisions see [decisions.md](decisions.md).
> For technology choices see [tech-stack.md](tech-stack.md).

---

## 1  What is PothSathi

Cox's Bazar draws millions of domestic tourists every year, yet visitors
face four recurring problems:

| Problem | Impact |
| --- | --- |
| **Inflated transport fares** | Auto-rickshaw and CNG drivers often quote well above fair rates to new arrivals. |
| **Misleading hotel tariffs** | Walk-in prices differ from online prices; hidden charges surprise guests. |
| **Beach safety hazards** | Strong currents and tidal surges cause drownings every season; tourists get no real-time warnings. |
| **No verified emergency info** | Emergency numbers, nearest hospital, pharmacy at night — hard to find, especially in Bengali. |

**PothSathi** (পথসাথী, "travel companion") is a bilingual (Bengali & English)
AI-powered tourism website that solves these problems for Cox's Bazar.
It provides verified local data — hotel prices, transport fares, beach safety
status, nearby essentials, and emergency contacts — through a chat-first
interface grounded in curated facts, never hallucinated.

---

## 2  Who uses it

| Persona | Language | Typical goal | Auth |
| --- | --- | --- | --- |
| **Family tourist** | Bengali | Fair fare, safe beach, nearby pharmacy | Guest (anon) or Google |
| **Solo traveller** | Bengali or English | Budget hotel, nightlife safety, ATM | Guest or email |
| **Foreign visitor** | English | Directions, emergency help, cultural tips | Guest or Google |
| **Admin** | Bengali or English | Update hotel data, set beach flag, manage KB | Email (role in Firestore) |

All tourist personas can use the site without creating an account
(Firebase Anonymous Auth). Login unlocks chat history and favourites.

---

## 3  Features at a glance

Priority key — **P0**: must ship; **P1**: should ship; **P2**: one item if time remains; **Later**: post-MVP.

| # | Feature | Pri | What it does |
| --- | --- | --- | --- |
| 1 | Bilingual UI | P0 | Full bn / en interface via `next-intl`. Bengali digit parsing. |
| 2 | Hotel Explorer | P0 | Browse 15–25 verified hotels with filters, map pins, recommender. |
| 3 | Nearby Essentials Map | P0 | Hospitals, pharmacies, ATMs, mosques, police on OSM via react-leaflet. |
| 4 | Fare Guide & Calculator | P0 | 10–15 verified routes with fare ranges; calculator for custom trips. |
| 5 | Beach Safety & SOS | P0 | Admin-set beach flag (with `last_updated`), emergency screen, `tel:` / `wa.me` links. |
| 6 | AI Chat | P0 | Safety rules → Gemini + tools → grounded answer with sources. Fallback: keyword + RAG → "AI is resting". |
| 7 | Hotel reviews + sentiment | P1 | User-submitted reviews with basic sentiment tagging. |
| 8 | Admin page | P1 | Edit hotel/place data, update beach flag, manage KB chunks. |
| 9 | Voice input / output | P1 | Browser Web Speech API (bn-BD, en). Text always works. |
| 10 | Report wrong info | P1 | One-tap button to flag incorrect data for admin review. |
| 11 | Fare Fairness Checker | P2 | Enter route + asked fare → fair / high / too high, with sourced range. |
| 12 | Trip planner, PWA, more beaches… | Later | See D12 in decisions.md. |

---

## 4  The app through the user's eyes

### Screens

| Screen | Key content |
| --- | --- |
| **Home** | Chat panel (primary CTA), language toggle, quick links to Hotels / Fares / Beach Safety. |
| **Hotels** | Card list with filters (area, price range, amenities). Map pins. Tap → detail + recommender. |
| **Nearby Map** | Full-width OSM map. Category chips: hospital, pharmacy, ATM, mosque, police. |
| **Fares** | Route table with fare ranges. Calculator: pick origin + destination → estimated fare. |
| **Beach Safety** | Current flag colour, `last_updated`, safety tips, link to SOS. |
| **Emergency / SOS** | Emergency numbers (tel: links), nearest hospital, police, one-tap WhatsApp link. |
| **Login / Guest** | Continue as guest (anon auth) or sign in (Google / email). |
| **Admin** | (P1) Data editor, beach flag setter, KB chunk manager. Protected route. |

### Navigation

- Bottom tab bar on mobile (Home, Hotels, Nearby, Fares, Safety).
- Top nav on desktop.
- Language switch (🌐 button) is always visible — toggles bn ↔ en instantly.

---

## 5  The AI system in plain words

### Chat pipeline (runs on the backend)

```
User message
  │
  ▼
┌──────────────────────────┐
│ 1. Safety Rule Engine    │  Catches emergency keywords in bn, en, Banglish.
│    (no LLM needed)       │  Returns pre-written emergency response instantly.
├──────────────────────────┤
│ 2. Gemini + Tools        │  LLM with function calling:
│                          │    search_hotels  — query hotel data
│                          │    find_nearby    — nearby places by category
│                          │    calculate_fare — fare estimate for a route
│                          │    get_beach_status — current beach flag
│                          │    search_knowledge — RAG over KB chunks
├──────────────────────────┤
│ 3. Grounded Answer       │  Gemini composes a response citing tool results.
│    with sources          │  Every claim links to its data source.
└──────────────────────────┘
         │  if Gemini fails or quota exhausted
         ▼
┌──────────────────────────┐
│ Fallback: keyword intent │  Simple keyword matching → direct DB lookup.
│ router + RAG             │  If that fails too → polite "AI is resting" message.
└──────────────────────────┘
```

### Three tiers of service (D10)

| Tier | What works | When it kicks in |
| --- | --- | --- |
| **Tier 0 — Static** | Emergency numbers, fare table, hotel list, place list, beach safety guide, SOS links. Built from seed JSON into the frontend at build time. | Always available, even if the backend is down. |
| **Tier 1 — Live data** | All Tier 0 data served fresh from FastAPI + Firestore, with backend TTL cache. | Backend is up, Gemini may or may not be. |
| **Tier 2 — AI Chat** | Full conversational AI with tools and grounded answers. | Backend + Gemini API both available and under quota. |

If a higher tier fails, the lower tier still works. The UI shows
"last updated" timestamps so the user knows how fresh the data is.

### When AI is down

- The chat box shows: **"আমাদের AI সহকারী এখন বিশ্রামে আছে। নিচের তথ্যগুলো দেখুন।"**
  ("Our AI assistant is resting. See the information below.")
- Static fare tables, hotel cards, and emergency info remain fully usable.

---

## 6  A day in the life

> All numbers below are **EXAMPLE placeholders** — not real prices or data.

**Scenario:** The Rahman family arrives at Kolatoli by bus from Dhaka. They
open PothSathi on a phone browser (Bengali). Five questions:

1. **"কোলাতলী থেকে লাবণী বিচে যেতে কত ভাড়া?"**
   → Fare Guide tool returns: *CNG auto: ৳EXAMPLE_80–৳EXAMPLE_120 (verify).
   Source: seed fare data, last updated EXAMPLE_DATE.*

2. **"সুইমিং পুল আছে এমন হোটেল, বাজেট ৳EXAMPLE_3000 এর নিচে?"**
   → Hotel search tool filters by amenity and price. Returns 2–3 hotel cards
   with names from seed data, each marked "sample / indicative".

3. **"আজ সমুদ্র নিরাপদ?"**
   → Beach status tool returns: *Flag: EXAMPLE_YELLOW. Set by admin at
   EXAMPLE_TIME. "সাবধানে সাঁতার কাটুন।"*
   If the status is older than 6 hours, a warning appears: "may be outdated".

4. **"রাতে কাছের ফার্মেসি কোথায়?"**
   → Nearby places tool returns the closest pharmacy with distance.
   Map pin shown. Opening hours from seed data or "hours not verified".

5. **"মানিব্যাগ হারিয়ে গেছে, কী করব?"**
   → Safety Rule Engine detects distress keyword ("হারিয়ে গেছে").
   Instant response: nearest police station, Tourist Police number
   (EXAMPLE_NUMBER — TO VERIFY), and step-by-step advice.

---

## 7  Emergency handling

- The **Safety Rule Engine** runs before Gemini, with zero latency.
- Keyword lists cover Bengali, English, and Banglish variants of:
  drowning, accident, fire, theft, lost, medical, police, ambulance.
- Emergency responses are pre-written, reviewed, and stored in code — never generated by the LLM.
- The **SOS screen** (always Tier 0) shows:

| Service | Number | Status |
| --- | --- | --- |
| National Emergency | 999 | TO VERIFY |
| Fire Service | 199 | TO VERIFY |
| Ambulance (Red Crescent) | 199 | TO VERIFY |
| Women & Children Helpline | 10921 | TO VERIFY |
| Tourist Police | TBD | TO VERIFY |

- One-tap `tel:` and `wa.me` links.
- If the user grants location, coordinates are shown so they can relay them verbally.

---

## 8  Trust and data verification

- **No invented facts.** Every hotel name, phone number, fare, and coordinate
  comes from seed JSON files that the developer fills and manually verifies.
- Every record has three metadata fields: `data_source`, `is_verified`,
  `last_updated`.
- Unverified or sample data shows a **"sample / indicative"** badge in the UI.
- The AI is instructed to cite sources in every answer; if no source exists
  the AI says "I don't have verified information for that".
- A **"Report wrong info"** button (P1) lets users flag errors for admin review.

---

## 9  Technical architecture (short)

> Full details will be in [architecture.md](architecture.md).

```
Browser (Next.js on Vercel Hobby)
   │  all API calls (login excepted)
   ▼
FastAPI backend (Render free, Docker)
   ├── Safety Rule Engine
   ├── Gemini LLMClient wrapper + function-calling tools
   ├── RAG index (in-memory, rebuilt at startup)
   ├── Repository layer (hides Firestore)
   └── Rate / abuse limits
   │
   ├──▶ Cloud Firestore (Spark plan)
   └──▶ Gemini API (free tier)

Firebase Auth (called directly from frontend for login only)
```

- Frontend talks **only** to FastAPI; Firestore security rules deny all client reads/writes.
- Firebase Emulator Suite for local dev and tests.
- In production: fail loudly if keys are missing; never serve mock data.

---

## 10  Core data entities

| Collection | Key fields | Approx count |
| --- | --- | --- |
| `hotels` | name, area, price_range, amenities, coordinates, is_verified | 15–25 |
| `places` | name, category, coordinates, opening_hours, is_verified | 30–40 |
| `transport_routes` | origin, destination, vehicle_type, fare_basis, fare_min, fare_max | 10–15 |
| `beach_status` | flag_colour, set_by, last_updated, note | 3 zones (kolatoli, sugandha, laboni) |
| `kb_chunks` | text, embedding, source, category | 40–60 |
| `users` | uid, role, display_name, created_at | — |
| `chat_sessions` | user_id, messages[], created_at, expires_at | — |
| `reviews` | hotel_id, user_id, text, sentiment, created_at | P1 |

> Full schemas in [firestore-schema.md](firestore-schema.md).

---

## 11  MVP scope and timeline

From D11, D12, D17, D28.

| Phase | Dates | Deliverables |
| --- | --- | --- |
| **Docs** | 20–21 Nov | decisions.md, overview.md, tech-stack.md, build-plan.md, firestore-schema.md |
| **Build P0** | 22 Nov – 3 Dec | Bilingual UI, hotel explorer, nearby map, fare guide, beach safety, SOS, AI chat |
| **Build P1** | 1–3 Dec (overlap) | Reviews, admin page, voice, report button — only if P0 is done |
| **P2 (if time)** | 3 Dec | Fare Fairness Checker — only if all P0 & P1 done, never after freeze (D28) |
| **Feature freeze** | 4 Dec | Hardening & deployment — no new features after this date |
| **Testing & Evaluation** | 5–6 Dec | 50-prompt evaluation, SUS usability study, critical bug fixes |
| **Code freeze** | 6 Dec | Bug fixes only (evening) |
| **Report & demo** | 7–8 Dec | Report, slides, demo video, evaluation results |
| **Submit** | 9 Dec | Final submission |

**Scope cut order** (if behind schedule):
P2 → voice → admin page → reviews → AI tools beyond `search_hotels`,
`find_nearby`, and `calculate_fare`.

---

## 12  Safety, privacy and responsibility

| Area | Rule |
| --- | --- |
| **Guidance only** | PothSathi gives travel guidance, not legal or medical advice. |
| **Chat retention** | Chat history kept 30 days at most, then deleted. |
| **Location** | Precise location used only for SOS events, minimal. Never logged. |
| **Logging** | Never log chat text, request bodies, or coordinates. |
| **PII to LLM** | Never send name, email, or phone to Gemini. |
| **Free-tier data use** | Free-tier Gemini data may be used by Google to improve products. The privacy note in the UI says so. |
| **Disclaimer** | "PothSathi is a university project. Data is indicative. Verify critical information independently." |

---

*End of overview. ~210 lines.*
