import asyncio
from typing import Optional, Callable

from .base import BaseAgent
from ..anakin_client import AnakinClient

# Keyword → niche label mapping for yt_search supplement query
NICHE_KEYWORDS = {
    "tech", "coding", "engineering", "cybersecurity", "study", "studying",
    "motivation", "skincare", "haircare", "fitness", "finance", "travel",
    "cooking", "lifestyle", "gaming", "education", "vlog",
}


def _extract_keywords(channel_info: dict) -> list[str]:
    text = " ".join([
        channel_info.get("description") or "",
        channel_info.get("keywords") or "",
    ]).lower()
    return [kw for kw in NICHE_KEYWORDS if kw in text] or ["lifestyle"]


class DiscoveryAgent(BaseAgent):
    def __init__(self, anakin: AnakinClient, on_update: Optional[Callable] = None):
        super().__init__("DiscoveryAgent", on_update)
        self.anakin = anakin
        self.channel_info: dict = {}
        self.own_channel_id: str = ""

    async def execute(self, channel_url: str) -> list[dict]:
        handle = channel_url.rstrip("/").split("/")[-1].lstrip("@")

        # Step 1: resolve channel_id from handle
        self.update(f"Looking up @{handle}...")
        try:
            search_result = await self.anakin.wire("yt_search", {"query": handle, "limit": 10})
            self.track_api_call("agentic_search")
            items = search_result.get("data") or []
            channel_id = next((v["channel_id"] for v in items if v.get("channel_id")), None)
        except Exception:
            channel_id = None
            items = []

        if channel_id:
            self.own_channel_id = channel_id

        # Step 2: get full channel metadata
        if channel_id:
            try:
                self.channel_info = await self.anakin.wire("yt_channel", {"channel_id": channel_id})
                self.track_api_call("agentic_search")
            except Exception:
                self.channel_info = {}
        else:
            self.channel_info = {}

        # Step 3: get the creator's own recent video IDs to seed yt_related
        own_video_ids = [
            v["video_id"] for v in items
            if v.get("channel_id") == channel_id and v.get("video_id")
        ][:3]

        keywords = _extract_keywords(self.channel_info)
        self.update(f"Niche: {', '.join(keywords[:4])}. Finding similar creators via related videos...")

        # Step 4: yt_related on own videos (parallel) → similar creator videos
        related_tasks = [
            self.anakin.wire("yt_related", {"video_id": vid})
            for vid in own_video_ids
        ]
        # Step 5: niche yt_search as supplement
        niche_query = " ".join(keywords[:3]) + " Indian creator YouTube"
        related_tasks.append(self.anakin.wire("yt_search", {"query": niche_query, "limit": 15}))
        self.track_api_call("agentic_search", len(related_tasks))

        results = await asyncio.gather(*related_tasks, return_exceptions=True)

        seen_video_ids: set[str] = set()
        seen_channel_ids: set[str] = set()
        if channel_id:
            seen_channel_ids.add(channel_id)  # exclude the input channel itself

        videos: list[dict] = []
        for r in results:
            if isinstance(r, Exception):
                continue
            for item in (r.get("data") or []):
                vid = item.get("video_id")
                cid = item.get("channel_id", "")
                if vid and vid not in seen_video_ids and cid not in seen_channel_ids:
                    seen_video_ids.add(vid)
                    if cid:
                        seen_channel_ids.add(cid)
                    videos.append({
                        "video_id": vid,
                        "channel_id": cid,
                        "channel_name": item.get("channel", ""),
                        "title": item.get("title", ""),
                        "url": item.get("url", f"https://www.youtube.com/watch?v={vid}"),
                    })

        self.update(f"Found {len(videos)} videos from {len(seen_channel_ids)} similar creators")
        return videos[:60]
