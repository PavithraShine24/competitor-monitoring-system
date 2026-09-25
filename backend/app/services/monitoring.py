from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from .extraction import extract_article
from .strategies import Candidate, DirectPageDetector, RSSDetector, SitemapDetector
from ..models import Article, ArticleImage, DetectionEvent, MonitoringCheck, Notification
from ..utils.time import detection_delay_seconds, utc_now
from ..utils.urls import normalize_url

DETECTORS = {"rss": RSSDetector, "sitemap": SitemapDetector, "direct": DirectPageDetector}

async def run_check(session: AsyncSession, competitor, config, retry_count: int = 0) -> MonitoringCheck:
    started = utc_now()
    check = MonitoringCheck(competitor_id=competitor.id, started_at=started, status="running", strategy=config.strategy, retry_count=retry_count)
    session.add(check)
    await session.flush()
    strategy = config.strategy
    source = competitor.feed_url if strategy == "rss" else competitor.sitemap_url if strategy == "sitemap" else competitor.blog_url or competitor.website_url
    if strategy == "auto":
        strategy = "rss" if competitor.feed_url else "sitemap" if competitor.sitemap_url else "direct"
        source = competitor.feed_url if strategy == "rss" else competitor.sitemap_url if strategy == "sitemap" else competitor.blog_url or competitor.website_url
        check.strategy = strategy
    try:
        candidates: list[Candidate] = await DETECTORS[strategy]().detect(source)
        check.articles_found = len(candidates)
        for candidate in candidates:
            normalized = normalize_url(candidate.url)
            existing = await session.scalar(select(Article).where(Article.competitor_id == competitor.id, Article.normalized_url == normalized))
            if existing:
                continue
            detected_at = utc_now()
            article = Article(competitor_id=competitor.id, title=candidate.title, url=candidate.url, normalized_url=normalized, source_url=source, published_at=candidate.published_at, detected_at=detected_at, detection_delay_seconds=detection_delay_seconds(candidate.published_at, detected_at), detection_method=strategy, extraction_status="pending")
            session.add(article)
            try:
                await session.flush()
            except IntegrityError:
                await session.rollback()
                continue
            try:
                async with __import__("httpx").AsyncClient(timeout=20, follow_redirects=True, headers={"User-Agent": "Signalwatch/0.1"}) as client:
                    page = await client.get(candidate.url)
                    page.raise_for_status()
                extracted = extract_article(page.text, candidate.url)
                for key, value in extracted.items():
                    if key != "images":
                        setattr(article, key, value)
                for image in extracted["images"]:
                    session.add(ArticleImage(article_id=article.id, **image))
            except Exception as error:
                article.extraction_status = "failed"
                article.structured_metadata = {"error": str(error)}
            session.add(DetectionEvent(article_id=article.id, competitor_id=competitor.id, monitoring_check_id=check.id, detection_method=strategy, detected_at=detected_at, published_at=article.published_at, detection_delay_seconds=article.detection_delay_seconds, evidence=candidate.evidence))
            session.add(Notification(article_id=article.id, type="in_app", status="created"))
            check.new_articles_found += 1
        finished = utc_now()
        check.completed_at = finished
        check.duration_ms = int((finished - started).total_seconds() * 1000)
        check.status = "success"
        competitor.last_checked_at = finished
        competitor.status = "online"
        if check.new_articles_found:
            competitor.last_successful_detection_at = finished
    except Exception as error:
        finished = utc_now()
        check.completed_at = finished
        check.duration_ms = int((finished - started).total_seconds() * 1000)
        check.status = "failed"
        check.error_message = str(error)
        competitor.last_checked_at = finished
        competitor.status = "offline"
    await session.commit()
    return check
