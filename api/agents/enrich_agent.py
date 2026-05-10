import re
from typing import Optional, Callable

from .base import BaseAgent
from ..anakin_client import AnakinClient, _extract_text, _extract_gen_json
from ..models import BrandContact

LINKEDIN_PATTERN = re.compile(r"https?://(?:www\.)?linkedin\.com/in/[\w%-]+/?")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_JUNK_EXTS = (".png", ".jpg", ".jpeg")


def _first_email(text: str) -> Optional[str]:
    return next(
        (e for e in EMAIL_PATTERN.findall(text) if not e.endswith(_JUNK_EXTS)), None
    )


class EnrichAgent(BaseAgent):
    def __init__(
        self,
        anakin: AnakinClient,
        brand_name: str,
        session_id: Optional[str] = None,
        on_update: Optional[Callable] = None,
    ):
        super().__init__(f"EnrichAgent[{brand_name}]", on_update)
        self.anakin = anakin
        self.brand_name = brand_name
        self.session_id = session_id

    async def execute(self) -> BrandContact:
        self.update(f"Finding contact for {self.brand_name}...")

        sr = await self.anakin.search(
            f'"{self.brand_name}" "head of marketing" OR "founder" OR "co-founder" email India site:linkedin.com'
        )
        self.track_api_call("search")
        search_text = str(sr)

        linkedin_url = self._extract_linkedin(search_text)
        contact = await self._build_contact(search_text, linkedin_url)

        if not contact.email:
            try:
                brand_sr = await self.anakin.search(
                    f'"{self.brand_name}" contact email partnerships marketing India'
                )
                self.track_api_call("search")
                contact.email = _first_email(str(brand_sr))
            except Exception:
                pass

        return contact

    async def _build_contact(
        self, search_text: str, linkedin_url: Optional[str]
    ) -> BrandContact:
        if not (linkedin_url and self.session_id):
            return BrandContact(email=_first_email(search_text), linkedin_url=linkedin_url)
        try:
            profile = await self.anakin.scrape(
                linkedin_url, session_id=self.session_id, generate_json=True
            )
            self.track_api_call("scrape_linkedin")
            self.update(f"LinkedIn contact found for {self.brand_name}")
            return self._parse_linkedin(profile, linkedin_url)
        except Exception as e:
            self.update(f"LinkedIn scrape failed ({e}), extracting from search")
            return BrandContact(email=_first_email(search_text), linkedin_url=linkedin_url)

    def _extract_linkedin(self, text: str) -> Optional[str]:
        m = LINKEDIN_PATTERN.search(text)
        return m.group(0) if m else None

    def _parse_linkedin(self, result: dict, linkedin_url: str) -> BrandContact:
        gen = _extract_gen_json(result)
        if gen:
            return BrandContact(
                name=gen.get("name") or gen.get("full_name"),
                role=gen.get("title") or gen.get("role") or gen.get("position"),
                email=gen.get("email"),
                linkedin_url=linkedin_url,
            )
        return BrandContact(
            email=_first_email(_extract_text(result)), linkedin_url=linkedin_url
        )
