from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from ..config import settings

COMMON_FEEDS = ("/feed", "/rss.xml", "/feed.xml", "/atom.xml", "/blog/feed", "/news/feed")
COMMON_SITEMAPS = ("/sitemap.xml", "/sitemap_index.xml")

async def analyze_website(website_url: str, feed_url: str | None = None, sitemap_url: str | None = None) -> dict:
    result = {"rss": {"found": False, "url": None, "kind": None}, "sitemap": {"found": False, "url": None}, "blog": {"found": False, "urls": []}, "structured_metadata": {"found": False, "types": []}, "recommended_strategy": "direct"}
    headers = {"User-Agent": "Signalwatch/0.1 (+local monitoring)"}
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds, follow_redirects=True, headers=headers) as client:
        response = await client.get(website_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        candidates = []
        for link in soup.select('link[rel="alternate"][href]'):
            link_type = (link.get("type") or "").lower()
            if "rss" in link_type or "atom" in link_type or "xml" in link_type:
                candidates.append((urljoin(str(response.url), link["href"]), "atom" if "atom" in link_type else "rss"))
        candidates.extend((urljoin(website_url, path), "unknown") for path in COMMON_FEEDS)
        for candidate, kind in candidates:
            try:
                feed_response = await client.get(candidate)
                content_type = feed_response.headers.get("content-type", "").lower()
                if feed_response.is_success and ("xml" in content_type or "rss" in feed_response.text[:500].lower() or "<feed" in feed_response.text[:500].lower()):
                    result["rss"] = {"found": True, "url": candidate, "kind": kind}
                    break
            except httpx.HTTPError:
                continue
        sitemap_candidates = []
        if sitemap_url:
            sitemap_candidates.append(sitemap_url)
        for path in COMMON_SITEMAPS:
            sitemap_candidates.append(urljoin(website_url, path))
        try:
            robots = await client.get(urljoin(website_url, "/robots.txt"))
            sitemap_candidates.extend(urljoin(website_url, line.split(":", 1)[1].strip()) for line in robots.text.splitlines() if line.lower().startswith("sitemap:"))
        except httpx.HTTPError:
            pass
        for candidate in dict.fromkeys(sitemap_candidates):
            try:
                sitemap_response = await client.get(candidate)
                body_start = sitemap_response.text[:1000].lower()
                if sitemap_response.is_success and ("<urlset" in body_start or "<sitemapindex" in body_start):
                    result["sitemap"] = {"found": True, "url": candidate}
                    break
            except httpx.HTTPError:
                continue
        blog_paths = []
        for anchor in soup.select("a[href]"):
            href = urljoin(str(response.url), anchor["href"])
            path = urlparse(href).path.lower()
            if any(token in path for token in ("/blog", "/news", "/articles", "/insights")):
                blog_paths.append(href)
        result["blog"] = {"found": bool(blog_paths), "urls": list(dict.fromkeys(blog_paths))[:20]}
        types = []
        for script in soup.select('script[type="application/ld+json"]'):
            text = script.string or script.get_text()
            if any(value in text for value in ("Article", "NewsArticle", "BlogPosting")):
                types.append("Article")
        result["structured_metadata"] = {"found": bool(types), "types": list(dict.fromkeys(types))}
    if result["rss"]["found"]:
        result["recommended_strategy"] = "rss"
    elif result["sitemap"]["found"]:
        result["recommended_strategy"] = "sitemap"
    return result
