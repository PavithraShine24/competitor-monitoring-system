from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

class CompetitorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    website_url: HttpUrl
    blog_url: HttpUrl | None = None
    feed_url: HttpUrl | None = None
    sitemap_url: HttpUrl | None = None
    enabled: bool = False
    strategy: str = Field(default="auto", pattern="^(auto|rss|sitemap|direct)$")

class CompetitorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    blog_url: HttpUrl | None = None
    feed_url: HttpUrl | None = None
    sitemap_url: HttpUrl | None = None
    enabled: bool | None = None

class CompetitorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    website_url: str
    blog_url: str | None
    feed_url: str | None
    sitemap_url: str | None
    enabled: bool
    status: str
    last_checked_at: datetime | None
    last_successful_detection_at: datetime | None

class ArticleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    competitor_id: int
    title: str
    url: str
    canonical_url: str | None
    source_url: str
    author: str | None
    published_at: datetime | None
    modified_at: datetime | None
    detected_at: datetime
    detection_delay_seconds: float | None
    detection_method: str
    content: str | None
    meta_description: str | None
    extraction_status: str

class HealthRead(BaseModel):
    status: str
    database: str
    redis: str
