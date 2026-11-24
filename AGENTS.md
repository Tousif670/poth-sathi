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
