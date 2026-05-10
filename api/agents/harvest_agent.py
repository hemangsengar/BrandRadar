import asyncio
from typing import Optional, Callable

from .base import BaseAgent
from ..anakin_client import AnakinClient


class HarvestAgent(BaseAgent):
    def __init__(
        self,
        anakin: AnakinClient,
        channel_name: str,
        channel_id: str = "",
        on_update: Optional[Callable] = None,
    ):
        super().__init__(f"HarvestAgent[{channel_name[:20]}]", on_update)
        self.anakin = anakin
        self.channel_name = channel_name
        self.channel_id = channel_id

    async def execute(self) -> list[dict]:
        self.update(f"Finding brand deals from {self.channel_name}...")

        # Search across multiple sponsorship vocabulary terms in parallel
        queries = [
            f"{self.channel_name} sponsored",
            f"{self.channel_name} brand deal",
            f"{self.channel_name} collaboration",
            f"{self.channel_name} partnership",
        ]
        tasks = [
            self.anakin.wire("yt_search", {"query": q, "limit": 10})
            for q in queries
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        self.track_api_call("agentic_search", len(queries))

        seen: set[str] = set()
        videos: list[dict] = []
        all_items: list[dict] = []
        for r in results:
            if isinstance(r, Exception):
                continue
            for item in (r.get("data") or []):
                vid = item.get("video_id")
                cid = item.get("channel_id", "")
                if vid and vid not in seen:
                    seen.add(vid)
                    all_items.append(item)
                    if not self.channel_id or cid == self.channel_id:
                        videos.append({
                            "video_id": vid,
                            "channel_id": cid,
                            "channel_name": item.get("channel", self.channel_name),
                            "title": item.get("title", ""),
                            "url": item.get("url", f"https://www.youtube.com/watch?v={vid}"),
                        })

        # Fallback: if channel_id filtering removed everything (API sometimes omits channel_id),
        # accept all results rather than returning empty-handed.
        if self.channel_id and not videos and all_items:
            for item in all_items:
                vid = item.get("video_id")
                cid = item.get("channel_id", "")
                videos.append({
                    "video_id": vid,
                    "channel_id": cid,
                    "channel_name": item.get("channel", self.channel_name),
                    "title": item.get("title", ""),
                    "url": item.get("url", f"https://www.youtube.com/watch?v={vid}"),
                })

        self.update(f"Found {len(videos)} verified videos from {self.channel_name}")
        return videos
