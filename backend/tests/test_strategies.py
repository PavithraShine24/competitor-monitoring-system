from datetime import datetime, timezone

import pytest

from app.config import settings
from app.services.strategies import Candidate, DirectPageDetector, RSSDetector, SitemapDetector

class FakeResponse:
    def __init__(self, body):
        self.content = body.encode()

    def raise_for_status(self):
        return None

class FakeClient:
    def __init__(self, responses):
        self.responses = responses

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def get(self, url):
        return FakeResponse(self.responses[url])

def test_rss_detector_has_common_strategy_name():
    assert RSSDetector.name == "rss"

def test_sitemap_detector_keeps_local_demo_article():
    assert SitemapDetector._is_article_url("http://localhost:9100/a/article/article-1")

@pytest.mark.parametrize("url", [
    "https://example.com/blog",
    "https://example.com/news",
    "https://example.com/topics/google-ai",
    "https://example.com/category/technology",
    "https://example.com/archive/2026",
])
def test_sitemap_detector_filters_broad_non_article_urls(url):
    assert not SitemapDetector._is_article_url(url)

@pytest.mark.asyncio
async def test_sitemap_index_recursion_and_candidate_limit(monkeypatch):
    detector = SitemapDetector()
    child_urls = [f"https://example.com/blog/article-{index}" for index in range(4)]
    child_xml = "<urlset>" + "".join(f"<url><loc>{url}</loc></url>" for url in child_urls) + "</urlset>"
    responses = {"https://example.com/sitemap.xml": "<sitemapindex><sitemap><loc>https://example.com/child.xml</loc></sitemap></sitemapindex>", "https://example.com/child.xml": child_xml}
    monkeypatch.setattr("app.services.strategies.httpx.AsyncClient", lambda **_kwargs: FakeClient(responses))
    monkeypatch.setattr(settings, "sitemap_candidate_limit", 2)
    result = await detector.detect("https://example.com/sitemap.xml")
    assert [candidate.url for candidate in result] == child_urls[:2]

@pytest.mark.asyncio
async def test_local_demo_sitemap_article_is_returned_by_detector(monkeypatch):
    xml = "<urlset><url><loc>http://localhost:9100/a/article/article-1</loc></url></urlset>"
    monkeypatch.setattr("app.services.strategies.httpx.AsyncClient", lambda **_kwargs: FakeClient({"http://localhost:9100/a/sitemap.xml": xml}))
    result = await SitemapDetector().detect("http://localhost:9100/a/sitemap.xml")
    assert [candidate.url for candidate in result] == ["http://localhost:9100/a/article/article-1"]

@pytest.mark.asyncio
async def test_sitemap_candidates_are_deduplicated(monkeypatch):
    detector = SitemapDetector()
    duplicate = Candidate("https://example.com/blog/article-1", "Article 1", None, {})

    async def read(_source, _client, _visited):
        return [duplicate, duplicate]

    monkeypatch.setattr(detector, "_read", read)
    monkeypatch.setattr(settings, "sitemap_candidate_limit", 500)
    result = await detector.detect("https://example.com/sitemap.xml")
    assert [candidate.url for candidate in result] == [duplicate.url]

@pytest.mark.asyncio
async def test_sitemap_candidates_are_sorted_by_lastmod_before_limit(monkeypatch):
    detector = SitemapDetector()
    dated_old = Candidate("https://example.com/blog/old", "Old", datetime(2026, 1, 1, tzinfo=timezone.utc), {})
    undated = Candidate("https://example.com/blog/undated", "Undated", None, {})
    dated_new = Candidate("https://example.com/blog/new", "New", datetime(2026, 9, 26, tzinfo=timezone.utc), {})

    async def read(_source, _client, _visited):
        return [dated_old, undated, dated_new]

    monkeypatch.setattr(detector, "_read", read)
    monkeypatch.setattr(settings, "sitemap_candidate_limit", 2)
    result = await detector.detect("https://example.com/sitemap.xml")
    assert [candidate.url for candidate in result] == [dated_new.url, dated_old.url]

@pytest.mark.asyncio
async def test_undated_sitemap_candidates_follow_dated_candidates(monkeypatch):
    detector = SitemapDetector()
    dated = Candidate("https://example.com/blog/dated", "Dated", datetime(2026, 9, 26, tzinfo=timezone.utc), {})
    undated = Candidate("https://example.com/blog/undated", "Undated", None, {})

    async def read(_source, _client, _visited):
        return [undated, dated]

    monkeypatch.setattr(detector, "_read", read)
    monkeypatch.setattr(settings, "sitemap_candidate_limit", 50)
    result = await detector.detect("https://example.com/sitemap.xml")
    assert [candidate.url for candidate in result] == [dated.url, undated.url]

def test_rss_and_direct_detector_interfaces_remain_unchanged():
    assert RSSDetector.name == "rss"
    assert DirectPageDetector.name == "direct"
