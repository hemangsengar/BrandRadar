import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Single shared client; connection pool reused across the pipeline's parallel calls.
_http = httpx.AsyncClient(
    timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=None),
    limits=httpx.Limits(max_connections=30, max_keepalive_connections=15),
)


def _extract_text(result: dict, *, agentic: bool = False) -> str:
    if agentic:
        gj = result.get("generatedJson") or {}
        return (
            gj.get("summary")
            or gj.get("answer")
            or result.get("content")
            or str(result)
        )
    return result.get("markdown") or result.get("content") or str(result)


def _extract_gen_json(result: dict) -> dict:
    gj = result.get("generatedJson") or result.get("generated_json") or {}
    # url-scraper wraps structured fields under "data"
    return gj.get("data") or gj if isinstance(gj, dict) else {}


class AnakinError(Exception):
    pass


class AnakinClient:
    BASE_URL = "https://api.anakin.io/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def scrape(
        self,
        url: str,
        use_browser: bool = False,
        generate_json: bool = False,
        country: str = "in",
        session_id: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "url": url,
            "useBrowser": use_browser,
            "generateJson": generate_json,
            "country": country,
        }
        if session_id:
            payload["sessionId"] = session_id

        resp = await _http.post(
            f"{self.BASE_URL}/url-scraper", json=payload, headers=self._headers
        )
        resp.raise_for_status()
        job = resp.json()

        job_id = job.get("jobId") or job.get("id")
        if not job_id:
            return job
        return await self._poll(f"{self.BASE_URL}/url-scraper/{job_id}", timeout=120)

    async def batch_scrape(
        self,
        urls: list[str],
        use_browser: bool = False,
        generate_json: bool = False,
        country: str = "in",
    ) -> list[dict]:
        payload: dict[str, Any] = {
            "urls": urls,
            "useBrowser": use_browser,
            "generateJson": generate_json,
            "country": country,
        }

        resp = await _http.post(
            f"{self.BASE_URL}/url-scraper/batch", json=payload, headers=self._headers
        )
        resp.raise_for_status()
        job = resp.json()

        job_id = job.get("jobId") or job.get("id")
        if not job_id:
            return job if isinstance(job, list) else []

        # Batch jobs poll at the same /url-scraper/{jobId} endpoint as single jobs
        result = await self._poll(
            f"{self.BASE_URL}/url-scraper/{job_id}", timeout=300
        )
        return result.get("results", result if isinstance(result, list) else [])

    async def wire(self, action_id: str, params: dict, timeout: int = 90) -> dict[str, Any]:
        """Execute a Wire (Holocron) pre-built action and return the result data."""
        for attempt in range(4):
            resp = await _http.post(
                f"{self.BASE_URL}/holocron/task",
                json={"action_id": action_id, "params": params},
                headers=self._headers,
            )
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", 10)) * (attempt + 1)
                await asyncio.sleep(wait)
                continue
            resp.raise_for_status()
            break
        else:
            raise AnakinError("Wire rate limit exceeded after retries")
        job = resp.json()

        job_id = job.get("job_id") or job.get("id")
        if not job_id:
            return job

        result = await self._poll(
            f"{self.BASE_URL}/holocron/jobs/{job_id}",
            timeout=timeout,
            initial_interval=2.0,
        )
        return result.get("data") or result

    async def search(self, query: str) -> dict[str, Any]:
        resp = await _http.post(
            f"{self.BASE_URL}/search",
            json={"prompt": query},
            headers=self._headers,
        )
        resp.raise_for_status()
        return resp.json()

    async def agentic_search(self, query: str, timeout: int = 300) -> dict[str, Any]:
        resp = await _http.post(
            f"{self.BASE_URL}/agentic-search",
            json={"prompt": query},
            headers=self._headers,
        )
        resp.raise_for_status()
        job = resp.json()

        # Agentic search uses snake_case job_id in response
        job_id = job.get("job_id") or job.get("id") or job.get("jobId")
        if not job_id:
            return job
        return await self._poll(
            f"{self.BASE_URL}/agentic-search/{job_id}",
            timeout=timeout,
            initial_interval=5.0,
        )

    async def _poll(
        self,
        url: str,
        timeout: int = 120,
        initial_interval: float = 1.0,
        max_interval: float = 10.0,
    ) -> dict[str, Any]:
        interval = initial_interval
        elapsed = 0.0

        while elapsed < timeout:
            resp = await _http.get(url, headers=self._headers, timeout=30.0)
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 5))
                await asyncio.sleep(retry_after)
                elapsed += retry_after
                continue

            # 202 means still processing; 200 means done (used by agentic-search)
            if resp.status_code not in (200, 202):
                resp.raise_for_status()

            data = resp.json()
            status = (data.get("status") or "").lower()

            if status in ("completed", "done", "success", "complete"):
                return data
            if status in ("failed", "error"):
                raise AnakinError(f"Job failed: {data.get('error', data)}")

            await asyncio.sleep(interval)
            elapsed += interval
            interval = min(interval * 1.5, max_interval)

        raise TimeoutError(f"Anakin job timed out after {timeout}s: {url}")
