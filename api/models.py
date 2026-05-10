from pydantic import BaseModel
from typing import Optional


class SponsorMention(BaseModel):
    sponsor_brand: str
    disclosure_text: Optional[str] = None
    creator_handle: str = ""
    posted_date: Optional[str] = None
    video_url: str


class BrandContact(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None


class BrandCard(BaseModel):
    brand_name: str
    last_sponsored_creator: str
    last_sponsored_days_ago: int = -1
    contact: BrandContact
    opener: str
    source_videos: list[str] = []
    last_campaign_snippet: Optional[str] = None


class JobStatus(BaseModel):
    job_id: str
    stage: str
    message: str
    progress: int
    brands: list[BrandCard] = []
    agent_reports: list[dict] = []
    api_calls: dict[str, int] = {}
    error: Optional[str] = None


class StartRequest(BaseModel):
    channel_url: str
