import os
from typing import Optional

from openai import AsyncOpenAI

from .models import BrandContact

_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


SYSTEM_PROMPT = """You write cold sponsorship pitch opening paragraphs for Indian YouTube creators.

Rules:
- No em-dashes. Use commas or periods instead.
- No bullet lists or headers. One flowing paragraph only.
- Exactly 3 sentences.
- Reference the brand's most recent campaign or the creator they last sponsored.
- Voice: warm, direct, data-informed, subtly behavioural-psychology inflected.
- End with a clear, low-friction ask (a 15-minute call, not a full proposal).
- Do not mention follower counts or vanity metrics.
- Write as if you are the creator addressing the brand contact directly."""


async def generate_opener(
    creator_profile: dict,
    brand_name: str,
    contact: BrandContact,
    last_sponsored_creator: str,
    last_campaign_snippet: Optional[str],
) -> str:
    channel_name = creator_profile.get("channel_name", "my channel")
    niche = creator_profile.get("niche", "educational content")
    contact_name = contact.name or "there"
    campaign_ref = (
        f'your recent campaign "{last_campaign_snippet}"'
        if last_campaign_snippet
        else f"your recent partnership with @{last_sponsored_creator}"
    )

    user_prompt = f"""Creator: {channel_name}, {niche} niche.
Brand: {brand_name}
Last sponsored creator similar to mine: @{last_sponsored_creator}
Recent campaign: {campaign_ref}
Contact: {contact_name}, {contact.role or "marketing team"}

Write the 3-sentence cold pitch opening paragraph."""

    resp = await _get_client().chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=200,
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()
