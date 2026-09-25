from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urljoin
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
            return await self._read(source_url, client, set())
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
            path = url.lower()
            if any(token in path for token in ("/blog", "/news", "/article", "/insight", "/post")):
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
