import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Callable, Optional

from dateutil import parser as dateparser

from .base import BaseAgent, AgentStatus
from .discovery_agent import DiscoveryAgent
from .harvest_agent import HarvestAgent
from .extract_agent import ExtractAgent
from .enrich_agent import EnrichAgent
from .draft_agent import DraftAgent
from ..anakin_client import AnakinClient
from ..models import BrandCard, BrandContact, SponsorMention

logger = logging.getLogger(__name__)

STAGE_RANGES = {
    "discover": (0,  20),
    "harvest":  (20, 40),
    "extract":  (40, 58),
    "enrich":   (58, 82),
    "draft":    (82, 100),
}


class HeadAgent:
    """Orchestrates all domain agents and monitors pipeline progress."""

    def __init__(self, anakin: AnakinClient, linkedin_session_id: Optional[str] = None):
        self.anakin = anakin
        self.linkedin_session_id = linkedin_session_id
        self.agents: list[BaseAgent] = []

    def _register(self, agent: BaseAgent) -> BaseAgent:
        agent._on_update = lambda a: None  # updates flow via update_job callback
        self.agents.append(agent)
        return agent

    def _aggregate(self) -> dict:
        totals: dict[str, int] = defaultdict(int)
        for agent in self.agents:
            for k, v in agent.api_calls.items():
                totals[k] += v
        return {
            "agent_reports": [a.report() for a in self.agents],
            "api_calls": dict(totals),
        }

    def _progress(self, stage: str, frac: float = 0.5) -> int:
        lo, hi = STAGE_RANGES.get(stage, (0, 100))
        return int(lo + (hi - lo) * max(0.0, min(1.0, frac)))

    async def run(
        self,
        channel_url: str,
        update_job: Callable,
        creator_profile: dict,
    ) -> list[BrandCard]:

        def push(stage: str, message: str, frac: float = 0.5):
            agg = self._aggregate()
            update_job(
                stage=stage,
                message=message,
                progress=self._progress(stage, frac),
                agent_reports=agg["agent_reports"],
                api_calls=agg["api_calls"],
            )

        # ── STAGE 1: DISCOVER ──────────────────────────────────────────────
        push("discover", "Looking up your channel and finding relevant sponsor brands...", 0.1)
        discovery = self._register(DiscoveryAgent(self.anakin))
        try:
            seed_videos: list[dict] = await discovery.run(channel_url)
        except Exception:
            seed_videos = []

        # Enrich creator_profile with real channel metadata for better openers
        if discovery.channel_info:
            info = discovery.channel_info
            creator_profile = {
                "channel_name": info.get("name") or creator_profile.get("channel_name", ""),
                "channel_url": channel_url,
                "niche": (info.get("keywords") or "")[:120] or creator_profile.get("niche", ""),
                "description": (info.get("description") or "")[:200],
            }

        # Also collect the input channel's own recent videos so self-deals are caught by extract
        own_channel_id = discovery.own_channel_id
        own_videos: list[dict] = []
        if own_channel_id:
            push("discover", "Also scanning your own recent videos for past brand deals...", 0.85)
            try:
                handle = channel_url.rstrip("/").split("/")[-1].lstrip("@")
                own_result = await self.anakin.wire("yt_search", {"query": handle, "limit": 10})
                for item in (own_result.get("data") or []):
                    if item.get("channel_id") == own_channel_id and item.get("video_id"):
                        own_videos.append({
                            "video_id": item["video_id"],
                            "channel_id": own_channel_id,
                            "channel_name": item.get("channel", handle),
                            "title": item.get("title", ""),
                            "url": item.get("url", f"https://www.youtube.com/watch?v={item['video_id']}"),
                        })
            except Exception:
                pass

        push("discover", f"Found {len(seed_videos)} videos from similar creators", 1.0)

        if not seed_videos and not own_videos:
            update_job(stage="error", message="Could not find similar creators. Try a channel with more published content.", progress=0, agent_reports=[], api_calls={})
            return []

        # ── STAGE 2: HARVEST (parallel per unique channel) ─────────────────
        seen_channels: dict[str, str] = {}
        for v in seed_videos:
            cid = v.get("channel_id", "")
            cname = v.get("channel_name", "")
            if cid and cid not in seen_channels and cname:
                seen_channels[cid] = cname

        push("harvest", f"Fetching brand deal videos from {len(seen_channels)} similar channels...", 0.05)
        harvest_agents = [
            self._register(HarvestAgent(self.anakin, name, channel_id=cid))
            for cid, name in list(seen_channels.items())[:12]
        ]
        harvest_results = await asyncio.gather(
            *[a.run() for a in harvest_agents], return_exceptions=True
        )
        push("harvest", "Harvest complete", 0.9)

        # Pool order: own videos → harvest (brand-deal targeted) → seed (discovery)
        # Harvest must come before seed so it isn't squeezed out by the cap
        all_videos: list[dict] = list(own_videos)
        seen_ids = {v["video_id"] for v in own_videos}

        for r in harvest_results:
            if isinstance(r, list):
                for v in r:
                    if v.get("video_id") not in seen_ids:
                        seen_ids.add(v["video_id"])
                        all_videos.append(v)
        for v in seed_videos:
            if v.get("video_id") not in seen_ids:
                seen_ids.add(v["video_id"])
                all_videos.append(v)
        all_videos = all_videos[:100]
        push("harvest", f"Collected {len(all_videos)} unique videos total", 1.0)

        # ── STAGE 3: EXTRACT ───────────────────────────────────────────────
        push("extract", f"Fetching descriptions for {len(all_videos)} videos via Wire yt_video...", 0.1)
        extract = self._register(ExtractAgent(self.anakin))
        try:
            mentions: list[SponsorMention] = await extract.run(all_videos)
        except Exception:
            mentions = []
        push("extract", f"Found {len(mentions)} sponsor mentions", 1.0)

        if not mentions:
            update_job(stage="error", message="No sponsor mentions found. Try a channel in a niche with active Indian sponsorships.", progress=0, agent_reports=[], api_calls={})
            return []

        brand_map: dict[str, list[SponsorMention]] = defaultdict(list)
        for m in mentions:
            if m.sponsor_brand:
                brand_map[m.sponsor_brand.strip().lower()].append(m)
        ranked = sorted(brand_map.items(), key=lambda x: len(x[1]), reverse=True)[:25]

        # ── STAGE 4: ENRICH (parallel) ─────────────────────────────────────
        push("enrich", f"Enriching {len(ranked)} brands with LinkedIn + Search API in parallel...", 0.05)
        enrich_agents = [
            self._register(EnrichAgent(self.anakin, ms[0].sponsor_brand, self.linkedin_session_id))
            for _, ms in ranked
        ]
        enrich_results = await asyncio.gather(
            *[a.run() for a in enrich_agents], return_exceptions=True
        )
        push("enrich", f"Enriched {sum(1 for r in enrich_results if not isinstance(r, Exception))} brand contacts", 1.0)

        # ── STAGE 5: DRAFT (parallel) ──────────────────────────────────────
        push("draft", f"Generating personalized openers for {len(ranked)} brands in parallel...", 0.05)
        draft_tasks = []
        for i, (_, brand_mentions) in enumerate(ranked):
            contact = (
                enrich_results[i]
                if i < len(enrich_results) and not isinstance(enrich_results[i], Exception)
                else BrandContact()
            )
            best = brand_mentions[0]
            agent = self._register(
                DraftAgent(
                    brand_name=best.sponsor_brand,
                    contact=contact,
                    last_sponsored_creator=best.creator_handle or "a similar creator",
                    last_campaign_snippet=best.disclosure_text,
                    creator_profile=creator_profile,
                )
            )
            draft_tasks.append(
                agent.run(
                    source_videos=[m.video_url for m in brand_mentions],
                    last_sponsored_days_ago=self._days_ago(best.posted_date),
                )
            )

        draft_results = await asyncio.gather(*draft_tasks, return_exceptions=True)
        cards = [r for r in draft_results if isinstance(r, BrandCard)]

        push("draft", f"Generated {len(cards)} brand cards", 1.0)
        return cards

    @staticmethod
    def _days_ago(date_str: Optional[str]) -> int:
        if not date_str:
            return -1
        try:
            dt = dateparser.parse(date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return max(0, (datetime.now(timezone.utc) - dt).days)
        except Exception:
            return -1
