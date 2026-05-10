from typing import Optional, Callable

from .base import BaseAgent
from ..models import BrandCard, BrandContact
from ..opener import generate_opener


class DraftAgent(BaseAgent):
    def __init__(
        self,
        brand_name: str,
        contact: BrandContact,
        last_sponsored_creator: str,
        last_campaign_snippet: Optional[str],
        creator_profile: dict,
        on_update: Optional[Callable] = None,
    ):
        super().__init__(f"DraftAgent[{brand_name}]", on_update)
        self.brand_name = brand_name
        self.contact = contact
        self.last_sponsored_creator = last_sponsored_creator
        self.last_campaign_snippet = last_campaign_snippet
        self.creator_profile = creator_profile

    async def execute(
        self, source_videos: list[str], last_sponsored_days_ago: int
    ) -> BrandCard:
        self.update(f"Drafting opener for {self.brand_name}...")

        opener = await generate_opener(
            creator_profile=self.creator_profile,
            brand_name=self.brand_name,
            contact=self.contact,
            last_sponsored_creator=self.last_sponsored_creator,
            last_campaign_snippet=self.last_campaign_snippet,
        )
        self.track_api_call("openai_gpt4o")

        return BrandCard(
            brand_name=self.brand_name,
            last_sponsored_creator=self.last_sponsored_creator,
            last_sponsored_days_ago=last_sponsored_days_ago,
            contact=self.contact,
            opener=opener,
            source_videos=source_videos,
            last_campaign_snippet=self.last_campaign_snippet,
        )
