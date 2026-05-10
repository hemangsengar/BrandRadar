# BrandRadar

**Sponsorship intelligence for Indian YouTube creators.**

Paste your YouTube channel → BrandRadar scans creators in your niche → surfaces brands actively running sponsorships → delivers contact details and a personalised pitch, ready to send.

Built at the Anakin.io hackathon, Bengaluru, May 2026.

---

## How it works

Five agents run in sequence (with parallel fan-out inside each stage):

| Stage | What happens |
|-------|--------------|
| **Discover** | Resolves your channel via `yt_channel`, then finds 8–15 similar channels via `yt_related`. Also fetches your own recent videos so past deals surface immediately. |
| **Harvest** | For each similar channel, fires 4 `yt_search` queries in parallel (`"sponsored"`, `"brand deal"`, `"collaboration"`, `"partnership"`) — filtered to that exact channel. |
| **Extract** | Fetches descriptions for up to 100 videos via `yt_video` (batches of 20). Runs 13 regex patterns + UTM/affiliate link detection + 70+ known Indian/niche brands. |
| **Enrich** | For each detected brand, searches for LinkedIn profiles and contact emails in parallel via Search API. |
| **Draft** | GPT-4o writes a personalised cold-email opener for every brand, referencing their last known creator partnership. |

All API calls go through the Anakin Wire (Holocron) task runner.

---

## Stack

- **Frontend** — Next.js 15 (App Router), Tailwind CSS v4, DM Sans / Syne / Space Mono
- **Backend** — FastAPI (Python 3.11), async throughout, in-memory job store
- **AI** — OpenAI GPT-4o for pitch drafting
- **Data** — Anakin Wire: `yt_search`, `yt_video`, `yt_channel`, `yt_related`, `search`, `scrape_linkedin`
- **Cache** — JSON file cache at `/tmp/brandradar_cache.json`, 24 h TTL + in-memory layer

---

## Local development

### Prerequisites

- Node.js 20+
- Python 3.11+
- An [Anakin.io](https://anakin.ai) API key
- An OpenAI API key

### 1. Frontend

```bash
npm install
npm run dev
# → http://localhost:3000
```

### 2. Backend

```bash
cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Create api/.env
echo "ANAKIN_API_KEY=your_key_here" >> .env
echo "OPENAI_API_KEY=your_key_here" >> .env

uvicorn main:app --reload
# → http://localhost:8000
```

Set `NEXT_PUBLIC_API_BASE=http://localhost:8000` in `.env.local` if running both locally.

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANAKIN_API_KEY` | ✅ | Anakin.io API key for Wire tasks |
| `OPENAI_API_KEY` | ✅ | Used for GPT-4o pitch drafting |
| `LINKEDIN_SESSION_ID` | optional | Enables LinkedIn profile scraping |
| `NEXT_PUBLIC_API_BASE` | frontend | Backend URL (empty = same origin) |

---

## Deployment

**Frontend → Vercel**

```bash
vercel deploy
# Set NEXT_PUBLIC_API_BASE to your backend URL in Vercel dashboard
```

**Backend → Railway / Render / Fly.io**

The API is a standard ASGI app. Expose port 8000, set env vars, run:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Rate limits

The `/api/start` endpoint is rate-limited to **5 requests per IP per 5 minutes** (in-memory, resets on restart). For production, replace with Redis-backed rate limiting.

---

## Project structure

```
.
├── api/
│   ├── agents/
│   │   ├── base.py            # BaseAgent with status tracking
│   │   ├── discovery_agent.py # Channel lookup + similar creator finding
│   │   ├── harvest_agent.py   # Multi-query brand-deal video search
│   │   ├── extract_agent.py   # Regex + pattern sponsor extraction
│   │   ├── enrich_agent.py    # LinkedIn + email enrichment
│   │   ├── draft_agent.py     # GPT-4o pitch generation
│   │   └── head_agent.py      # Orchestrator
│   ├── anakin_client.py       # Anakin Wire HTTP client
│   ├── cache.py               # JSON + in-memory cache
│   ├── models.py              # Pydantic models
│   ├── opener.py              # Pitch prompt builder
│   └── main.py                # FastAPI app + rate limiter
├── app/
│   ├── page.tsx               # Main page (hero + progress + results)
│   ├── layout.tsx             # Root layout + fonts
│   └── globals.css            # Design tokens + keyframes
└── components/
    ├── SearchInput.tsx        # Channel URL input with validation
    ├── ProgressTracker.tsx    # Live pipeline progress
    ├── BrandCard.tsx          # Brand result card with pitch accordion
    └── ApiCounter.tsx         # Debug API call counter
```
