import asyncio
import re
from typing import Optional, Callable

from .base import BaseAgent
from ..anakin_client import AnakinClient
from ..models import SponsorMention

# Compiled sponsor patterns — ordered most-reliable first.
# All use (?<!not ) negative lookbehind to avoid matching "not sponsored by".
_PATTERNS: list[re.Pattern] = [re.compile(p, re.IGNORECASE) for p in [
    # "sponsored by X" / "in partnership with X" — excludes "not sponsored by"
    r"(?<!not\s)(?<!not )(?:this video is )?(?:sponsored by|in partnership with|brought to you by)\s+([A-Za-z0-9][A-Za-z0-9\s&.]{1,40}?)(?:\s*[\.\,\!\n\(])",
    # "use code/promo X at Brand"
    r"(?:use (?:my |our )?(?:code|promo|coupon|link)|promo code|discount code)\s+\w+\s+(?:for|at|on)\s+([A-Za-z0-9][A-Za-z0-9\s&.]{1,30}?)(?:\s*[\.\,\!\n\(])",
    # "sign up / free trial to/with Brand"
    r"(?:sign up|free .{0,20}trial|free .{0,20}account)\s+(?:for|to|at|with|on)\s+([A-Za-z0-9][A-Za-z0-9\s&.]{1,30}?)(?:\s*[\.\,\!\n\(])",
    # "check out / visit Brand using/with my link"
    r"(?:check out|visit)\s+([A-Za-z0-9][A-Za-z0-9\s&.]{1,30}?)\s+(?:using|with|via)\s+my\s+(?:link|code)",
    # "supported/presented/powered by X"
    r"(?<!not\s)(?:supported|presented|powered) by\s+([A-Za-z0-9][A-Za-z0-9\s&.]{1,40}?)(?:\s*[\.\,\!\n\(])",
    # "#ad" or "#sponsored" tag followed by brand name
    r"#(?:ad|sponsored|collab)\b[^\n]*?([A-Z][A-Za-z0-9]{2,25})(?:\s*[\.\,\!\n])",
    # Hindi: "Brand ne sponsor kiya"
    r"([A-Za-z0-9][A-Za-z0-9\s&.]{1,30}?)\s+(?:ne )?sponsor kiya",
    # "thanks to / special thanks to / shoutout to Brand"
    r"(?:special )?thanks?\s+(?:to|for(?:\s+sponsoring)?)\s+([A-Za-z0-9][A-Za-z0-9\s&.]{1,35}?)(?:\s*[\.\,\!\n\(])",
    # "in collaboration with Brand" / "collab with Brand"
    r"(?:in\s+)?collab(?:oration)?\s+with\s+([A-Za-z0-9][A-Za-z0-9\s&.]{1,35}?)(?:\s*[\.\,\!\n\(])",
    # "created/made/built in association/partnership with Brand"
    r"(?:created|made|built|designed)(?:\s+in)?\s+(?:association|partnership)\s+with\s+([A-Za-z0-9][A-Za-z0-9\s&.]{1,35}?)(?:\s*[\.\,\!\n\(])",
    # "made possible by Brand" / "made this possible with Brand"
    r"(?:made possible|made this possible)\s+(?:by|with|through)\s+([A-Za-z0-9][A-Za-z0-9\s&.]{1,35}?)(?:\s*[\.\,\!\n\(])",
    # Hindi: "Brand ke saath" / "Brand ke through" / "Brand ki taraf se"
    r"([A-Za-z0-9][A-Za-z0-9\s&.]{1,30}?)\s+(?:ke saath|ke through|ki taraf se)\b",
]]

# Reject these as brand names — they indicate no/disclaimer sponsorship
_JUNK_BRANDS = frozenset({
    "any", "any service", "any service provider", "this", "the", "a", "an",
    "my", "your", "our", "their", "us", "them", "i", "we", "you",
})


def _is_valid_brand(name: str) -> bool:
    low = name.lower().strip()
    if len(low) < 3 or len(low) > 50:
        return False
    return low not in _JUNK_BRANDS and not any(low.startswith(j) for j in _JUNK_BRANDS)

_UTM_LINK = re.compile(r"https?://(?:www\.)?([a-zA-Z0-9-]+)\.[a-z]{2,}[^\s]*utm_source=youtube", re.IGNORECASE)
# Custom short/affiliate links like go.kripeshadwani.com/nordvpn or creator.com/brand
_AFFILIATE_LINK = re.compile(r"https?://[a-zA-Z0-9.-]+\.[a-z]{2,}/([a-zA-Z][a-zA-Z0-9-]{2,30})[^\s\)]*", re.IGNORECASE)
# Simple affiliate/ref link domains (not social/CDN domains)
_SKIP_DOMAINS = {"youtube", "youtu", "instagram", "twitter", "facebook", "bit", "goo", "amzn", "t", "www", "google", "t.me", "discord"}

# Well-known sponsor brands for Indian YouTube — used for title-based and affiliate link detection.
# Maps lowercase brand key → display name.
KNOWN_BRANDS: dict[str, str] = {
    # VPN / Security
    "nordvpn": "NordVPN", "nordpass": "NordPass",
    "surfshark": "Surfshark", "expressvpn": "ExpressVPN",
    "dashlane": "Dashlane", "lastpass": "LastPass",
    # Hosting / Web
    "hostinger": "Hostinger", "bluehost": "Bluehost", "namecheap": "Namecheap",
    "godaddy": "GoDaddy", "wix": "Wix", "shopify": "Shopify", "squarespace": "Squarespace",
    # Productivity / Design
    "notion": "Notion", "canva": "Canva", "grammarly": "Grammarly",
    "loom": "Loom", "asana": "Asana", "monday": "Monday.com",
    # Learning / Books
    "skillshare": "Skillshare", "brilliant": "Brilliant",
    "masterclass": "MasterClass", "blinkist": "Blinkist", "audible": "Audible",
    "coursera": "Coursera", "udemy": "Udemy",
    "scaler": "Scaler", "upgrad": "UpGrad", "unacademy": "Unacademy",
    "byju": "BYJU'S", "vedantu": "Vedantu",
    # Finance / Crypto (India)
    "cred": "CRED", "razorpay": "Razorpay", "zepto": "Zepto",
    "groww": "Groww", "upstox": "Upstox", "smallcase": "Smallcase",
    "coindcx": "CoinDCX", "wazirx": "WazirX", "coinswitch": "CoinSwitch",
    # Fitness / Health
    "healthkart": "Healthkart", "muscleblaze": "MuscleBlaze",
    # Indian Consumer
    "jio": "Jio", "airtel": "Airtel",
    "meesho": "Meesho", "myntra": "Myntra", "flipkart": "Flipkart",
    "boat": "boAt", "noise": "Noise",
    # Beauty / Skincare (India)
    "mamaearth": "Mamaearth", "minimalist": "The Minimalist",
    "mcaffeine": "mCaffeine", "plum": "Plum Goodness",
    # Gaming / Fantasy
    "mpl": "MPL", "winzo": "WinZO", "dream11": "Dream11",
    # Creator Economy
    "epidemic sound": "Epidemic Sound", "artlist": "Artlist",
    "morning brew": "Morning Brew", "beehiiv": "Beehiiv", "gumroad": "Gumroad",
    # Business / Dev
    "fiverr": "Fiverr", "hubspot": "HubSpot", "amazon": "Amazon",
}


def _brand_from_title(title: str) -> str:
    """Return known brand display name if the video title clearly features it."""
    low = title.lower()
    for key, display in KNOWN_BRANDS.items():
        if key in low:
            if any(kw in low for kw in (
                "review", "sponsor", "deal", "offer", "best", "honest", "worth",
                "vs", "test", "compared", "collab", "partnership", "unboxing",
                "haul", "gifted", "feat", "with",
            )):
                return display
    return ""


def _extract_sponsor(description: str, title: str = "") -> tuple[str, str]:
    """Return (brand_name, disclosure_text) or ("", "")."""
    # 1. Try regex on description text
    for pattern in _PATTERNS:
        m = pattern.search(description)
        if m:
            brand = m.group(1).strip().rstrip(".,!").strip()
            if not _is_valid_brand(brand):
                continue
            start = max(0, m.start() - 20)
            snippet = description[start:start + 150].strip()
            return brand, snippet

    # 2. UTM affiliate link in description
    utm = _UTM_LINK.search(description)
    if utm:
        domain = utm.group(1)
        if domain not in _SKIP_DOMAINS:
            return domain.capitalize(), utm.group(0)

    # 3. Custom affiliate link — path segment matching a known brand
    for m in _AFFILIATE_LINK.finditer(description):
        path_seg = m.group(1).lower()
        for key, display in KNOWN_BRANDS.items():
            norm = key.replace(" ", "")
            if norm == path_seg or path_seg.startswith(norm):
                snippet = m.group(0)
                return display, snippet

    # 4. Brand name in video title (sponsor review/deal)
    if title:
        brand = _brand_from_title(title)
        if brand:
            return brand, f"Video title: {title[:100]}"

    return "", ""


class ExtractAgent(BaseAgent):
    def __init__(self, anakin: AnakinClient, on_update: Optional[Callable] = None):
        super().__init__("ExtractAgent", on_update)
        self.anakin = anakin

    async def execute(self, videos: list[dict]) -> list[SponsorMention]:
        total = len(videos)
        mentions: list[SponsorMention] = []
        scanned = 0
        BATCH = 20

        for batch_start in range(0, total, BATCH):
            batch = videos[batch_start:batch_start + BATCH]
            tasks = [
                self.anakin.wire("yt_video", {"video_id": v["video_id"]})
                for v in batch
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            self.track_api_call("scrape", len(batch))
            scanned += len(batch)

            for video, result in zip(batch, results):
                if isinstance(result, Exception):
                    continue
                description = result.get("description") or ""
                title = result.get("title") or video.get("title") or ""
                brand, disclosure = _extract_sponsor(description, title)
                if not brand:
                    continue
                mentions.append(SponsorMention(
                    sponsor_brand=brand,
                    disclosure_text=disclosure or None,
                    creator_handle=result.get("author") or video.get("channel_name") or "",
                    posted_date=result.get("published") or None,
                    video_url=video["url"],
                ))

            found_str = f" · {len(mentions)} found" if mentions else ""
            self.update(f"Scanning video descriptions... {scanned}/{total}{found_str}")

        self.update(f"Extracted {len(mentions)} sponsor mentions from {total} videos")
        return mentions
