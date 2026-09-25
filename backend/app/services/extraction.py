from datetime import datetime, timezone
import json
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import trafilatura
from dateutil import parser as date_parser

DATE_KEYS = ("datePublished", "dateCreated", "dateModified")

def _parse_date(value):
    if not value:
        return None
    try:
        parsed = date_parser.parse(str(value))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None

def extract_article(html: str, source_url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    metadata = {}
    images = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            value = json.loads(script.get_text())
            records = value if isinstance(value, list) else [value]
            for record in records:
                if isinstance(record, dict):
                    metadata.update(record)
        except json.JSONDecodeError:
            continue
    canonical = soup.select_one('link[rel="canonical"]')
    title = metadata.get("headline") or (soup.select_one("h1").get_text(" ", strip=True) if soup.select_one("h1") else None) or (soup.title.get_text(" ", strip=True) if soup.title else "Untitled")
    description = (soup.select_one('meta[name="description"]') or soup.select_one('meta[property="og:description"]'))
    author = metadata.get("author")
    if isinstance(author, dict):
        author = author.get("name")
    content = trafilatura.extract(html, url=source_url, include_links=True, include_images=True) or ""
    for position, image in enumerate(soup.select("article img, main img")):
        src = image.get("src") or image.get("data-src")
        if src:
            images.append({"image_url": urljoin(source_url, src), "alt_text": image.get("alt"), "position": position})
    return {"title": title, "canonical_url": canonical.get("href") if canonical else metadata.get("url") or source_url, "author": author, "published_at": _parse_date(metadata.get("datePublished")), "modified_at": _parse_date(metadata.get("dateModified")), "content": content, "meta_description": description.get("content") if description else None, "images": images, "structured_metadata": metadata, "extraction_status": "success" if content else "partial"}
