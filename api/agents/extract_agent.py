import re
from typing import Optional, Callable

from .base import BaseAgent
from ..anakin_client import AnakinClient, _extract_text, _extract_gen_json
from ..models import SponsorMention

SPONSOR_PATTERNS = [
    r"(?:sponsored by|this video is sponsored by|in partnership with|brought to you by)\s+([A-Za-z0-9\s&.]+?)(?:\s*[\.\,\!\n])",
    r"(?:use code|promo code|discount code)\s+\w+\s+(?:for|at|on)\s+([A-Za-z0-9\s&.]+?)(?:\s*[\.\,\!\n])",
    r"(?:check out|visit)\s+([A-Za-z0-9\s&.]+?)\s+(?:using|with|via)\s+my\s+(?:link|code)",
]

UTM_DOMAIN = re.compile(r"https?://(?:www\.)?([a-zA-Z0-9-]+)\.")
UTM_LINK = re.compile(r"https?://[^\s]+utm_source=youtube[^\s]*", re.IGNORECASE)


class ExtractAgent(BaseAgent):
    def __init__(self, anakin: AnakinClient, on_update: Optional[Callable] = None):
        super().__init__("ExtractAgent", on_update)
        self.anakin = anakin

    async def execute(self, video_urls: list[str]) -> list[SponsorMention]:
        self.update(f"Extracting sponsor mentions from {len(video_urls)} videos...")
        mentions: list[SponsorMention] = []

        try:
            results = await self.anakin.batch_scrape(
                video_urls, use_browser=True, generate_json=True, country="in"
            )
            self.track_api_call("batch_scrape")

            for i, result in enumerate(results):
                url = video_urls[i] if i < len(video_urls) else ""
                mention = self._parse_result(result, url)
                if mention and mention.sponsor_brand.strip():
                    mentions.append(mention)

        except Exception as e:
            self.update(f"Batch scrape failed ({e}), using individual scrapes")
            for url in video_urls[:20]:
                try:
                    result = await self.anakin.scrape(url, use_browser=True, country="in")
                    self.track_api_call("scrape")
                    sponsor = self._regex_extract(_extract_text(result))
                    if sponsor:
                        mentions.append(SponsorMention(sponsor_brand=sponsor, video_url=url))
                except Exception:
                    continue

        self.update(f"Found {len(mentions)} sponsor mentions")
        return mentions

    def _parse_result(self, result: dict, video_url: str) -> SponsorMention | None:
        gen = _extract_gen_json(result)
        if gen.get("sponsor_brand"):
            return SponsorMention(
                sponsor_brand=str(gen["sponsor_brand"]).strip(),
                disclosure_text=gen.get("disclosure_text"),
                creator_handle=gen.get("creator_handle") or "",
                posted_date=gen.get("posted_date"),
                video_url=video_url,
            )
        sponsor = self._regex_extract(_extract_text(result))
        if sponsor:
            return SponsorMention(sponsor_brand=sponsor, video_url=video_url)
        return None

    def _regex_extract(self, text: str) -> str:
        for pattern in SPONSOR_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        utm = UTM_LINK.search(text)
        if utm:
            dm = UTM_DOMAIN.search(utm.group(0))
            if dm:
                return dm.group(1).capitalize()
        return ""
