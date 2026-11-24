# PothSathi — AI Specification

> Binding decisions: [decisions.md](decisions.md).
> Architecture context: [architecture.md](architecture.md).
> Tech stack detail: [tech-stack.md](tech-stack.md).

---

## 1  Principles

1. **Safety first.** Emergency keywords are caught *before* the LLM. The
   response is pre-written, never generated.
2. **Grounded answers.** Every factual claim must cite a data source (seed
   data, Firestore record, or KB chunk). If no source exists the AI says
   "I don't have verified information for that."
3. **No invented facts.** Hotel names, fares, phone numbers, coordinates —
   always from seed/Firestore, never hallucinated.
4. **Bilingual.** The AI responds in the language the user writes in. The
   system prompt instructs this explicitly.
5. **Privacy.** Never send PII (name, email, phone) to Gemini. Free-tier
   data may be used by Google; the user is told (D14).
6. **Graceful degradation.** If Gemini fails → keyword + RAG fallback.
   If that fails → polite "AI is resting" message. Static data always works.
7. **Budget-aware.** A global daily AI counter stops calls before the
   free-tier quota is exceeded (D15).

---

## 2  LLMClient Wrapper

All LLM calls go through one class: `backend/app/core/llm_client.py`.

### Interface

```python
class LLMClient:
    """Wrapper around the Gemini API. One instance per app."""

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDeclaration] | None = None,
        system_prompt: str | None = None,
    ) -> LLMResponse: ...

    async def embed(self, text: str) -> list[float]: ...
```

### Env config

| Variable | Purpose | Example |
| --- | --- | --- |
| `GEMINI_API_KEY` | API key for Gemini | `AIza...` |
| `GEMINI_MODEL` | Chat model id (must be free-tier) | `gemini-3.8-flash` |
| `GEMINI_EMBEDDING_MODEL` | Embedding model id | `gemini-embedding-001` |

### Timeouts and retries

| Setting | Value | Rationale |
| --- | --- | --- |
| Request timeout | 30 s | Long enough for tool-calling round-trips |
| Max retries | 2 | On 429 or 503 only |
| Retry backoff | 2 s, then 4 s | Exponential, capped |
| Max input tokens | 4 096 | Keeps cost low; rejects long prompts |
| Max output tokens | 1 024 | Enough for a detailed answer with cards |

### Error types

| Error | Mapped to |
| --- | --- |
| 429 Too Many Requests | `LLMQuotaError` → triggers fallback |
| 503 Service Unavailable | `LLMUnavailableError` → triggers fallback |
| Timeout | `LLMTimeoutError` → triggers fallback |
| 400 Bad Request | `LLMBadRequestError` → log, return error to user |
| Any other | `LLMUnknownError` → log, return error to user |

### Fake client for tests

`FakeLLMClient` implements the same interface. Returns canned responses
from a fixture file. Used when `APP_ENV=test`. Never returns mock data
in `prod` (D19).

---

## 3  Request Pipeline

```
User message (text, bn or en)
  │
  ├─ 1. Input validation (length ≤ 2000 chars, strip PII patterns)
  ├─ 2. Rate limit check (per-user, per-IP, global AI counter)
  ├─ 3. Language detection (simple heuristic: Bengali Unicode range)
  │
  ▼
  4. Safety Rule Engine ──► match? ──► return pre-written response (no LLM)
  │                           no
  ▼
  5. Gemini chat with tools
  │   ├─ system prompt (§6)
  │   ├─ conversation history (last 10 messages)
  │   ├─ tool declarations (§5)
  │   ├─ user message
  │   │
  │   ├─ Gemini may call 1+ tools
  │   │     └─ tool execution through Services (§5)
  │   │     └─ results returned to Gemini
  │   │
  │   └─ Gemini produces grounded answer with sources
  │
  ├─ on success → 6. Build response JSON (§12)
  │
  ├─ on LLM error → 7. Fallback: keyword intent router + RAG (§11)
  │
  └─ on fallback failure → 8. Polite "AI is resting" message
  │
  ▼
  9. Save to chat_sessions (async, no PII in logs)
```

---

## 4  Safety Rule Engine

Runs **before** the LLM on every message. Zero-latency, zero-cost.

### Categories

| # | Category | Action | Response includes |
| --- | --- | --- | --- |
| 1 | Drowning / rip current | EMERGENCY | 999, nearest lifeguard/hospital, safety steps |
| 2 | Medical emergency | EMERGENCY | 999, nearest hospital, first-aid tips |
| 3 | Theft / harassment | EMERGENCY | 999, Tourist Police (TO VERIFY), police station |
| 4 | Lost person / child | URGENT | Tourist Police (TO VERIFY), police station, steps |
| 5 | Fire | EMERGENCY | 199 (TO VERIFY), fire station, evacuation tips |
| 6 | Other danger | URGENT | 999, context-dependent advice |

### File: `backend/app/data/safety_rules.json`

> **REVIEW** — keywords below are EXAMPLES only. A native Bengali speaker
> must review and expand this list before launch.

**Structure (one entry per category):**

```json
{
  "rules": [
    {
      "category": "drowning_rip_current",
      "keywords_bn": ["ডুবে যাচ্ছে", "স্রোত", "ডুবে গেছে"],
      "keywords_en": ["drowning", "rip current", "swept away"],
      "keywords_banglish": ["dube jacche", "srot", "dube geche"],
      "action": "EMERGENCY",
      "response_key": "emergency_drowning"
    },
    {
      "category": "medical_emergency",
      "keywords_bn": ["হার্ট অ্যাটাক", "রক্তক্ষরণ", "অজ্ঞান"],
      "keywords_en": ["heart attack", "bleeding", "unconscious"],
      "keywords_banglish": ["heart attack", "roktokhoron", "ojjan"],
      "action": "EMERGENCY",
      "response_key": "emergency_medical"
    },
    {
      "category": "theft_harassment",
      "keywords_bn": ["চুরি", "ছিনতাই", "হয়রানি"],
      "keywords_en": ["stolen", "robbed", "harassment"],
      "keywords_banglish": ["churi", "chhintai", "harassment"],
      "action": "EMERGENCY",
      "response_key": "emergency_theft"
    },
    {
      "category": "lost_person_child",
      "keywords_bn": ["হারিয়ে গেছে", "খুঁজে পাচ্ছি না", "শিশু হারিয়ে"],
      "keywords_en": ["lost child", "missing person", "can't find"],
      "keywords_banglish": ["hariye geche", "khuje pacchi na", "bachcha hariye"],
      "action": "URGENT",
      "response_key": "emergency_lost"
    },
    {
      "category": "fire",
      "keywords_bn": ["আগুন", "আগুন লেগেছে", "পুড়ে যাচ্ছে"],
      "keywords_en": ["fire", "burning", "flames"],
      "keywords_banglish": ["agun", "agun legeche", "pure jacche"],
      "action": "EMERGENCY",
      "response_key": "emergency_fire"
    },
    {
      "category": "other_danger",
      "keywords_bn": ["বিপদ", "সাহায্য", "বাঁচাও"],
      "keywords_en": ["danger", "help me", "emergency"],
      "keywords_banglish": ["bipod", "sahajjo", "bachao"],
      "action": "URGENT",
      "response_key": "emergency_other"
    }
  ]
}
```

**Matching logic (pseudocode):**

```
for rule in safety_rules:
    for keyword in rule.keywords_bn + rule.keywords_en + rule.keywords_banglish:
        if keyword.lower() in user_message.lower():
            return pre_written_response(rule.response_key, detected_language)
```

- Match is case-insensitive and substring-based.
- First match wins (rules ordered by severity: EMERGENCY before URGENT).
- Pre-written responses are stored in translation files, keyed by `response_key`.
- Every emergency response shows **999** and **Tourist Police** — both marked
  **TO VERIFY** in seed data.
- Rules run BEFORE the LLM — no Gemini call, no latency, no cost.


---

## 5  Tools for Gemini Function Calling

Each tool is declared as a Gemini function-calling tool. Gemini decides
when to call them based on the user's question.

### 5.1  search_hotels

| Field | Value |
| --- | --- |
| **Name** | `search_hotels` |
| **Description (model-facing)** | "Search the verified hotel database. Filter by area, price range, and amenities. Returns hotel cards with names, prices, ratings, and locations. All data is from verified seed records." |
| **Parameters** | `{ "area": {"type": "string", "enum": ["kolatoli", "sugandha", "laboni"], "description": "Beach area"}, "max_price_bdt": {"type": "integer", "description": "Max nightly price in BDT"}, "amenities": {"type": "array", "items": {"type": "string"}, "description": "Required amenities, e.g. ['pool', 'wifi']"} }` |
| **Required params** | None (all optional — returns all hotels if no filter) |
| **Return value** | `{ "hotels": [{ "name", "area", "price_range", "amenities", "rating", "is_verified" }], "count": int }` |
| **Service called** | `hotel_service.search()` |
| **Validation** | `max_price_bdt` must be > 0 if present. `area` must be in enum. |

### 5.2  find_nearby

| Field | Value |
| --- | --- |
| **Name** | `find_nearby` |
| **Description** | "Find the nearest places by category (hospital, pharmacy, ATM, mosque, police) relative to the user's location. Returns name, distance, and coordinates." |
| **Parameters** | `{ "category": {"type": "string", "enum": ["hospital", "pharmacy", "atm", "mosque", "police"], "description": "Place category"}, "latitude": {"type": "number", "description": "User latitude"}, "longitude": {"type": "number", "description": "User longitude"}, "limit": {"type": "integer", "description": "Max results (default 5)"} }` |
| **Required params** | `category` |
| **Return value** | `{ "places": [{ "name", "category", "distance_km", "lat", "lon", "is_verified" }] }` |
| **Service called** | `nearby_service.find_nearby()` |
| **Validation** | `latitude` in [-90, 90], `longitude` in [-180, 180]. If coords missing, return all places in category without distance. |

### 5.3  calculate_fare

| Field | Value |
| --- | --- |
| **Name** | `calculate_fare` |
| **Description** | "Calculate the estimated transport fare between two locations in Cox's Bazar. Returns fare range by vehicle type (CNG auto, rickshaw, etc.) from verified route data." |
| **Parameters** | `{ "origin": {"type": "string", "description": "Starting location name"}, "destination": {"type": "string", "description": "Destination name"}, "mode": {"type": "string", "description": "Optional vehicle type / mode filter"}, "passengers": {"type": "integer", "description": "Optional passenger count; multiplies fare only when fare_basis is per_person (D22)"} }` |
| **Required params** | `origin`, `destination` |
| **Return value** | `{ "routes": [{ "vehicle_type", "fare_basis", "fare_min_bdt", "fare_max_bdt", "distance_km", "data_source", "is_verified" }], "fare_basis": "per_vehicle | per_person", "passengers": int, "calculated_min_fare_bdt": number, "calculated_max_fare_bdt": number, "note": "string" }` |
| **Service called** | `transport_service.calculate_fare()` |
| **Validation** | Origin and destination must not be empty strings. Fuzzy match against known route endpoints. If `passengers` is provided, must be ≥ 1. Per D22, `passengers` multiplies the fare only when `fare_basis` is `per_person`. |

### 5.4  get_beach_status

| Field | Value |
| --- | --- |
| **Name** | `get_beach_status` |
| **Description** | "Get the current beach safety status for Cox's Bazar. Returns the flag colour, when it was last updated, and safety advice." |
| **Parameters** | `{ "zone": {"type": "string", "enum": ["kolatoli", "sugandha", "laboni"], "description": "Optional beach zone name. If omitted, returns safety status for all three zones (D23)."} }` |
| **Required params** | None (all zones returned if omitted) |
| **Return value** | `{ "zones": [{ "zone_id": "kolatoli | sugandha | laboni", "zone_name": { "bn", "en" }, "flag_colour": "green|yellow|red", "last_updated": "ISO timestamp", "set_by": "admin", "note": "string", "is_outdated": bool }] }` |
| **Service called** | `safety_service.get_beach_status()` |
| **Validation** | If `zone` is provided, must be in enum (`kolatoli`, `sugandha`, `laboni`). If `last_updated` is older than 6 hours, set `is_outdated: true` and add "may be outdated" to note (D24). |

### 5.5  search_knowledge

| Field | Value |
| --- | --- |
| **Name** | `search_knowledge` |
| **Description** | "Search the curated knowledge base for Cox's Bazar travel information. Returns relevant text passages with sources. Use for cultural tips, local customs, travel advice, and general questions." |
| **Parameters** | `{ "query": {"type": "string", "description": "Search query in Bengali or English"} }` |
| **Required params** | `query` |
| **Return value** | `{ "chunks": [{ "text", "source", "category", "relevance_score" }] }` |
| **Service called** | `rag_service.search()` |
| **Validation** | `query` must be non-empty, ≤ 500 chars. |

---

## 6  System Prompts

### English system prompt

```
You are PothSathi (পথসাথী), a helpful, friendly, and truthful bilingual
travel assistant for Cox's Bazar, Bangladesh.

RULES:
1. Respond in the same language the user writes in (Bengali or English).
2. ONLY answer questions about Cox's Bazar tourism, travel, safety,
   hotels, transport, food, beaches, local culture, and emergencies.
3. For ANY other topic, politely say: "I can only help with Cox's Bazar
   travel information."
4. NEVER invent hotel names, phone numbers, fares, prices, or addresses.
   Use ONLY the data returned by your tools.
5. If a tool returns no results, say: "I don't have verified information
   for that. Please check with local authorities."
6. ALWAYS cite your data source (e.g., "According to our verified hotel
   data..." or "Based on our fare database...").
7. For emergencies, direct the user to call 999 (National Emergency)
   immediately. Do not attempt to provide medical or legal advice.
8. Keep responses concise — under 200 words unless the user asks for
   detail.
9. If showing prices, always note they are "indicative / sample" unless
   is_verified is true.
10. Never ask for or mention the user's name, email, or phone number.
```

### Bengali system prompt

```
তুমি পথসাথী (PothSathi), কক্সবাজারের জন্য একটি সহায়ক, বন্ধুত্বপূর্ণ এবং
সত্যনিষ্ঠ দ্বিভাষিক ভ্রমণ সহকারী।

নিয়ম:
১. ব্যবহারকারী যে ভাষায় লেখে সেই ভাষায় উত্তর দাও (বাংলা বা ইংরেজি)।
২. শুধুমাত্র কক্সবাজার ভ্রমণ, নিরাপত্তা, হোটেল, পরিবহন, খাবার, সৈকত,
   স্থানীয় সংস্কৃতি এবং জরুরি বিষয়ে উত্তর দাও।
৩. অন্য কোনো বিষয়ে ভদ্রভাবে বলো: "আমি শুধু কক্সবাজার ভ্রমণের তথ্য দিতে
   পারি।"
৪. কখনো হোটেলের নাম, ফোন নম্বর, ভাড়া, দাম বা ঠিকানা বানিয়ে বলো না।
   শুধুমাত্র তোমার টুল থেকে পাওয়া তথ্য ব্যবহার করো।
৫. টুল থেকে কোনো ফলাফল না পেলে বলো: "এই বিষয়ে আমার কাছে যাচাইকৃত তথ্য
   নেই। স্থানীয় কর্তৃপক্ষের সাথে যোগাযোগ করুন।"
৬. সবসময় তথ্যের উৎস উল্লেখ করো।
৭. জরুরি অবস্থায় ব্যবহারকারীকে অবিলম্বে ৯৯৯ (জাতীয় জরুরি সেবা) এ কল
   করতে বলো। চিকিৎসা বা আইনি পরামর্শ দেওয়ার চেষ্টা করো না।
৮. উত্তর সংক্ষিপ্ত রাখো — ২০০ শব্দের মধ্যে, যদি না ব্যবহারকারী বিস্তারিত
   চায়।
৯. দাম দেখানোর সময় সবসময় লেখো "নমুনা / আনুমানিক", যদি না is_verified সত্য
   হয়।
১০. ব্যবহারকারীর নাম, ইমেইল বা ফোন নম্বর কখনো জিজ্ঞেস করো না বা উল্লেখ
    করো না।
```

> **Note:** The system prompt is chosen based on the detected language of
> the user's message. Both prompts enforce the same rules.

---

## 7  RAG Pipeline

### Source

Curated knowledge base in Firestore collection `kb_chunks` (D7). Target:
40–60 chunks covering beach safety tips, cultural etiquette, local food
guide, transport advice, emergency procedures, and general Cox's Bazar facts.

### Chunking

- Each chunk is 100–300 words of curated text, written by the developer.
- One chunk = one topic (e.g., "Rip current safety", "Kolatoli restaurants").
- Chunks are NOT auto-split from large documents — they are hand-curated.
- Each chunk has metadata: `source`, `category`, `language`, `last_updated`.

### Embedding

- Pre-computed offline using `gemini-embedding-001` (3072 dims).
- Stored in `kb_chunks.embedding` as a list of floats.
- At startup, all embeddings are loaded into an in-memory numpy array.

### Search flow

```
1. User query → embed via LLMClient.embed() (1 Gemini API call)
2. Cosine similarity against all chunk embeddings (numpy dot product)
3. Rank by similarity score descending
4. Return top-k (k = 3)
5. Apply threshold: score ≥ 0.65
```

### Behaviour below threshold

If no chunk scores ≥ 0.65:
- Return empty chunks list to Gemini.
- Gemini will respond with "I don't have verified information for that."
- The response JSON sets `fallback_used: true`.

### Keyword fallback (if embedding call fails)

If `LLMClient.embed()` fails (quota hit, timeout):
- Fall back to simple keyword matching (case-insensitive substring search
  over chunk text).
- Return top-3 matches by keyword hit count.
- Lower quality, but ensures some result.

### Citation format

Every chunk returned to Gemini includes its `source` field. The system
prompt instructs Gemini to cite sources. Example citation in the response:
"According to our Cox's Bazar travel guide (source: beach_safety_tips)..."


---

## 8  Hotel Recommender

When a user asks for hotel suggestions (via `search_hotels` or the hotel
detail page), the recommender scores each hotel against the user's criteria.

### Scoring weights

| Factor | Weight | What it measures |
| --- | --- | --- |
| Budget fit | 30 | How close the hotel's price is to the user's budget |
| Area match | 25 | Whether the hotel is in the requested area |
| Amenity overlap | 25 | How many requested amenities the hotel has |
| Rating | 20 | Average user rating (from reviews, P1; seed rating otherwise) |

### Normalization (all scores to 0..1)

**Budget fit:**

```
If user has no budget → budget_score = 1.0  (no penalty)
If hotel_max_price ≤ user_budget:
    budget_score = 1.0 - (user_budget - hotel_max_price) / user_budget
    # closer to budget = higher score (prefers value, not cheapest)
If hotel_max_price > user_budget:
    budget_score = 0.0  (over budget = excluded)
```

**Area match:**

```
If user specified no area → area_score = 1.0
If hotel.area == requested_area → area_score = 1.0
Else → area_score = 0.0
```

**Amenity overlap:**

```
If user requested no amenities → amenity_score = 1.0
Else → amenity_score = count(matched) / count(requested)
```

**Rating:**

```
rating_score = hotel.rating / 5.0
If no rating → rating_score = 0.5  (neutral default)
```

### Final score

```
score = (budget_score × 0.30) + (area_score × 0.25) +
        (amenity_score × 0.25) + (rating_score × 0.20)
```

### Tie-breaks

If two hotels have the same score (within 0.01), sort by:
1. `is_verified` (verified first)
2. `rating` (higher first)
3. `name` (alphabetical)

### Treatment of sample data

Hotels with `is_verified: false` are included in recommendations but their
cards show a "sample / indicative" badge. The recommender does not penalize
unverified hotels in scoring — but tie-breaks favour verified ones.

### Worked EXAMPLE calculations

> All hotel data below is EXAMPLE only — not real hotels.

**User request:** budget ৳EXAMPLE_3000, area: kolatoli, amenities: [wifi, pool]

**Hotel A** — EXAMPLE_Sea_View (kolatoli, ৳EXAMPLE_2500, amenities: [wifi, pool, restaurant], rating: 4.2, verified)

```
budget_score  = 1.0 - (3000 - 2500) / 3000 = 1.0 - 0.167 = 0.833
area_score    = 1.0  (kolatoli matches)
amenity_score = 2 / 2 = 1.0  (wifi ✓, pool ✓)
rating_score  = 4.2 / 5.0 = 0.84

score = (0.833 × 0.30) + (1.0 × 0.25) + (1.0 × 0.25) + (0.84 × 0.20)
      = 0.250 + 0.250 + 0.250 + 0.168
      = 0.918
```

**Hotel B** — EXAMPLE_Beach_Inn (kolatoli, ৳EXAMPLE_1800, amenities: [wifi], rating: 3.8, verified)

```
budget_score  = 1.0 - (3000 - 1800) / 3000 = 1.0 - 0.400 = 0.600
area_score    = 1.0  (kolatoli matches)
amenity_score = 1 / 2 = 0.5  (wifi ✓, pool ✗)
rating_score  = 3.8 / 5.0 = 0.76

score = (0.600 × 0.30) + (1.0 × 0.25) + (0.5 × 0.25) + (0.76 × 0.20)
      = 0.180 + 0.250 + 0.125 + 0.152
      = 0.707
```

**Hotel C** — EXAMPLE_Grand_Resort (sugandha, ৳EXAMPLE_2800, amenities: [wifi, pool, gym], rating: 4.5, unverified)

```
budget_score  = 1.0 - (3000 - 2800) / 3000 = 1.0 - 0.067 = 0.933
area_score    = 0.0  (sugandha ≠ kolatoli)
amenity_score = 2 / 2 = 1.0  (wifi ✓, pool ✓)
rating_score  = 4.5 / 5.0 = 0.90

score = (0.933 × 0.30) + (0.0 × 0.25) + (1.0 × 0.25) + (0.90 × 0.20)
      = 0.280 + 0.000 + 0.250 + 0.180
      = 0.710
```

**Result:** Hotel A (0.918) > Hotel C (0.710) > Hotel B (0.707).
Hotel C and B differ by 0.003 — within the 0.01 tie-break threshold.
Tie-break rule 1: `is_verified` → Hotel B is verified, Hotel C is not →
**Hotel B ranks above Hotel C**.

**Final order:** Hotel A → Hotel B → Hotel C.

---

## 9  Review Sentiment Analyzer (P1)

A lightweight rule-based sentiment analyzer for hotel reviews. No ML model
— uses lexicon matching with negation handling.

### Lexicons

Two dictionaries: `lexicon_bn.json` and `lexicon_en.json`.

**English lexicon (EXAMPLE entries):**

```json
{
  "positive": ["clean", "friendly", "spacious", "great", "excellent",
               "comfortable", "beautiful", "quiet", "helpful", "fresh"],
  "negative": ["dirty", "noisy", "rude", "small", "broken",
               "expensive", "smelly", "slow", "crowded", "old"]
}
```

**Bengali lexicon (EXAMPLE entries):**

```json
{
  "positive": ["পরিষ্কার", "বড়", "সুন্দর", "ভালো", "চমৎকার",
               "আরামদায়ক", "শান্ত", "সহায়ক", "তাজা", "দারুণ"],
  "negative": ["নোংরা", "ছোট", "খারাপ", "ভাঙা", "দামি",
               "গন্ধ", "ধীর", "ভিড়", "পুরনো", "কোলাহলপূর্ণ"]
}
```

### Negation handling

Negation words flip the polarity of the next sentiment word.

- English negation: "not", "no", "never", "don't", "doesn't", "wasn't", "isn't"
- Bengali negation: "না", "নয়", "নেই", "নি"

```
"room was not clean" → "clean" is positive, negated → counts as negative
"ঘর পরিষ্কার না" → "পরিষ্কার" is positive, "না" negates → counts as negative
```

### Aspect categories

| Aspect | English keywords | Bengali keywords (EXAMPLE) |
| --- | --- | --- |
| Food | food, breakfast, meal, restaurant, eat | খাবার, নাস্তা, রেস্তোরাঁ |
| Cleanliness | clean, dirty, hygiene, tidy, wash | পরিষ্কার, নোংরা, স্বাস্থ্যকর |
| Location | location, near, far, beach, view, walk | অবস্থান, কাছে, দূরে, বীচ |
| Service | staff, service, helpful, rude, reception | সেবা, স্টাফ, সহায়ক, অভ্যর্থনা |
| Price | price, cheap, expensive, value, cost | দাম, সস্তা, দামি, মূল্য |

### Algorithm (pseudocode)

```python
def analyze_review(text: str, language: str) -> SentimentResult:
    lexicon = load_lexicon(language)
    negation_words = load_negation_words(language)
    words = tokenize(text)  # simple whitespace + punctuation split

    aspect_scores = {aspect: {"pos": 0, "neg": 0} for aspect in ASPECTS}
    overall_pos, overall_neg = 0, 0
    negated = False

    for word in words:
        if word.lower() in negation_words:
            negated = True
            continue

        sentiment = None
        if word.lower() in lexicon["positive"]:
            sentiment = "negative" if negated else "positive"
        elif word.lower() in lexicon["negative"]:
            sentiment = "positive" if negated else "negative"

        if sentiment:
            # Find which aspect this word belongs to
            aspect = detect_aspect(word, language)
            if aspect:
                aspect_scores[aspect][sentiment[:3]] += 1
            if sentiment == "positive":
                overall_pos += 1
            else:
                overall_neg += 1
            negated = False  # reset after one sentiment word

    overall = "positive" if overall_pos > overall_neg else \
              "negative" if overall_neg > overall_pos else "neutral"

    return SentimentResult(
        overall=overall,
        confidence=abs(overall_pos - overall_neg) / max(overall_pos + overall_neg, 1),
        aspects=aspect_scores
    )
```

### Output schema

```json
{
  "overall": "positive",
  "confidence": 0.72,
  "aspects": {
    "Food": { "positive": 2, "negative": 0, "sentiment": "positive" },
    "Cleanliness": { "positive": 1, "negative": 1, "sentiment": "neutral" },
    "Location": { "positive": 1, "negative": 0, "sentiment": "positive" },
    "Service": { "positive": 0, "negative": 1, "sentiment": "negative" },
    "Price": { "positive": 0, "negative": 0, "sentiment": "neutral" }
  }
}
```

---

## 10  Guardrails

| Guardrail | Implementation | When |
| --- | --- | --- |
| **Prompt injection** | Strip markdown code fences, "ignore previous", "you are now", system-override patterns from user input. If detected, return a polite refusal. | Before LLM call |
| **Input length** | Reject messages > 2 000 chars with `INPUT_TOO_LONG` error. | Before LLM call |
| **Personal data** | Regex scan for email (`*@*.*`), phone (digits ≥ 8), and common PII patterns. Strip before sending to Gemini. Log warning (without the PII). | Before LLM call |
| **Off-topic** | System prompt restricts to Cox's Bazar travel topics. If Gemini detects off-topic, it responds with a redirect message. | In system prompt |
| **Claims without source** | System prompt requires every factual claim to cite a tool result. If a tool returned no data, Gemini says "I don't have verified information." | In system prompt |

### Prompt injection detection (pseudocode)

```python
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"you\s+are\s+now",
    r"system\s*:\s*",
    r"```\s*system",
    r"new\s+instructions?\s*:",
    r"override\s+(your\s+)?rules",
]

def check_injection(text: str) -> bool:
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False
```

---

## 11  Fallback Matrix

| Condition | Primary path | Fallback 1 | Fallback 2 | Fallback 3 |
| --- | --- | --- | --- | --- |
| Normal operation | Gemini + tools → answer | — | — | — |
| Gemini 429 (quota) | — | Keyword intent → Service call | RAG search | "AI is resting" |
| Gemini 503 (down) | — | Keyword intent → Service call | RAG search | "AI is resting" |
| Gemini timeout | — | Keyword intent → Service call | RAG search | "AI is resting" |
| Embedding call fails | Gemini chat works | — | Keyword match over chunks | — |
| Firestore down | — | — | — | Tier 0 static data |
| All tools fail | Gemini answers from KB context only | RAG search | "AI is resting" | — |
| Safety rule match | Pre-written response (no LLM) | — | — | — |
| Rate limit hit | 429 response | — | Tier 0/1 pages | — |

---

## 12  Response JSON Schema

Every chat response from `POST /api/v1/chat/messages` returns this shape:

```json
{
  "answer_text": "string — the assistant's response in bn or en",
  "language": "bn | en",
  "cards": [
    {
      "type": "hotel | place | fare | beach_status",
      "data": { "...structured data from the tool..." }
    }
  ],
  "sources": [
    {
      "label": "Verified hotel data",
      "source_id": "hotels/EXAMPLE_ID",
      "is_verified": true
    }
  ],
  "severity": "info | warning | error | null",
  "tool_calls_used": ["search_hotels", "find_nearby"],
  "fallback_used": false,
  "safety_triggered": false,
  "is_ai_resting": false
}
```

| Field | Type | Description |
| --- | --- | --- |
| `answer_text` | string | The response text, in the user's language |
| `language` | `"bn"` or `"en"` | Detected / response language |
| `cards` | array | Structured data cards for UI rendering (may be empty) |
| `sources` | array | Data sources cited in the answer |
| `severity` | string or null | `null` for normal, `"warning"` for degraded, `"error"` for failures |
| `tool_calls_used` | string[] | Which tools Gemini called (for logging/eval) |
| `fallback_used` | bool | `true` if the answer came from the fallback chain |
| `safety_triggered` | bool | `true` if the safety rule engine handled this |
| `is_ai_resting` | bool | `true` if AI quota is exhausted |

---

## 13  Evaluation Plan Pointer

The full evaluation plan — 50 test prompts, accuracy metrics, hallucination
rate comparison, SUS questionnaire, and gap analysis vs. Google Maps and
TripAdvisor — will live in **[docs/evaluation-and-report.md](evaluation-and-report.md)**.

That document will cover:
- Test prompt design (25 bn + 25 en, across all tool categories and edge cases).
- Comparison: plain Gemini vs. Gemini + rules + tools + RAG.
- Emergency rule accuracy measurement.
- Usability test protocol (10–15 users, SUS).
- Gap analysis methodology.
- Architecture and sequence diagrams for the final report.

---

## Open Questions

1. **Gemini function-calling format:** The exact JSON schema format for
   tool declarations depends on the Gemini SDK version. Verify against
   `google-generativeai` Python SDK docs when implementing.
2. **Banglish keyword coverage:** The safety rules include Banglish
   keywords (Romanized Bengali), but Banglish has no standard spelling.
   The keyword list needs extensive testing with real user input. Marked
   REVIEW in the safety_rules.json structure.
3. **Sentiment lexicon size:** The EXAMPLE lexicons above are minimal
   (10 words each). A production lexicon needs 50–100+ words per
   language, plus domain-specific tourism vocabulary. This is a manual
   curation task.
4. **System prompt token count:** The full system prompt (§6) should be
   measured against the token budget. If it exceeds ~500 tokens, consider
   shortening.
5. **Embedding dimension:** `gemini-embedding-001` outputs 3072 dims.
   If a newer model (e.g. `gemini-embedding-2`) is used, dimension may
   differ. The in-memory index must handle this dynamically or via config.

---

*End of ai-spec. ~350 lines.*
