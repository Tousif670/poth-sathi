# PothSathi — Risk Register & Open Questions

> Binding decisions: [decisions.md](decisions.md).  
> Architecture: [architecture.md](architecture.md).  
> Tech stack: [tech-stack.md](tech-stack.md).  
> Build plan: [build-plan.md](build-plan.md).

---

## 1 Risk Register

Mitigations point directly to specific documents or build plan slices.

### 1.1 High-Priority Risks
| # | Risk | Impact | Likelihood | Mitigation & Reference |
| --- | --- | --- | --- | --- |
| R1 | **Not enough time** (~10 coding days to 4 Dec feature freeze) | High | High | Strict vertical slices, daily working skeleton, and automated scope cut order: cut P2, voice, admin page, and reviews first ([decisions.md](decisions.md) D17, [build-plan.md](build-plan.md) §2). |
| R2 | **AI hallucinating prices or safety advice** | High | High | Safety rule engine answers emergencies without LLM ([ai-spec.md](ai-spec.md) §4). Strict grounding prompt; missing data returns "no verified info" ([ai-spec.md](ai-spec.md) §6, Slice 6). |
| R3 | **Gemini free-tier quota exhaustion & data terms** | High | Med | In-memory global daily AI counter (D15), Tier 1 RAG fallback, and "AI is resting" mode ([architecture.md](architecture.md) §6, Slice 5). Zero PII sent to Gemini ([decisions.md](decisions.md) D14). |
| R4 | **Demo-day presentation failure** (no Wi-Fi / quota hit) | High | Med | Local Firebase Emulator fallback, offline Tier 0 static JSON build, and pre-recorded 3-minute backup screencast ([decisions.md](decisions.md) D10, [build-plan.md](build-plan.md) §6). |
| R5 | **Wrong or missing real-world seed data** | High | Med | Manual field verification with `data_source` and `is_verified` tags. Unverified entries show a "Sample / Indicative" badge ([decisions.md](decisions.md) D9, [data-plan.md](data-plan.md) §4). |

### 1.2 Medium-Priority Risks
| # | Risk | Impact | Likelihood | Mitigation & Reference |
| --- | --- | --- | --- | --- |
| R6 | **Render cold start during live demo** (~50s delay) | Med | High | UptimeRobot free keep-warm ping hits `GET /api/v1/health` every 14 minutes ([architecture.md](architecture.md) §13, Slice 9). Warm up server manually 10 min before presentation. |
| R7 | **Bengali & Banglish linguistic quality** | Med | Med | System prompt mandates Bengali reply for Bengali queries ([ai-spec.md](ai-spec.md) §6). Safety rules explicitly include phonetic Banglish keywords (Slice 6). |
| R8 | **Firestore free read limit exceeded** (50k/day limit) | Med | Med | In-memory TTL caching for public collections (hotels, places, fares, beach status) drastically cuts reads ([architecture.md](architecture.md) §7, Slice 2). |
| R9 | **Prompt injection & system prompt override** | Med | Low | Pre-LLM sanitization regex strips markdown fences and override directives ([ai-spec.md](ai-spec.md) §10, Slice 5). |
| R10 | **API key or secret credential leakage** | High | Low | `.env` and service account keys git-ignored; only committed `.env.example`. Startup sanity checks block credentials in repository ([repo-structure.md](repo-structure.md) §6). |

### 1.3 Low-Priority Risks
| # | Risk | Impact | Likelihood | Mitigation & Reference |
| --- | --- | --- | --- | --- |
| R11 | **RAG memory footprint exceeds 512 MB RAM** | Med | Low | 300 chunks × 3072 floats = ~3.5 MB RAM, easily fitting inside Render free tier ([tech-stack.md](tech-stack.md) §4, Slice 7). |
| R12 | **Mock data accidentally served in production** | High | Low | Fail-loud startup: `APP_ENV=prod` exits immediately if credentials are missing or point to emulator ([decisions.md](decisions.md) D19, Slice 9). |
| R13 | **OpenStreetMap tile server blocking** | Low | Low | Set custom User-Agent and mandatory OSM attribution. Fallback to free CARTO Positron raster tiles ([tech-stack.md](tech-stack.md) §3, Slice 3). |
| R14 | **Browser Web Speech API failing on non-Chrome** | Low | High | Voice is non-critical P1. Unsupported browsers display "Use text chat" notice; core text chat always works ([decisions.md](decisions.md) D8, [architecture.md](architecture.md) §10). |

---

## 2 Open Questions

### Group 1: Must Resolve Before Building (Before 25 Nov)
1. **Gemini Free-Tier Flash RPM/RPD Quota:** Check Google AI Studio dashboard for the active free limit of `gemini-3.8-flash` or `gemini-3.8-flash-lite` to configure `DAILY_AI_LIMIT`.
2. **Harmonize Transport Naming:** Standardize router and collection naming to `transport_routes` and `/api/v1/transport/*` across all existing documentation.

### Group 2: Resolve During Phase 1 & 2 (26 Nov – 2 Dec)
1. **Banglish Keyword Coverage:** Expand Romanized Bengali variations in `safety_rules.json` (e.g. "bapao", "bachao", "dube jacchi") during tool testing.
2. **Keep-Warm Automation:** Verify whether UptimeRobot free tier or GitHub Actions scheduled curl keeps Render active without hitting monthly free hour caps (750 hours).
3. **Sentiment Lexicon Breadth:** Ensure `lexicon_bn.json` contains at least 30 verified Bengali tourism adjectives before testing review endpoints.

### Group 3: Resolve Later (Post-MVP / Commercial)
1. **Automated Chat Session TTL:** Transition from manual 30-day cleanup scripts to Firestore Native TTL policies.
2. **Tide & Marine Integration:** Verify reliable free API for Bay of Bengal tide gauge data.
3. **Hosting Migration:** Transition from Vercel Hobby and Render Free to commercial infrastructure if launched for tourists.

---

## 3 Free-Tier Limits Quick Reference

| Service & Resource | Free Tier Allowance | Source URL & Verification Status | Protection Mechanism |
| --- | --- | --- | --- |
| **Gemini API** | ~5 RPM, ~20–500 RPD (varies by model) | https://ai.google.dev/pricing (verify) | Global counter + in-memory rate limiter (Slice 5) |
| **Cloud Firestore** | 1 GiB storage, 50,000 reads/day, 20,000 writes/day | https://firebase.google.com/pricing (verify) | In-memory TTL cache on backend (Slice 2) |
| **Firebase Auth** | 50,000 Monthly Active Users (MAU) | https://firebase.google.com/pricing (verify) | Standard client SDK session caching |
| **Render Free** | 512 MB RAM, 0.1 CPU, 750 free instance-hours/mo | https://render.com/docs/free (verify) | 14-min keep-warm ping; in-memory RAG index ≤4 MB |
| **Vercel Hobby** | 100 GB bandwidth, non-commercial only | https://vercel.com/docs/limits (verify) | Strictly non-commercial university scope |
| **OpenStreetMap** | Free raster tiles with attribution | https://wiki.openstreetmap.org/wiki/Tile_usage_policy (verify) | Custom User-Agent; CARTO tiles fallback |
| **Open-Meteo** | Free marine weather for non-commercial use | https://open-meteo.com/en/docs/marine-weather-api (verify) | 1-hour cache on backend weather fetches |
| **Tides Data** | None confirmed free without key | UNVERIFIED | Excluded from MVP; static safety flags used |

---

## 4 What a Payment Card Would Unlock Later

While PothSathi is designed to run entirely on \$0 free tiers for this university project, adding a payment card later would unlock:
1. **Always-On Backend:** Render Starter instance (~$7/month, verify: https://render.com/pricing) eliminating cold starts completely.
2. **Commercial Deployment:** Vercel Pro subscription (~$20/month, verify: https://vercel.com/pricing) allowing commercial monetization.
3. **Dedicated Vector Database:** Managed Pinecone or Cloud Firestore Vector Search (~$10–30/month, verify: https://www.pinecone.io/pricing) replacing in-memory startup indexing.
4. **Custom Domain & SSL:** Branded domain (e.g. `pothsathi.com`, ~$12/year, verify: https://domains.google) replacing `*.vercel.app`.
5. **High-Volume Gemini Quota:** Pay-as-you-go Gemini API tier eliminating daily prompt caps and guaranteeing private data handling terms.
