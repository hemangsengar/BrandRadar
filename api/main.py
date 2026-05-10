import logging
import os
import time
from collections import defaultdict
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from .agents.head_agent import HeadAgent
from .anakin_client import AnakinClient
from .cache import get_cached, set_cache
from .models import BrandCard, JobStatus, StartRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="BrandRadar API")

_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

_JOBS_MAX = 200
jobs: dict[str, JobStatus] = {}

_RATE_WINDOW = 300  # 5 minutes
_RATE_LIMIT = 5     # max requests per window per IP
_rate_store: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(ip: str) -> None:
    now = time.time()
    window_start = now - _RATE_WINDOW
    timestamps = [t for t in _rate_store[ip] if t > window_start]
    _rate_store[ip] = timestamps
    if len(timestamps) >= _RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many requests. Please wait a few minutes.")
    _rate_store[ip].append(now)

_anakin_client: AnakinClient | None = None


def _get_anakin() -> AnakinClient:
    global _anakin_client
    if _anakin_client is None:
        key = os.getenv("ANAKIN_API_KEY", "")
        if not key:
            raise RuntimeError("ANAKIN_API_KEY is not set")
        _anakin_client = AnakinClient(key)
    return _anakin_client


def _evict_old_jobs() -> None:
    if len(jobs) < _JOBS_MAX:
        return
    done = [jid for jid, j in jobs.items() if j.stage in ("complete", "error")]
    for jid in done[: len(jobs) - _JOBS_MAX // 2]:
        jobs.pop(jid, None)


def _creator_profile(channel_url: str, channel_info: dict | None = None) -> dict:
    handle = channel_url.rstrip("/").split("/")[-1].lstrip("@")
    if channel_info:
        return {
            "channel_name": channel_info.get("name") or handle,
            "channel_url": channel_url,
            "niche": (channel_info.get("keywords") or "")[:120] or "content creator",
            "description": (channel_info.get("description") or "")[:200],
        }
    return {"channel_name": handle, "channel_url": channel_url, "niche": "content creator"}


@app.post("/api/start")
async def start(req: StartRequest, background_tasks: BackgroundTasks, request: Request):
    _check_rate_limit(request.client.host if request.client else "unknown")
    _evict_old_jobs()

    cached = get_cached(req.channel_url)
    if cached:
        job_id = uuid4().hex
        jobs[job_id] = JobStatus(
            job_id=job_id,
            stage="complete",
            message=f"Loaded {len(cached)} brands from cache (instant)",
            progress=100,
            brands=cached,
            api_calls={"cached": 1},
        )
        return {"job_id": job_id, "cached": True}

    job_id = uuid4().hex
    jobs[job_id] = JobStatus(
        job_id=job_id,
        stage="queued",
        message="Starting multi-agent pipeline...",
        progress=0,
    )
    background_tasks.add_task(_run, job_id, req.channel_url)
    return {"job_id": job_id, "cached": False}


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/health")
async def health():
    return {"status": "ok"}


async def _run(job_id: str, channel_url: str):
    def update_job(stage: str, message: str, progress: int, agent_reports=None, api_calls=None, **_):
        j = jobs.get(job_id)
        if not j:
            return
        j.stage = stage
        j.message = message
        j.progress = progress
        if agent_reports is not None:
            j.agent_reports = agent_reports
        if api_calls is not None:
            j.api_calls = api_calls
        logger.info(f"[{job_id[:8]}] {stage}: {message} ({progress}%)")

    try:
        head = HeadAgent(_get_anakin(), linkedin_session_id=os.getenv("LINKEDIN_SESSION_ID"))
        brands: list[BrandCard] = await head.run(
            channel_url=channel_url,
            update_job=update_job,
            creator_profile=_creator_profile(channel_url),
        )

        j = jobs[job_id]
        if brands:
            set_cache(channel_url, brands)
            j.brands = brands
            j.stage = "complete"
            j.message = f"Found {len(brands)} brands ready to sponsor you"
            j.progress = 100
        else:
            j.stage = "error"
            j.message = "No brands found. Try a channel with more recent sponsored content."
            j.progress = 0

    except Exception as e:
        logger.exception(f"Pipeline failed for job {job_id}")
        j = jobs.get(job_id)
        if j:
            j.stage = "error"
            j.message = f"Pipeline error: {e}"
            j.progress = 0
            j.error = str(e)
