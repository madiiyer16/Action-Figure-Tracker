# FigureTrack — Project Progress

> **How to use this file**: Read it at the start of every session to understand the current state. Update the relevant sections at the end of your session before committing. Keep entries factual — what's actually in the codebase, not what was planned.

---

## Project overview

Action figure price tracker that compares total landed cost (base price + shipping) across AmiAmi and BBTS, with price history charts and a shipping calculator. ML buy/wait predictions and a watchlist with email alerts are planned.

**Stack**: Next.js 16 App Router · TypeScript · Tailwind v4 · Prisma 6 · Neon PostgreSQL · Recharts  
**Prisma client path**: `@/generated/prisma/client` (not `@prisma/client`)  
**DB singleton**: `src/lib/prisma.ts`  
**Scraper runtime**: Python venv at `scrapers/venv/`

---

## Phase status

| Phase | Status | Summary |
|-------|--------|---------|
| 1 — Foundation | ✅ Done | Next.js app, Prisma schema (7 models), Neon DB, static UI shells |
| 2 — Scrapers | ✅ Done | AmiAmi + BBTS Playwright scrapers, DB upsert logic |
| 3 — Live data | ✅ Done | API routes, search, figure detail, price chart, shipping calculator |
| 4 — Auth + Watchlist | 🔲 Next | See below |

---

## DB state (as of Phase 3)

| Table | Rows | Notes |
|-------|------|-------|
| figures | 366 | |
| listings | 366 | 254 BBTS · 112 AmiAmi |
| price_history | 892 | 2 scrape runs |
| shipping_rates | 18 | JP→US (EMS/SAL) and US→US (standard) at 300–2000g |
| users | 0 | Schema ready, no auth yet |
| watchlist | 0 | Schema ready |
| price_predictions | 0 | Schema ready |

---

## What exists

### API routes (`src/app/api/`)
- `GET /api/search?q=&limit=` — figures with cheapest in-stock listing; filters `currentPriceUsd > 5000`
- `GET /api/figures/[id]` — figure + all listings (filtered) + full price history
- `GET /api/shipping?origin=JP&zone=1&method=EMS&weight=300` — looks up `shipping_rates` table

### Pages
- `/` — async server component reads `searchParams.q` (Promise), passes to `SearchSection`
- `/figure/[id]` — async server component reads `params.id` (Promise), fetches Prisma, serializes Decimal/Date, renders `ShippingCalculator` + `PriceChart`
- `/watchlist` — static placeholder, needs auth

### Client components (`src/app/ui/`)
- `SearchSection.tsx` — search form + results list, calls `/api/search`
- `PriceChart.tsx` — Recharts `LineChart`, one line per retailer, dark-themed
- `ShippingCalculator.tsx` — zip + method form, calls `/api/shipping` per retailer, re-sorts by landed cost

### Scrapers (`scrapers/`)
- `amiami.py` — Playwright scraper for AmiAmi (Nuxt SPA, requests get 403)
- `bbts.py` — Playwright scraper for BigBadToyStore
- `db.py` — `upsert_figure`, `upsert_listing`, `record_price`
- `run.py` — runs both scrapers

---

## Known issues

### Bad price data (~69 listings)
Some listings have `currentPriceUsd > 5000` (highest is ~$17M). Caused by malformed price strings in `amiami.py → jpy_to_usd()` that return a raw large integer instead of a USD value. **Workaround already applied**: all Prisma queries and API routes filter `{ currentPriceUsd: { lte: 5000 } }`. **Root fix needed**: add a sanity cap in `jpy_to_usd()` (reject result > 2000) and re-run the scraper or run a `DELETE FROM listings WHERE "currentPriceUsd" > 5000` migration.

### Shipping zone mapping is simplified
All US zip codes map to zone 1. The `shipping_rates` table only has zone 1 rows. Expanding to real Japan Post zones (by zip prefix) is deferred.

### ML predictions hardcoded
The "Buy Now · 74% confidence" badge on the figure detail page is static. `price_predictions` table is empty.

---

## Next phase: 4 — Auth + Watchlist

### Must-have
- [ ] User auth: sign up / sign in / sign out against the `users` table (`email`, `passwordHash`, `zipCode`, `country`). Session via NextAuth or a lightweight JWT cookie.
- [ ] `POST /api/watchlist` — add figure to watchlist with optional `targetPriceUsd`
- [ ] `DELETE /api/watchlist/[id]` — remove entry
- [ ] `/watchlist` page — list user's watched figures with current price vs target, mark figures below target in green
- [ ] Wire the "Watch" button on `/figure/[id]` to the API (disabled / redirect to login if not authed)

### Should-have
- [ ] Price alert emails: after each scrape run, check `watchlist` entries where `currentPriceUsd ≤ targetPriceUsd` and send email (Resend or Nodemailer). Users table has `email`.
- [ ] Fix bad price data: cap in `jpy_to_usd()` + clean migration

### Nice-to-have
- [ ] Wire `price_predictions` table: simple heuristic (price trending up over last 3 history rows → "Buy Now", else "Wait"), write a scraper post-hook that inserts a row per figure
- [ ] Expose user's saved zip code in `ShippingCalculator` as a default

---

## Gotchas for new instances

1. **`params` and `searchParams` are Promises in Next.js 16** — always `await params` and `await searchParams` in server components and route handlers.
2. **Prisma Decimal and Date aren't serializable** — convert before passing as client component props: `Number(decimal)`, `date.toISOString()`.
3. **Prisma client import** is `from '@/generated/prisma/client'`, not the usual `@prisma/client`.
4. **Raw SQL column names are quoted camelCase** — e.g. `"figureId"`, `"currentPriceUsd"`, `"priceUsd"`. The Python scrapers use these too (see `db.py`).
5. **Tailwind v4** — uses `@import "tailwindcss"` in globals.css, not `@tailwind base/components/utilities`. Config is in `postcss.config.mjs`.
6. **Always filter bad listings** — any new query against `listings` should include `where: { currentPriceUsd: { lte: 5000 } }` until the scraper bug is fixed.
7. **Read `node_modules/next/dist/docs/` before writing Next.js code** — the AGENTS.md rule applies; Next.js 16 has breaking changes from training data.
8. **Do not add `Co-Authored-By: Claude` to commits** — omit the co-author trailer entirely. Plain commit messages only.

---

## Session housekeeping

At the end of every session:
1. Update the relevant sections of this file (DB state, phase status, known issues)
2. `git add` your changes and commit **without** a `Co-Authored-By` line
3. `git push` so GitHub stays current and the next session can read this file fresh
