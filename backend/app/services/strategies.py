from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urljoin
from urllib.parse import urlsplit
import feedparser
import httpx
from bs4 import BeautifulSoup
from .extraction import _parse_date
from ..config import settings
from ..utils.urls import normalize_url

@dataclass
class Candidate:
    url: str
    title: str
    published_at: datetime | None
    evidence: dict

class RSSDetector:
    name = "rss"
    async def detect(self, source_url: str) -> list[Candidate]:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds, follow_redirects=True, headers={"User-Agent": "Signalwatch/0.1"}) as client:
            response = await client.get(source_url)
            response.raise_for_status()
        parsed = feedparser.parse(response.content)
        candidates = []
        for entry in parsed.entries:
            url = entry.get("link")
            if not url:
                continue
            published = _parse_date(entry.get("published") or entry.get("updated") or entry.get("created"))
            candidates.append(Candidate(normalize_url(url), entry.get("title", "Untitled"), published, {"feed_id": entry.get("id"), "feed_url": source_url}))
        return candidates

class SitemapDetector:
    name = "sitemap"
    async def detect(self, source_url: str) -> list[Candidate]:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds, follow_redirects=True, headers={"User-Agent": "Signalwatch/0.1"}) as client:
            candidates = await self._read(source_url, client, set())
        filtered = [candidate for candidate in candidates if self._is_article_url(candidate.url)]
        deduplicated = list({candidate.url: candidate for candidate in filtered}.values())
        ordered = sorted(deduplicated, key=lambda candidate: (candidate.published_at is not None, candidate.published_at or datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
        return ordered[:settings.sitemap_candidate_limit]

    @staticmethod
    def _is_article_url(url: str) -> bool:
        segments = [segment for segment in urlsplit(url).path.lower().split("/") if segment]
        if len(segments) < 2:
            return False
        if segments[0] in {"topics", "topic", "category", "categories", "tag", "tags", "archive", "archives", "about", "contact", "image-library", "images"}:
            return False
        markers = {"article", "articles", "blog", "insight", "insights", "news", "post", "posts"}
        return any(segment in markers for segment in segments[:-1])
    async def _read(self, source_url, client, visited):
        if source_url in visited or len(visited) > 10:
            return []
        visited.add(source_url)
        response = await client.get(source_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "xml")
        if soup.find("sitemapindex"):
            results = []
            for item in soup.find_all("sitemap"):
                location = item.find("loc")
                if location:
                    results.extend(await self._read(location.get_text(strip=True), client, visited))
            return results
        results = []
        for item in soup.find_all("url"):
            location = item.find("loc")
            if not location:
                continue
            url = normalize_url(location.get_text(strip=True))
            lastmod = item.find("lastmod")
            results.append(Candidate(url, url.rsplit("/", 1)[-1].replace("-", " ").title(), _parse_date(lastmod.get_text(strip=True) if lastmod else None), {"sitemap_url": source_url}))
        return results

class DirectPageDetector:
    name = "direct"
    async def detect(self, source_url: str) -> list[Candidate]:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds, follow_redirects=True, headers={"User-Agent": "Signalwatch/0.1"}) as client:
            response = await client.get(source_url)
            response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        results = []
        for anchor in soup.select("a[href]"):
            href = urljoin(str(response.url), anchor["href"])
            if any(token in href.lower() for token in ("/blog/", "/news/", "/article/", "/insight/", "/post/")):
                results.append(Candidate(normalize_url(href), anchor.get_text(" ", strip=True) or href.rsplit("/", 1)[-1], None, {"listing_url": source_url}))
        return list({candidate.url: candidate for candidate in results}.values())
