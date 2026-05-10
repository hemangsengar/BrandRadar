# Hemang's 4-Hour Anakin.io Hackathon Game Plan: Win 1st Place

**Status:** Strategic playbook for the Anakin.io Mini-Hackathon, Bengaluru, 10 May 2026, 11:30am–3:30pm IST.

---

## TL;DR

- **Build "BrandRadar" — a Sponsorship Sniper for sub-50K Indian YouTube/Instagram creators.** Paste your channel URL, and in ~60 seconds get back 15–25 brands actively sponsoring creators in your exact niche, with founder/marketing contact emails and a personalised cold pitch. This is creator-economy infrastructure, not a chatbot. Hemang's 17K YouTube channel + Raycreatess + behavioural psych background makes him the only person in the room who can pitch this credibly.
- **Anakin sits in the deep critical path:** Agentic Search to find recent sponsored videos in the niche → URL Scraper with `generateJson:true` to extract sponsor names from descriptions and pinned comments → Browser Sessions / `useBrowser:true` to crack JS-heavy creator directories and brand contact pages that block normal scraping → Search API to enrich each brand with its founder's email and recent funding signal. A generic LLM call cannot do any of this; the entire value chain is web-data acquisition.
- **The 30-second demo wow:** Hemang pastes his own youtube.com/@hemang URL on stage. A real, live progress bar streams: *"finding similar creators…", "scanning 47 sponsored videos…", "enriching 23 brands…"*. Out pops a cards-grid of 23 real Indian D2C brands (Boult, Wakefit, Atomberg, etc.) with founder emails, sponsorship recency, and a paste-ready cold opener referencing the brand's last campaign. Then he says: *"This is my channel. These are deals I should have closed last quarter. Stranger, paste your channel."* — and invites a judge to do it live.

---

## Part 1: Deep Anakin.io API Analysis

### 1.1 What Anakin.io actually is (not to be confused with anakin.ai)

Two distinct products share the "Anakin" name; only one is in scope:
- **anakin.io** (this hackathon's sponsor) — a YC-backed, ISO 27001/SOC 2 certified web-scraping + agentic-search REST API at `https://api.anakin.io/v1`. Developer-first. The pitch deck products in your brief all live here.
- anakin.ai — an unrelated no-code AI app builder. Ignore it.

The parent company anakin.company is a B2B competitive-pricing intelligence platform for e-commerce; anakin.io is the developer-facing API born out of that infrastructure. That heritage matters: **the strongest narratives for judges will be ones that look like "indie/creator version of what Anakin's enterprise customers already do."**

### 1.2 Endpoint inventory (verified from Anakin's docs, CLI, PHP SDK and OSS repo)

Base URL: `https://api.anakin.io/v1`. Auth: `Authorization: Bearer ak-…`. The public docs explicitly list the following product navigation: URL Scraper → Submit Scrape Job, Batch URL Scraping, Get Job Status; Web Scraper → Run Scraper, Get Result; Search API → Search; Agentic Search → Submit Search, Get Results; Reference → Polling Jobs, Error Responses, Browser Sessions.

**a) URL Scraper** (`POST /v1/scrape`, polling-based)
- Input shape (confirmed by docs and SDK): `{ url, format: "markdown" | "html" | "json", useBrowser: bool, generateJson: bool, country: "us" | "in" | …, sessionId?: string, timeout? }`.
- Returns clean markdown by default; with `generateJson: true` it produces an AI-extracted structured JSON of the page (the OSS repo notes "generatedJson is only present when generateJson: true and GEMINI_API_KEY is configured" — i.e., on the hosted side a Gemini-backed extractor runs server-side).
- Three handler chain server-side: HTTP fetch (~200ms) → Camoufox anti-detect Firefox via Playwright → fallback API. This is why "zero blocks across 207 countries" is realistic.
- 30× caching on repeat URLs. **Important quirk:** because of the cache, demoing the same URL twice will be unrealistically fast — *show a fresh URL during demo* to display real latency honestly, then a cached one to show the speed.

**b) Batch URL Scraper** (`POST /v1/scrape/batch`)
- Submit up to N URLs in one job; poll for results. Saves coordination code in 4-hour builds.

**c) Web Scraper** (`POST /v1/web-scraper/run`)
- "Custom high-throughput scrapers for structured data extraction." This is the productised version of Anakin's pricing-intel infrastructure — repeatable structured datasets across many similar pages (e.g., 1000 product pages of the same retailer).

**d) Search API** (`POST /v1/search`, synchronous)
- "AI-powered web search with citations." Returns ranked results plus extracted page content (not just titles — confirmed in their differentiation notes vs Tavily). This single capability is what most hackers will under-use; it replaces Tavily + Exa in one call.

**e) Agentic Search** (`POST /v1/agentic-search` + `GET /v1/agentic-search/{id}`)
- "Multi-stage automated research pipeline." 1–5 minute deep-research job. Runs multiple search rounds, scrapes top sources, synthesises with citations. The CLI exposes this as `anakin research "..."`.
- This is the most demo-worthy underused product. Most submissions will use only the basic scraper.

**f) Browser Sessions** (Reference doc + `--session-id` CLI flag)
- "Persistent login state allows scraping of account-gated or paywalled content after authentication is configured through the dashboard." You configure a session in the dashboard once (login to LinkedIn / Reddit / Notion / wherever), then pass `sessionId` on every scrape to act as the logged-in user. **This is the killer differentiator vs Firecrawl basic scraping.**

**g) Wire** (alpha; mentioned in PHP SDK as "Wire actions")
- The official PHP SDK and the v0.1.x announcement note "scrape, crawl, search, and Wire actions." Wire appears to be Anakin's named primitive for sequenced browser interactions (click/fill/scrape on a single session — analogous to Browserbase Stagehand or browser-use's Action API). Treat it as alpha; don't put it on the demo critical path unless you've validated it before 11:30am, but you can mention it in the README as a future enhancement.

**h) Crawl**
- Full-site crawling (linked pages within a domain). Useful but less interesting for a 4-hour demo than agentic search.

### 1.3 Pricing, credits, rate-limits, quirks

- Free tier exists with no card required ("Get started, no card required" on /pricing). Paid plans add monthly credits and discount per-credit top-ups; "credits never expire."
- The PHP SDK explicitly enumerates exception types you must handle: `AuthenticationException`, `InsufficientCreditsException`, `RateLimitException` (with `retryAfter` seconds), `JobFailedException`. Retries on 429/5xx are SDK-handled with capped exponential backoff.
- SDK is **alpha (v0.1.x); public API may change between minor versions until v1.0.** Pin versions in `requirements.txt`. Treat any non-documented field as unstable.
- Default async-job pattern: submit → poll. If you want the SDK to hide this, the official SDKs poll internally and return the final result synchronously, with `poll_timeout: 300s`, `poll_interval: 1.0s` initial, `poll_max_interval: 10.0s`. **Replicate this behaviour in your FastAPI client wrapper.**
- Important shell footgun: always quote URLs containing `?`, `&`, `#`. Won't matter inside Python but will bite you during the live CLI demo if you go that route.
- There is an unofficial Vercel adapter repo at `Anakin-Inc/anakinio-vercel` and an n8n node at `anakin-n8n` — useful proof-points for the README but not needed for the build.

### 1.4 Differentiation vs the field

| Feature | Anakin.io | Firecrawl | Browserbase | Exa | Tavily |
|---|---|---|---|---|---|
| Markdown scrape | ✅ | ✅ | partial | ❌ | ❌ |
| AI structured JSON of page | ✅ `generateJson` | ✅ extract | ❌ | ❌ | ❌ |
| Authenticated browser sessions | ✅ persistent dashboard config | sandbox-style | ✅ core product | ❌ | ❌ |
| Agentic deep research | ✅ | ✅ agent | ❌ | partial | ✅ basic |
| Country-routed proxies (207) | ✅ | partial | partial | ❌ | ❌ |
| Anti-detect (Camoufox/Firefox) | ✅ | Chromium | Chromium | ❌ | ❌ |
| Synchronous AI search w/ extracted body | ✅ | ✅ | ❌ | ✅ snippets | ✅ snippets |

**The unique combination Anakin offers** is *(authenticated session) × (country-routed anti-detect rendering) × (agentic multi-stage research) × (AI-structured JSON)* — all in one API. Most hackathon teams will use only the markdown scraper.

### 1.5 What's underutilised — the "judge whisper" capabilities

Most submissions will be `POST /scrape → markdown → LLM → answer`. To make the Anakin team and the judges sit forward, use at least three of these in the same project:

1. **Browser Sessions with a real authenticated source** (LinkedIn, Reddit logged-in, Instagram). Configure once in the dashboard pre-event.
2. **`generateJson:true` with a custom Pydantic-style schema** showing structured extraction beats string-parsing.
3. **Agentic Search as the "research" first step**, feeding URLs into URL Scraper as the "harvest" step — show the multi-stage pipeline.
4. **`country: "in"` parameter** for India-specific content (geo-targeted prices, availability). No other sponsor can do this as cleanly.
5. **Caching for the "demo it twice" trick** — first call ~3s, second call <300ms. Judges feel the speed.

If a project demonstrates 3+ of these, it's signalling to the Anakin founders that the builder *read past the homepage*. That alone will move them up in the prize ranking.

### 1.6 Showcase examples and prior art to learn from

The closest first-party blueprint is the launch post for Anakin's eCommerce Product Extractor (YC Launch): "extracts data from any eCommerce product page into JSON, fully automatically." Their parent product, anakin.company, sells competitor pricing tracking to the world's largest grocery, food-delivery and rideshare players, increasing revenue 12%. Anything that tastes like "indie creator/founder version of the enterprise pricing-intel motion" will resonate strategically with the founders Mohit Prateek and Rashmi Bala (IIT Kanpur). Their `Anakin-Inc/anakin` open-source repo, `anakinio-vercel` adapter, n8n node, Zapier and Dify plugins all point at distribution-via-integration as a North Star.

---

## Part 2: Winning Hackathon Pattern Analysis

### 2.1 What actually wins sponsor-API hackathons

Concrete recent examples worth pattern-matching against:

**Browser Brawl (1st place, YC × Browser-Use Hackathon, Feb–Mar 2025).** Mehul Kalia and team built an arena where two browser agents compete on a live website — an attacker tries to complete tasks while a defender resists. Winning insight: it's both a *demo-spectacle* (live agents fighting on screen) and a *real product* (rich training-data traces for adversarial agent eval). They built it in under a day.

**Call Me Maybe (1st, ElevenHacks #1 Firecrawl).** Scrapes SEC filings + business directories with Firecrawl → triggers an ElevenLabs voice-call to the contact. Demo wow: it actually phones the audience member while they watch. Real outcome (a phone ringing) > theoretical AI capability.

**ProoferX (2nd, E2B × Fireworks).** Crawls developer docs, runs every code example in an E2B sandbox, flags broken ones. Specific persona (DevRel teams) + specific pain (stale docs hurting trust) + dramatic before/after.

**Apollo / TARIFFED! (Microsoft AI Agents Hackathon 2025 winners).** Multi-agent orchestration with web search grounding — but always tied to a *named role* (deep research assistant for analysts; tariff lookup for supply-chain managers).

### 2.2 Common patterns of winners

1. **One specific, named persona; one specific, dollar-quantifiable pain.** Generic "AI for content creators" loses; "Indian YouTubers with 5K–50K subs leaving ₹1L/month on sponsor deals" wins.
2. **A "pause-button moment" in the demo.** Like the original Tivo demo where pressing pause on live TV instantly sold investors. You need a 5-second visual that makes a judge involuntarily say "oh, that's cool." (Browser Brawl: agents fighting. Call Me Maybe: actual ringing phone. ProoferX: red X turning to green check on a doc.)
3. **The Anakin endpoints are *load-bearing*, not bolted on.** Judges have explicitly said "Anakin must be in the critical path." If a judge can mentally remove Anakin and your project still works, you lose.
4. **Real data, not synthetic.** Five real brands the judge has heard of beats fifty fake ones.
5. **Tight 3-minute pitch arc:** problem (15s) → demo (2min) → why now / why this stack (20s) → ask (10s). Don't apologise, don't show slides about future features.

### 2.3 Common loser patterns (avoid)

- "Generic chatbot for X" — explicitly killed by Anakin's brief.
- "Scrape and summarise" with no transformation — sounds like a tutorial.
- Multi-feature dashboards where nothing is polished. (Eyal Shechtman's 5-time-winner formula: "One person builds the ugliest, most functional MVP humanly possible. Just. Make. It. Functional.")
- Building infra for an idea hackathon, or vice versa. The Maven post-mortem from a YC + OpenAI winner: "Security hackathon? Build a security tool, not infrastructure."
- Burying the demo in slides. Sabela Garcia (TechCrunch Disrupt judge): "Not showing the product is the #1 mistake. If you have built something, show it to me."
- Apologising on stage. Multiple judges flag this as a credibility-killer.
- Picking an idea where the killer feature requires anything live-internet-dependent that can't be cached. Have a recorded fallback.

---

## Part 3: Specific User + Specific Pain Ideation (12 candidates)

For each: **Persona — Pain — Magic Moment — Why Anakin specifically — Build complexity (1–10)**.

**1. BrandRadar — Sponsorship Sniper for Indian micro-creators**
- Persona: Indian YouTubers/Instagram creators with 5K–50K subs in tech/finance/lifestyle, no agent, no manager.
- Pain: They leave ₹50k–2L/month on the table because they can't see which D2C/SaaS brands are actively sponsoring creators in their exact niche, and have no founder email to pitch.
- Magic moment: Paste channel URL → 60s later, 23 brand cards with founder emails + a personalised opener referencing the brand's most recent campaign.
- Why Anakin: Agentic Search to find similar-niche channels' recent uploads → Scrape video descriptions/pinned comments with `generateJson` for sponsor mentions → Browser Sessions on LinkedIn for founder enrichment → `country:"in"` for India bias. A pure LLM call has no access to YouTube descriptions or LinkedIn behind login walls.
- Complexity: 6/10.

**2. PriceSiren — D2C Competitor Surveillance Cockpit**
- Persona: Solo Indian D2C founder running Shopify, ARR < ₹1Cr, 1–3 person team.
- Pain: Doesn't know when competitor drops price, runs offer, launches new SKU. Agencies cost ₹50K/month; he can't pay.
- Magic moment: Paste 3 competitor Shopify URLs → instant pricing diff table + currently-running discount codes + top-3 negative-review themes.
- Why Anakin: This is *literally* what anakin.company does for enterprises; his demo is "indie version of your enterprise product." Strong founder-resonance.
- Complexity: 5/10.

**3. ThreadHunter — Reddit Buyer-Intent Miner for Indie Hackers**
- Persona: Solo SaaS indie hacker with <$5K MRR, hunting first 100 customers.
- Pain: Spends 2 hrs/day scrolling Reddit looking for "is there a tool that does X" threads.
- Magic moment: Type "AI invoice tool" → 60s later, 30 ranked Reddit threads with intent-score, draft "help-first" reply (not spam), direct link.
- Why Anakin: Search API for thread discovery → Browser Sessions to access account-gated subreddits and old.reddit → `generateJson` to extract intent-score/pain-summary.
- Complexity: 5/10.

**4. CofounderDD — YC Application Battle Card Generator**
- Persona: First-time founder applying to YC W26, 14 days before deadline.
- Pain: Can't find honest competitive info; existing tools are 30 mins of manual digging per competitor.
- Magic moment: Paste your one-liner → 90s → 5 competitor battle cards (last fundraise, founders' Twitter, recent product changes, hiring signals).
- Why Anakin: Agentic Search is the whole product; without it this is impossible.
- Complexity: 6/10.

**5. GhostJobKiller — Job-Listing Reality Checker**
- Persona: Indian fresher applying to YC/Wellfound/LinkedIn jobs.
- Pain: 30%+ of listings are "ghost jobs" — never filled, just keep collecting CVs.
- Magic moment: Paste a Wellfound URL → "This role has been open 87 days, 3,400 applicants, founder's last LinkedIn post was about a hiring freeze."
- Why Anakin: Browser Sessions for LinkedIn, multi-source agentic search.
- Complexity: 6/10.

**6. RTOSentinel — Pre-shipment COD risk score for D2C**
- Persona: Indian D2C founder shipping COD orders.
- Pain: 30–40% RTO rate eats margin.
- Magic moment: Paste pin code + product URL → "67% RTO risk: this pin code historically refuses electronics > ₹3000."
- Why Anakin: Scrape Shiprocket/Delhivery RTO heatmaps, pin-code reviews, etc. Niche but very Indian.
- Complexity: 7/10 (data-source risk).

**7. CreatorMediaKitter — Auto-generated media kit from your channel**
- Persona: Same as #1 (creator).
- Pain: Don't have a media kit; can't pitch brands.
- Magic moment: Paste channel → 90s → polished PDF with audience demo, CPM benchmark, top-performing video formats.
- Why Anakin: Scrape Social Blade, similar creators, brand-deal databases.
- Complexity: 6/10. (Weaker than #1 because the wow is a PDF, not money.)

**8. RegulatoryWatch — RBI/SEBI/MCA notifier for fintech/edtech founders**
- Persona: Early-stage Indian fintech/edtech founder.
- Pain: Misses regulatory notifications until customers complain.
- Magic moment: Type "neobank for students" → ranked list of 3 RBI circulars affecting you this month.
- Why Anakin: Crawl + Search API on government sites with anti-bot.
- Complexity: 6/10.

**9. ListicleHacker — "Where can I get my indie product listed?"**
- Persona: Indie hacker with a launched product, 0–500 users.
- Pain: SEO + listicle directory submission is hellish manual work.
- Magic moment: Paste your product URL → 60s → 25 listicle/directory sites you should submit to, with submission URL + contact email + estimated DA.
- Why Anakin: Search + Scrape + extract contact info via `generateJson`.
- Complexity: 5/10.

**10. CartCloner — Reverse-engineer a competitor's funnel**
- Persona: D2C founder.
- Pain: Wants to see competitor's abandoned-cart email sequence but can't sign up + abandon manually for 30 brands.
- Magic moment: Paste competitor URL → Anakin Wire/Browser Session signs up with a burner email, abandons cart → 24 hrs later you get their full retention sequence.
- Why Anakin: Browser Sessions + Wire actions.
- Complexity: 8/10 (time-delayed, hard to demo live in 3 minutes — *risky*).

**11. AgentArena — Open-source agent eval harness for solo devs**
- Persona: Solo dev building AI agents, can't afford SteelBench/WebVoyager.
- Pain: Doesn't know if his agent actually books a meeting on a real site.
- Magic moment: Two agents racing on Calendly side-by-side on stage.
- Why Anakin: Browser Sessions as the agent runtime, Wire as the action layer.
- Complexity: 8/10. Inspired by Browser Brawl but harder solo.

**12. FundraiseMirror — "How are companies like mine actually pitching?"**
- Persona: Indian seed-stage founder.
- Pain: Can't access pitch decks / PR templates from companies in his vertical.
- Magic moment: Type "B2B SaaS, India, seed" → 10 recent fundraise PRs + extracted positioning patterns.
- Why Anakin: Agentic Search across YourStory, Inc42, Entrackr.
- Complexity: 5/10. (Too "research-paper-y" for this audience.)

---

## Part 4: Top 3 Winning Project Recommendations (ranked)

### #1 — **BrandRadar: The Sponsorship Sniper**

1. **Tagline + 1-liner.** *BrandRadar — Paste your channel URL, get 25 brands ready to sponsor you tomorrow.* For sub-50K Indian creators who don't have an agent.

2. **Persona (narrow).** Tech/finance/lifestyle creators on YouTube India with 5K–50K subscribers, posting weekly, no manager, no media-kit, no inbound brand emails yet. Roughly 3–4 lakh creators in India fit this exactly.

3. **Pain + dollar value.** They're leaving ₹50,000–2,00,000/month in sponsorship money on the table because (a) they don't know which D2C/SaaS brands are *currently* paying creators in their niche, and (b) even if they did, they can't find the brand-marketing/founder email. A first sponsorship deal is worth ₹15k–50k for a 10K-sub creator; the *information gap*, not skill gap, is the wall.

4. **The 30-second magic moment.** Hemang opens the live deployed app, pastes `youtube.com/@hemang` (his real 17K-sub behavioural-psych channel). A streaming progress bar narrates: *finding 28 similar creators → scanning 47 sponsored videos in last 90 days → enriching 23 brands → drafting openers*. A grid of 23 brand cards renders. Each card: brand logo, "last sponsored @CreatorX 11 days ago" recency tag, founder's name + email, and a one-paragraph cold opener that references the brand's most recent campaign. He hovers one card, clicks **Copy email** — then says, *"This is a deal I should have closed last month. Stranger, paste your channel"* and turns the laptop to a judge.

5. **Why this beats the field.** (a) It's the only project in the room where a judge can run the demo on themselves and get a *useful business outcome in 60 seconds*. (b) Hemang has unusual founder/persona authority — he runs the channel and the digital-products brand the persona aspires to. Most competitors will be 21-year-old engineers pitching about industries they don't operate in. (c) Anakin is fundamentally load-bearing: scraping YouTube descriptions, finding brand contacts behind LinkedIn login, geo-targeting India, and the Agentic Search pipeline can't be replicated by an OpenAI call. (d) The TAM ("every micro-creator in India") and willingness-to-pay ("first deal pays for the tool 100×") survives any judge follow-up question.

6. **Architecture sketch.**
```
[Next.js single-page UI on Vercel]
        │  POST /api/find-brands {channelUrl}
        ▼
[FastAPI backend on Vercel functions]
        │
        ├─► Anakin Agentic Search   → "Sponsored videos by creators similar to {channelUrl}, last 90 days, India"
        │       returns ranked list of YouTube video URLs + creator URLs
        │
        ├─► Anakin Batch URL Scraper (useBrowser=true, generateJson=true, country="in")
        │       extracts: { sponsor_brand, sponsor_disclosure, creator_handle, posted_date }
        │       schema-driven JSON via generateJson
        │
        ├─► For each unique brand:
        │     Anakin Search API ("{brand} founder OR head of marketing email site:linkedin.com")
        │     Anakin URL Scraper with sessionId=LINKEDIN_SESSION (Browser Sessions)
        │       → resolved contact + role
        │
        ├─► OpenAI/Claude via LangChain
        │       prompt = creator_context + brand_context + last_campaign
        │       → personalised opener (Hemang's behavioural-psych voice, no em-dashes)
        │
        ├─► ChromaDB (local) caches brand-info so repeat demos are <1s
        │
        └─► Returns BrandCard[] → front-end grid
```

7. **Hour-by-hour build plan (11:30–15:30 IST).**

| Time | Milestone | Concrete output |
|---|---|---|
| 11:30–11:50 | Pre-flight | Repo created, `requirements.txt` with `fastapi anakin-cli openai langchain chromadb python-dotenv pydantic`. `vercel.json` for Python runtime. `.env` with `ANAKIN_API_KEY`. Auth-tested LinkedIn Browser Session in the Anakin dashboard *before this morning if possible* — this is the one thing you cannot afford to debug live. |
| 11:50–12:30 | Core extractor | `extract_sponsors_from_video(url)` using URL Scraper with `generateJson` + Pydantic schema `{sponsor_brand, disclosure_text, posted_date, creator}`. Test on 3 known sponsored videos. |
| 12:30–13:00 | Discovery layer | Wrap Agentic Search with a polling helper that mimics the SDK pattern (poll_interval 1.0, max 10s, timeout 120s). Cache results in `chromadb/`. Return 20–40 video URLs from a single `channelUrl` input. |
| 13:00–13:30 | Brand enrichment | Fan-out to per-brand `enrich_brand(name)` using Search API + Browser-Session-authenticated LinkedIn scrape. Validate emails are real-format with simple regex. |
| 13:30–13:50 | Opener generator | LLM prompt template; explicit "no em-dashes, no listicle" instruction; few-shot with 2 of Hemang's own LinkedIn posts as voice samples. |
| 13:50–14:30 | Frontend | Next.js page: input box + streaming progress (SSE from FastAPI) + brand-card grid with `Copy email` and `Copy opener` buttons. Use `shadcn/ui` for instant polish. |
| 14:30–14:50 | Deploy | Push to GitHub (public). `vercel --prod`. Smoke-test live URL on phone hotspot to prove no localhost fakery. |
| 14:50–15:10 | Demo prep | Pre-warm cache by running on Hemang's real channel URL twice (30× faster on second run = the speed flex). Pre-prep one *fresh* judge-friendly URL (e.g., `youtube.com/@AnakinIO` if they have one, else a popular Indian tech channel) so the live judge demo isn't cold. Record 90-second backup video in case wifi dies. |
| 15:10–15:25 | Submission package | LinkedIn post, X post, README polish, project description form. Submit at 15:25 — 5 minutes before close. |
| 15:25–15:30 | Buffer | Sit on hands. Do not push code. |

8. **Demo script (3:00).**
   - **0:00–0:20** *Hook.* "I run a 17,000-subscriber YouTube channel on behavioural psychology. Last quarter I made zero rupees from sponsorships. Not because brands aren't paying. Because I can't find them. There are 4 lakh Indian creators with this exact problem."
   - **0:20–0:40** *Stakes.* "A first sponsorship deal for a 10K creator is ₹15,000 to ₹50,000. The wall isn't skill. It's information. Existing tools cost $200/month and ignore Indian brands."
   - **0:40–2:30** *Live demo.* Paste own channel URL on the deployed Vercel app. Narrate as the progress bar streams: agentic search → 47 sponsored videos → 23 brands → contacts. Cards render. Hover one (a brand the judges know — Boult or Wakefit). Show the founder email. Show the cold opener. Click **Copy**. *"That's a brand I should have closed last month."* **Then turn the laptop to a judge: "Paste your channel."** This is the pause-button moment.
   - **2:30–2:45** *Why Anakin specifically.* "This works because Anakin is doing four things no other API can do in one call: agentic search to discover similar creators, structured JSON extraction of sponsor disclosures, India-routed proxies, and authenticated browser sessions for the LinkedIn enrichment. I cannot build this with raw GPT."
   - **2:45–3:00** *The ask.* "It's deployed. It's open source. The first three judges to paste their channel get a free month of brand alerts. Thank you."

9. **Risk register + mitigations.**

| Risk | Probability | Mitigation |
|---|---|---|
| LinkedIn Browser Session breaks during demo (auth expired) | Medium | Pre-warm cache for the demo channel + judge channel an hour before. Have a recorded 90s video as fallback. The `useBrowser:true` + IP rotation often saves you, but don't rely on it. |
| Anakin Agentic Search > 60s | Medium | Start the agentic search in parallel with the simpler discovery (top-N similar channels via Search API) and surface partial results within 15s; the agentic enrichment fills in over the first minute. Show *streaming* output so 60s feels intentional, not slow. |
| Sponsor disclosures not in description (in voiceover instead) | Low–Medium | Fall back to scraping pinned comments + first 10 comments. If still nothing, add a heuristic: any link in description with UTM `utm_source=youtube` is treated as sponsor. |
| Wifi flake at venue | Low | Bring a phone hotspot. Have backup recording. Have one pre-cached input that returns instantly. |
| Judge picks an obscure 200-sub channel | Medium | Cap the demo to the prepared two URLs ("we recommend channels with 1000+ subs to get richer signal — try yours later via the link"). |

10. **Deployment plan (<30 min, FastAPI + Next.js on Vercel).**
    - Single repo with `/app` (Next.js) and `/api/index.py` (FastAPI ASGI entrypoint). Vercel auto-detects FastAPI when `app = FastAPI()` is at a supported entry path. No `vercel.json` needed if using the modern Python builder, but keep one for explicit `@vercel/python` mapping.
    - `requirements.txt` pinned (Anakin SDK is alpha — pin exact versions).
    - Env vars set in Vercel dashboard: `ANAKIN_API_KEY`, `OPENAI_API_KEY`, `LINKEDIN_SESSION_ID`.
    - Frontend → backend in same project (Next.js API routes proxy to FastAPI function). No CORS pain.
    - Cold-start mitigation: Vercel Fluid keeps Python warm; on demo day, hit the URL once 5 min before stage time.
    - Backup deploy on Railway with a single `Dockerfile` if Vercel's 500MB function limit bites because of `chromadb` + `langchain` weight. Test this *during* the build, not after.

---

### #2 — **PriceSiren: D2C Competitor Surveillance Cockpit**

1. **Tagline.** *PriceSiren — The pricing-intel system Anakin's enterprise customers pay $50K/year for. Indie version. ₹0/month.*
2. **Persona.** Solo Indian D2C founder, ARR < ₹1Cr, on Shopify, watching 3–5 specific competitors.
3. **Pain.** Ad-spend wasted because competitor dropped price 12% yesterday and he found out from a customer email today. ₹50K/month agency is out of reach.
4. **Magic moment.** Paste 3 competitor URLs (e.g., MyMuse, Boat, Sleepy Owl). Instant grid: pricing diff table, currently running discount codes, top-3 negative review themes, and "competitor dropped price ₹150 in last 24h" red flags.
5. **Why beats field.** This is *literally* anakin.company's enterprise pitch turned indie. Strong founder-empathy with the Anakin team. Indian D2C is hot and judges will recognise every brand in the demo.
6. **Architecture.** FastAPI + Next.js. Anakin Web Scraper (the structured-data product, not just URL Scraper) for repeat product-page extraction. `generateJson` with a `{name, price, mrp, discount, in_stock, top_review}` schema. Country `in`. Diff stored in SQLite, surfaced as "since last check" deltas. LangChain summarises review themes.
7. **Hour-by-hour.** Same shape as #1; replace YouTube discovery with structured product-page extraction.
8. **Demo.** "I run Raycreatess. I sell digital products to 800+ Indian customers. When my competitor changed price last month, I found out 6 days later. ₹38,000 in lost margin. Watch."
9. **Risk.** Schema variance across Shopify themes — mitigate by feeding 5 example pages into `generateJson` upfront and verifying.
10. **Deploy.** Same as #1.

**Why ranked #2 not #1.** Lower demo drama (a price diff table is less visceral than 23 brand-deal cards rendering). Hemang has weaker public credibility on D2C than on creator-economy.

---

### #3 — **ThreadHunter: Reddit Buyer-Intent Miner**

1. **Tagline.** *ThreadHunter — type your tool's keyword, get 30 Reddit threads where someone literally asked for it.*
2. **Persona.** Indian solo SaaS indie hacker, <$5K MRR, looking for first 100 paying customers.
3. **Pain.** Spends 2 hrs/day scrolling Reddit for "is there a tool that does X" threads. Manual, soul-crushing.
4. **Magic moment.** Type "AI invoice tool" → 30 Reddit threads, intent-score 0–100, "Help-First" reply draft (paragraph 1 validates pain, paragraph 2 offers value, paragraph 3 mentions tool), one click to copy.
5. **Why beats field.** Indie-hacker community is huge globally; demo is universally relatable; Browser Sessions on Reddit (logged-in old.reddit) is a dramatic Anakin flex.
6. **Architecture.** Anakin Search API (Reddit-scoped) → URL Scraper with logged-in `sessionId` → `generateJson` with `{question, pain_summary, urgency, asker_history_score, intent_score}` → LLM reply generator. SQLite for caching.
7. **Hour-by-hour.** Same shape; the schema is simpler, so build is faster — ~3 hours to a clean MVP, leaving 1 hour for polish and the "judge paste your keyword" magic.
8. **Demo.** "I'm a solo founder. I built ThreadHunter at 2am because I was tired of scrolling Reddit looking for people who already want my tool."
9. **Risk.** Reddit API/scraping abuse policy — frame the project as "discovery, not automation", and rate-limit gently. Browser Session does most of the heavy lifting.
10. **Deploy.** Same as #1.

**Why ranked #3.** The persona-judge match is *less* personal for Hemang than #1, and #1's emotional pull ("creator leaving money on the table") beats it for the 40% "specific user, specific pain" criterion.

---

## Part 5: The Single Best Pick — Why **BrandRadar (#1)**

**Recommended: BrandRadar.**

Justification across the four lenses you asked me to evaluate:

1. **Hemang's strengths are on the critical path.** RAG/LangChain for the opener generator, async FastAPI for the fan-out, Pydantic schemas for `generateJson`, ChromaDB for cache — all his strongest tools. The frontend is light enough that his "working knowledge" of Next.js is enough.

2. **Hemang's *biography* is the unfair advantage.** Judges don't separate the project from the pitcher. When Hemang says *"I run a 17K-subscriber channel on behavioural psychology and I personally lose ₹X every month on this exact problem,"* he becomes the *only person in the room* who is simultaneously the engineer, the user, and the buyer. No competitor can match that triangulation. His Raycreatess customer base (800+ digital-products customers, many of whom are creators) is a credible distribution channel for the "what comes after the hackathon" question that judges always ask.

3. **Demo-ability in 3 minutes is the highest of the three.** A grid of 23 brand-cards rendering on stage, with a copyable email for each, is *more visceral* than a price-diff table or a list of Reddit threads. The "turn the laptop to a judge" beat is the closest thing to a Tivo pause-moment that this idea space allows.

4. **Defensibility against judge skepticism.** The two questions that kill weak hackathon projects are *"why doesn't a generic LLM do this?"* and *"how big is this market?"*. BrandRadar has clean answers: (a) you cannot Google or GPT your way to a fresh sponsor disclosure inside a YouTube description that was published 11 days ago — the *recency* is the product; (b) the market is *every* Indian creator with 5K+ subs, ~3–4 lakh people, with an obvious ₹500/month willingness-to-pay if it lands one ₹15K deal.

The only scenario where #1 loses to #2 is if your LinkedIn Browser Session breaks live and the brand-enrichment grid is empty. Mitigate by: (i) pre-cache Hemang's channel and one judge-friendly channel before stage; (ii) the demo still works without LinkedIn (you fall back to "founder name, role, brand website") — the contact email becomes generic but the rest of the card is intact; (iii) backup video.

---

## Part 6: Submission Package Templates (for BrandRadar)

### 6.1 LinkedIn post (~250 words, no em-dashes, Hemang's voice)

> 4 hours. Solo. Coffee.
>
> I run a 17,000-subscriber YouTube channel on behavioural psychology. Last quarter I made zero rupees from brand sponsorships. Not because brands aren't paying creators. Because I genuinely could not figure out which ones were paying creators in my niche right now, and even if I could, I had no way to reach the founder.
>
> So today at the Anakin Mini-Hackathon in Bengaluru, I built BrandRadar.
>
> You paste your YouTube channel URL. In about 60 seconds it finds 25 brands that have actually sponsored creators like you in the last 90 days, pulls the founder or marketing-head contact, and drafts a cold pitch in your voice that references the brand's most recent campaign.
>
> The whole pipeline runs on Anakin.io. Their agentic search finds the similar channels. Their structured JSON extractor pulls sponsor disclosures from video descriptions. Their authenticated browser sessions get me past the LinkedIn login wall to find the right person. India-routed proxies make sure the data is local. There is no version of this that works with a generic OpenAI call. The web data layer is the entire product.
>
> Live demo at brandradar.vercel.app. Source on GitHub.
>
> If you are a creator with 5,000 to 50,000 subs and you have ever wondered which brands are spending right now in your niche, paste your channel and tell me what you find. I'm reading every reply.
>
> #anakinhackathon #buildinpublic

### 6.2 X / Twitter post (≤280 chars)

> built a thing in 4 hours
>
> paste your YouTube channel → 60s later → 25 indian brands actively sponsoring creators in your niche, with founder emails and a cold pitch in your voice
>
> built on @anakin_io agentic search + browser sessions
>
> brandradar.vercel.app

### 6.3 GitHub README skeleton

```markdown
# BrandRadar

> Paste your YouTube channel URL. Get 25 brands ready to sponsor you tomorrow.

Built in 4 hours at the Anakin.io Mini-Hackathon, Bengaluru, May 10 2026.
Solo build. No prior code.

## The problem

There are roughly 3 to 4 lakh Indian creators with 5K to 50K subscribers
and no manager. They leave ₹50K to ₹2L per month on the table because:

1. They don't know which brands are paying creators in their niche right now.
2. Even if they did, they can't find the founder or marketing-head email.

Existing tools start at $200/month and ignore Indian brands.

## The solution

Paste your channel URL. BrandRadar runs a 4-stage pipeline:

1. **Discover** — finds 20 to 40 similar creators in your niche.
2. **Harvest** — scans their last 90 days of sponsored videos.
3. **Extract** — pulls the sponsor brand from descriptions and pinned comments.
4. **Enrich** — finds the founder/marketing contact for each brand.
5. **Draft** — generates a personalised opener referencing the brand's most recent campaign.

## How Anakin.io is in the critical path

| Stage | Anakin product | Why no other API works |
|---|---|---|
| Discover similar channels | Agentic Search | Multi-stage research with citations |
| Harvest sponsored videos | Batch URL Scraper, useBrowser=true, country=in | India-routed anti-detect proxies |
| Extract sponsor disclosures | URL Scraper with generateJson=true | AI-structured JSON from any page |
| Enrich brand contact | Browser Sessions (LinkedIn) | Persistent authenticated scraping |

A generic LLM call cannot do any of this. The entire product is web-data-acquisition.

## Tech stack

- Backend: FastAPI on Vercel Python functions
- Frontend: Next.js + shadcn/ui on Vercel
- LLM: OpenAI GPT-4o for the opener generator
- Cache: ChromaDB local for repeat lookups
- Anakin SDK: anakin-cli (Python)

## Demo

[GIF placeholder — paste channel → 60 second pipeline → 23 brand cards rendering]

Live: https://brandradar.vercel.app
Demo video: [3-min YouTube link]

## Run locally

```
git clone https://github.com/hemang/brandradar
cd brandradar
pip install -r requirements.txt
cp .env.example .env  # set ANAKIN_API_KEY, OPENAI_API_KEY, LINKEDIN_SESSION_ID
uvicorn api.main:app --reload
```

## What's next

- Wire actions for automatic outreach (currently manual copy-paste)
- Instagram and X channel support
- Brand-side dashboard ("which creators should I sponsor")

## License

MIT.
```

### 6.4 Project Details paragraph (~150 words)

> BrandRadar is a sponsorship discovery tool for Indian YouTube and Instagram creators with 5,000 to 50,000 subscribers who don't have an agent. You paste your channel URL and within roughly 60 seconds it returns 20 to 25 brands actively sponsoring creators in your niche over the last 90 days, the founder or marketing-head contact for each brand, and a personalised cold pitch in your voice that references the brand's most recent campaign. Anakin.io is the entire data layer: Agentic Search discovers similar creators, the URL Scraper with generateJson extracts sponsor disclosures from video descriptions, India-routed proxies keep results local, and authenticated Browser Sessions get past LinkedIn's login wall for contact enrichment. The opener is generated by GPT-4o on top of that data. The use case is direct revenue: a typical first sponsorship deal for a 10K creator is between ₹15,000 and ₹50,000, so a single successful pitch pays for the tool a hundred times over.

---

## Part 7: Edge & Differentiation — The Last 30 Minutes (3:00–3:30 PM)

These are the "90% of submissions won't have this" details. **Pick one or two, not all.**

1. **Live "stranger try it" QR code on the demo screen.** Generate a QR pointing to `brandradar.vercel.app/?demo=true`. Show it on the slide while you pitch. Three of the audience will scan and run their own channels in real time; if one of them is a judge, you've won. (This is the "double-bonus if a stranger would too" criterion turned literal.)

2. **The benchmark slide.** A single before/after visualisation: "Manual process to find this for one creator: 3 hours. With BrandRadar: 47 seconds." Use a real stopwatch on stage to validate the second number live. This converts an opinion ("it's fast") into evidence.

3. **The Anakin-specific receipt.** A real-time API call counter in the corner of the UI: *"This run used 4 Anakin endpoints, 23 scrapes, 1 agentic search, 12 LinkedIn lookups via browser session. Total: 47 seconds."* It surfaces the depth of Anakin usage without you having to say it. Judges from Anakin will love this.

4. **The "I built this for myself" receipt.** A small line in the footer: *"Demo channel: youtube.com/@hemang — 17,142 subs. ₹0 in sponsorships last quarter. Building this so it's never zero again."* One sentence of founder-credibility worth more than three slides.

5. **Counterintuitive insight on stage.** While the live demo runs, drop a one-liner from your real data: *"Side-finding from this run: across 47 sponsored videos in Indian tech YouTube last quarter, 31 were sponsored by 3 brands. The market isn't crowded. It's concentrated. That's a feature, not a bug."* Pure information, zero ego, makes you look like an analyst not just a coder.

6. **Open the README to a "What I'd build with another 4 hours" section** that lists 5 specific Anakin Wire-action automations (auto-send the email, schedule follow-up, track open-rates). This signals you understand the entire Anakin product surface, including the alpha pieces, and have a 30-day roadmap. Founders read this as "this guy will keep building on us."

The single highest-leverage of these is **#3 (the API-call receipt overlay)** — it's small, takes 20 minutes to add, and is a love letter to the sponsor that no one else will think of.

---

## Caveats

- **The Anakin SDK is officially alpha (v0.1.x).** "Public API may change between minor versions until v1.0." Pin every version in `requirements.txt`. Don't assume a parameter that worked yesterday still works today; smoke-test the four endpoints you depend on at 11:30am sharp before you write any logic.
- **Browser Sessions need to be configured *in the Anakin dashboard before the event*.** This is the one item that will silently kill your demo if left to the last hour. Configure a LinkedIn session and one Reddit session this evening, both with throwaway accounts.
- **`generateJson` depends server-side on a Gemini key per the OSS repo.** On the hosted product this is transparent, but if their Gemini quota glitches, the structured-extraction step degrades to plain markdown. Have a regex fallback for sponsor-detection.
- **The "Wire" primitive is genuinely alpha** and only documented in the PHP SDK release notes. Don't put Wire on the demo critical path. Mention in README only.
- **"Anakin must be in critical path" is a hard, binary judging criterion.** If a judge can mentally remove Anakin and your project still works, you score 0% on participation. The architecture above has Anakin doing the discovery, harvest, extraction, *and* enrichment — four separate places — which is intentionally over-engineered for the critical-path test.
- **Two distinct "Anakin" companies with similar URLs exist** (anakin.io vs anakin.ai). Make sure every link in your README, LinkedIn post and submission form points at anakin.io. A wrong link in the README would be embarrassing.
- **Caching makes the demo *too* fast on the second run.** Counterintuitively, you want some genuine 30+ second runtime on the *first* live demo so judges feel the work happening; instant results trigger "this is fake" suspicion. Show the streaming progress UI to keep that 30 seconds visually busy.
- **Solo / 4 hours / from scratch is tight for the architecture above.** If by 13:30 the discovery layer is still flaky, *cut the Agentic Search step* and replace with a hardcoded list of 30 similar-niche channels for Hemang's specific channel; the rest of the pipeline will still demo cleanly. Ship a polished narrow thing, not a broken broad thing — that's the explicit judging criterion.
- **One unverified element:** the exact request schema for Anakin's Agentic Search and Browser Sessions endpoints isn't fully visible in public snippets; the polling pattern, parameter names, and response shape were inferred from the CLI, the PHP SDK, the Reference docs nav, and the OSS repo. Read the actual endpoint docs at anakin.io/docs/agentic-search and anakin.io/docs/browser-sessions at 11:30am sharp before committing code to those endpoints. The architecture is correct; specific field names may differ.