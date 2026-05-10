import re
from typing import Optional, Callable

from .base import BaseAgent
from ..anakin_client import AnakinClient, _extract_text

YOUTUBE_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?youtube\.com/(?:@[\w.-]+|channel/[\w-]+|c/[\w-]+)"
)

SEED_CREATORS = [
    "https://www.youtube.com/@nitishrajput",
    "https://www.youtube.com/@beerbiceps",
    "https://www.youtube.com/@warikoo",
    "https://www.youtube.com/@mishraankit",
]


class DiscoveryAgent(BaseAgent):
    def __init__(self, anakin: AnakinClient, on_update: Optional[Callable] = None):
        super().__init__("DiscoveryAgent", on_update)
        self.anakin = anakin

    async def execute(self, channel_url: str) -> list[str]:
        self.update(f"Running agentic search for creators similar to {channel_url}...")

        try:
            query = (
                f"Indian YouTube creators similar to {channel_url} who have recent sponsored "
                f"content in tech finance lifestyle psychology niche, minimum 5000 subscribers. "
                f"List their YouTube channel URLs."
            )
            result = await self.anakin.agentic_search(query)
            self.track_api_call("agentic_search")

            content = _extract_text(result, agentic=True)
            creator_urls = list(set(YOUTUBE_URL_PATTERN.findall(content)))
            creator_urls = [u for u in creator_urls if channel_url not in u]

            self.update(f"Agentic search found {len(creator_urls)} similar creators")

            if len(creator_urls) < 3:
                self.update("Supplementing with Search API...")
                sr = await self.anakin.search(
                    f"Indian YouTube creators sponsored content 2024 2025 similar to {channel_url} site:youtube.com"
                )
                self.track_api_call("search")
                additional = YOUTUBE_URL_PATTERN.findall(str(sr))
                creator_urls = list(set(creator_urls + additional))

            if not creator_urls:
                self.update("Using seed creators as fallback")
                creator_urls = SEED_CREATORS

            return creator_urls[:15]

        except Exception as e:
            self.update(f"Agentic search failed ({e}), using Search API fallback")
            try:
                sr = await self.anakin.search(
                    f"top Indian YouTube creators {channel_url} niche sponsored content"
                )
                self.track_api_call("search")
                urls = YOUTUBE_URL_PATTERN.findall(str(sr))
                return list(set(urls))[:10] or SEED_CREATORS
            except Exception:
                return SEED_CREATORS
