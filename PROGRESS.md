# FigureTrack — Project Progress

> **How to use this file**: Read it at the start of every session to understand the current state. Update the relevant sections at the end of your session before committing. Keep entries factual — what's actually in the codebase, not what was planned.

---

## Project Vision

Action figure price tracker for collectors who import figures from Japan. The core problem: a figure listed at $60 on AmiAmi Japan might cost $95 landed after EMS shipping. A competing listing on BBTS might be $85 with free US shipping. Right now collectors calculate this manually across multiple tabs. This app does it automatically.

**Full feature set (all phases):**
1. **Price aggregator** — scrape AmiAmi and BBTS, show all prices in one place
2. **Shipping calculator** — true landed cost (price + shipping) based on user's zip code
3. **Price history chart** — line chart of price over time per retailer
4. **ML price prediction** — buy now vs wait recommendation based on price trend, days since release, restock history
5. **Price drop alerts** — email when landed cost hits user's target price
6. **Watchlist** — save figures, track them on a dashboard

---

## Rules for every Claude instance working on this project

1. **No co-author tags in commits** — commits show only the user's name, never `Co-Authored-By: Claude`
2. **Give a handoff document** when the conversation gets long (~80% context) or at each phase boundary. Must include: what was built, known issues, what comes next, and all carry-over rules. Tell the user to paste the contents of this file into the next chat.
3. **Do one phase at a time** — do not jump ahead
4. **Explain each step** before doing it
5. **Update this file** at the end of every session before committing

---

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Frontend | Next.js 16, App Router, TypeScript | `src/app/` structure |
| Styling | Tailwind CSS v4 | Uses `@import "tailwindcss"` in globals.css, no tailwind.config file |
| Charts | Recharts | Installed |
| Database | Neon PostgreSQL | Free tier, does not pause (unlike Supabase) |
| ORM | Prisma 6 | Client at `@/generated/prisma/client` (NOT `@prisma/client`) |
| Scrapers | Python 3.12, Playwright | venv at `scrapers/venv/` |
| Auth | Custom JWT sessions | Cookie-based, `src/lib/session.ts` + `src/lib/dal.ts` |
| ML service | FastAPI + scikit-learn | Not built yet — Phase 5 |
| Deployment | Vercel (frontend), Render (ML) | Not deployed yet — Phase 6 |
| Cron | GitHub Actions | Free, runs scrapers every 12h — Phase 6 |

---

## Critical Gotchas

1. **`params` and `searchParams` are Promises in Next.js 16** — always `await params` and `await searchParams` in server components and route handlers
2. **Prisma Decimal and Date aren't serializable** — convert before passing as client component props: `Number(decimal)`, `date.toISOString()`
3. **Prisma client import** is `from '@/generated/prisma/client'`, not `@prisma/client`
4. **Raw SQL column names are quoted camelCase** — `"figureId"`, `"currentPriceUsd"`, `"priceUsd"`, `"inStock"`, `"imageUrl"`, `"recordedAt"`, `"retailerUrl"`, `"lastScrapedAt"`, `"listingId"`
5. **Tailwind v4** — config is in `postcss.config.mjs`, not a `tailwind.config.js` file
6. **Always filter bad listings** — any query against `listings` must include `where: { currentPriceUsd: { lte: 5000 } }` until the scraper bug is fixed
7. **Read `node_modules/next/dist/docs/`** before writing any Next.js code — the AGENTS.md rule requires this; Next.js 16 has breaking changes from training data

---

## Database Schema

All 7 tables exist and are migrated.

- `figures` — id, name, brand, category, scale, imageUrl, originalMsrpJpy, originalMsrpUsd, createdAt
- `listings` — id, figureId, retailer, retailerUrl, currentPriceUsd, inStock, lastScrapedAt — unique on (figureId, retailer)
- `price_history` — id, listingId, priceUsd, inStock, recordedAt
- `shipping_rates` — id, originCountry, destinationZone, weightGrams, method, rateUsd
- `users` — id, email, passwordHash, zipCode, country, createdAt
- `watchlist` — id, userId, figureId, targetPriceUsd, addedAt — unique on (userId, figureId)
- `price_predictions` — id, figureId, predictionScore, recommendation, confidence, predictedAt, modelVersion

---

## DB State (as of Phase 3)

| Table | Rows | Notes |
|---|---|---|
| figures | 366 | |
| listings | 366 | 254 BBTS · 112 AmiAmi |
| price_history | 892 | 2 scrape runs (Jun 13–14 2026) |
| shipping_rates | 18 | JP→US EMS/SAL and US→US standard, zone 1 only, 300–2000g |
| users | 0 | Schema ready |
| watchlist | 0 | Schema ready |
| price_predictions | 0 | Schema ready |

---

## Phase Status

### Phase 1 — Foundation ✅ DONE
Next.js 16 + Tailwind v4 + Prisma 6 + Neon DB. All 7 tables migrated. Static homepage and figure detail page.

### Phase 2 — Scrapers ✅ DONE
- `scrapers/amiami.py` — Playwright (AmiAmi is a Nuxt SPA, plain requests get 403)
- `scrapers/bbts.py` — Playwright (BBTS also blocks plain HTTP), fresh browser context per keyword
- `scrapers/db.py` — upsert_figure, upsert_listing, record_price
- `scrapers/run.py` — runner: `scrapers/venv/bin/python scrapers/run.py`
- Run daily to accumulate price history for ML

### Phase 3 — Core UI ✅ DONE
- `src/app/api/search/route.ts` — `GET /api/search?q=&limit=`
- `src/app/api/figures/[id]/route.ts` — figure + listings + price history
- `src/app/api/shipping/route.ts` — shipping rate lookup
- `src/app/ui/SearchSection.tsx` — live search (client component)
- `src/app/ui/PriceChart.tsx` — Recharts line chart, one line per retailer
- `src/app/ui/ShippingCalculator.tsx` — price comparison + shipping calculator
- Homepage and figure detail page connected to real DB

### Phase 4 — Auth and Watchlist ✅ DONE
- `src/lib/session.ts` — JWT cookie sessions
- `src/lib/dal.ts` — `verifySession()` (redirects to login if unauthed), `getOptionalSession()` (returns null if unauthed)
- `src/lib/email.ts` — email helper for price alerts
- `src/app/actions/auth.ts` — `signup`, `login`, `logout` server actions using bcrypt
- `src/app/login/` and `src/app/signup/` — login and signup pages with forms
- `src/app/ui/LoginForm.tsx`, `SignupForm.tsx`, `WatchButton.tsx` — client form components
- `src/app/watchlist/page.tsx` — real watchlist dashboard (requires auth, shows figure + current price vs target, "At target" badge)
- `src/app/api/watchlist/[id]/route.ts` — watchlist CRUD
- `src/app/api/cron/price-alerts/` — cron endpoint that checks watchlist targets and sends emails
- `src/app/layout.tsx` — shows Sign in / Sign out in nav based on session
- `SESSION_SECRET` and `CRON_SECRET` in `.env`

**Note**: Email sending requires SMTP config in `.env` (commented out). Set up before testing price alerts.

### Phase 5 — ML Model 🔲 NOT STARTED
Needs 2–4 weeks of price history data first (start no earlier than late June 2026).

Plan:
- `ml-service/` directory — FastAPI app
- Features: days_since_release, price_vs_msrp_ratio, price_30/60/90d_change_pct, restock_count, in_stock, category/brand encoded
- Target variable: price_30d_future_change_pct
- Model: Gradient Boosting Regressor (scikit-learn)
- Endpoint: `POST /predict` → { prediction_score, recommendation, confidence }
- Deploy to Render free tier
- Wire prediction badge into figure detail page (currently hardcoded "Buy Now / 74%")

### Phase 6 — Deploy and Cron 🔲 NOT STARTED
- Deploy frontend to Vercel
- GitHub Actions cron — runs `scrapers/run.py` every 12 hours (free, no server needed)
- Deploy ML service to Render
- Fix zip→zone shipping mapping (currently all hardcoded to zone 1)
- Seed shipping rates for zones 2–8
- Write README with screenshots/demo video

---

## Key Files

```
src/
  app/
    page.tsx                  — homepage with live search
    figure/[id]/page.tsx      — detail: listings, chart, shipping calc
    watchlist/                — watchlist dashboard
    login/                    — login page
    signup/                   — signup page
    actions/                  — server actions (auth)
    ui/
      SearchSection.tsx       — search bar + results (client)
      PriceChart.tsx          — Recharts line chart (client)
      ShippingCalculator.tsx  — price comparison + shipping form (client)
    api/
      search/route.ts
      figures/[id]/route.ts
      shipping/route.ts
  lib/
    prisma.ts                 — Prisma singleton
    session.ts                — JWT session helpers
    dal.ts                    — data access layer
scrapers/
  amiami.py                   — AmiAmi Playwright scraper
  bbts.py                     — BBTS Playwright scraper
  db.py                       — shared DB write helpers
  run.py                      — runner
  venv/                       — Python venv (gitignored)
prisma/
  schema.prisma
  migrations/
.env                          — DATABASE_URL, JPY_TO_USD_RATE, SESSION_SECRET, CRON_SECRET
PROGRESS.md                   — this file
```

---

## Known Issues

### Bad price data (~69 listings)
Some listings have `currentPriceUsd > 5000` (highest ~$17M). Caused by malformed JPY strings in `jpy_to_usd()`. **Workaround**: all queries filter `{ currentPriceUsd: { lte: 5000 } }`. **Fix needed**: cap result > 2000 in `jpy_to_usd()` and run `DELETE FROM listings WHERE "currentPriceUsd" > 5000`.

### Shipping zone hardcoded to 1
All zip codes map to zone 1. Table only has zone 1 rows. Deferred to Phase 6.

### ML predictions hardcoded
"Buy Now · 74% confidence" badge is static. `price_predictions` table is empty. Fix in Phase 5.

---

## Session Housekeeping

At the end of every session:
1. Update the relevant sections of this file
2. Commit all changes (no `Co-Authored-By` line)
3. Push to GitHub
