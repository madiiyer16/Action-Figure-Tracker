# FigureTrack

Price tracker for action figure collectors who import from Japan. Aggregates listings from AmiAmi and BigBadToyStore, calculates true landed cost (item + shipping) based on your US zip code, and tracks price history over time.

**Live demo:** _add your Vercel URL here_

---

## Features

- **Multi-retailer price comparison** — AmiAmi (Japan) and BigBadToyStore (US) in one place
- **True landed cost** — shipping calculated per Japan Post zone based on your zip code (EMS or SAL)
- **Price history chart** — see how prices have moved over time per retailer
- **Watchlist** — save figures and set a target price; get an email when the landed cost drops to your target
- **ML price prediction** — buy now vs. wait recommendation based on price trend (available after 30 days of history)
- **Automated scraping** — GitHub Actions runs the scrapers every 12 hours

---

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 16, TypeScript, Tailwind CSS v4 |
| Database | Neon PostgreSQL (serverless) |
| ORM | Prisma 6 |
| Charts | Recharts |
| Auth | Custom JWT cookie sessions (jose + bcryptjs) |
| Scrapers | Python 3.12, Playwright |
| ML service | FastAPI, scikit-learn (Render) |
| Deployment | Vercel (frontend), GitHub Actions (cron) |

---

## Local setup

### Prerequisites

- Node.js 20+
- Python 3.12+
- A [Neon](https://neon.tech) PostgreSQL database

### 1. Install dependencies

```bash
npm install
```

### 2. Configure environment variables

Copy the template and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `DATABASE_URL` | Neon PostgreSQL connection string |
| `SESSION_SECRET` | Random string for JWT signing (min 32 chars) |
| `CRON_SECRET` | Bearer token for the price-alerts cron endpoint |
| `JPY_TO_USD_RATE` | Current JPY→USD exchange rate (e.g. `0.0067`) |
| `NEXT_PUBLIC_SITE_URL` | Your app's URL (e.g. `http://localhost:3000`) |
| `ML_SERVICE_URL` | URL of the deployed ML service (optional) |
| `SMTP_HOST` | SMTP server for price alert emails (optional) |
| `SMTP_PORT` | SMTP port (e.g. `587`) |
| `SMTP_USER` | SMTP username |
| `SMTP_PASS` | SMTP password or app password |
| `SMTP_FROM` | From address (e.g. `FigureTrack <you@gmail.com>`) |

### 3. Run database migrations

```bash
npx prisma migrate deploy
npm run seed   # seeds shipping rates for zones 1–5
```

### 4. Start the dev server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## Running the scrapers

The scrapers use Playwright and require a Python virtual environment:

```bash
cd scrapers
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install --with-deps chromium
python run.py
```

Run flags: `--amiami` or `--bbts` to run a single scraper.

In production, GitHub Actions runs `python run.py` automatically every 12 hours. Set `DATABASE_URL` and `JPY_TO_USD_RATE` as repository secrets.

---

## ML service

The ML service (`ml-service/`) predicts whether a figure's price is likely to rise or fall over the next 30 days. It requires at least 30 days of price history to train.

**To train and deploy:**

```bash
cd ml-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python train.py          # trains and saves model.pkl
```

The service is deployed to Render. Set `DATABASE_URL` as an environment variable there, and set `ML_SERVICE_URL` in your Vercel environment to point to it.

---

## Price alert emails

After each scraper run, call the price-alerts endpoint to notify users whose watchlist targets have been hit:

```bash
curl -X POST https://your-app.vercel.app/api/cron/price-alerts \
  -H "Authorization: Bearer <CRON_SECRET>"
```

This is called automatically by the GitHub Actions workflow once `SITE_URL` and `CRON_SECRET` are set as repository secrets.
