import re
from typing import Optional, Callable

from .base import BaseAgent
from ..anakin_client import AnakinClient, _extract_text

VIDEO_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+"
)


class HarvestAgent(BaseAgent):
    def __init__(
        self,
        anakin: AnakinClient,
        creator_url: str,
        on_update: Optional[Callable] = None,
    ):
        handle = creator_url.rstrip("/").split("/")[-1]
        super().__init__(f"HarvestAgent[{handle}]", on_update)
        self.anakin = anakin
        self.creator_url = creator_url

    async def execute(self) -> list[str]:
        self.update(f"Scraping recent videos from {self.creator_url}...")

        try:
            result = await self.anakin.scrape(
                self.creator_url, use_browser=True, country="in"
            )
            self.track_api_call("scrape")

            content = _extract_text(result)
            video_urls = list(set(VIDEO_URL_PATTERN.findall(content)))
            self.update(f"Found {len(video_urls)} videos")
            return video_urls[:10]

        except Exception as e:
            self.update(f"Failed to harvest {self.creator_url}: {e}")
            return []
