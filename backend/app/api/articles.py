from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import Article, DetectionEvent, MonitoringCheck, Notification
from ..schemas import ArticleRead

router = APIRouter(prefix="/api", tags=["articles"])

@router.get("/articles", response_model=list[ArticleRead])
async def list_articles(competitor_id: int | None = None, method: str | None = None, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), db: AsyncSession = Depends(get_db)):
    query = select(Article).order_by(Article.detected_at.desc()).limit(limit).offset(offset)
    if competitor_id:
        query = query.where(Article.competitor_id == competitor_id)
    if method:
        query = query.where(Article.detection_method == method)
    return (await db.scalars(query)).all()

@router.get("/articles/{article_id}", response_model=ArticleRead)
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@router.get("/monitoring/checks")
async def list_checks(limit: int = Query(100, ge=1, le=500), db: AsyncSession = Depends(get_db)):
    checks = (await db.scalars(select(MonitoringCheck).order_by(MonitoringCheck.started_at.desc()).limit(limit))).all()
    return [{"id": c.id, "competitor_id": c.competitor_id, "started_at": c.started_at, "completed_at": c.completed_at, "duration_ms": c.duration_ms, "status": c.status, "strategy": c.strategy, "articles_found": c.articles_found, "new_articles_found": c.new_articles_found, "error_message": c.error_message, "retry_count": c.retry_count} for c in checks]

@router.get("/notifications")
async def list_notifications(limit: int = Query(100, ge=1, le=500), db: AsyncSession = Depends(get_db)):
    notifications = (await db.scalars(select(Notification).order_by(Notification.created_at.desc()).limit(limit))).all()
    return [{"id": n.id, "article_id": n.article_id, "type": n.type, "status": n.status, "created_at": n.created_at} for n in notifications]

@router.get("/articles/{article_id}/events")
async def article_events(article_id: int, db: AsyncSession = Depends(get_db)):
    events = (await db.scalars(select(DetectionEvent).where(DetectionEvent.article_id == article_id).order_by(DetectionEvent.created_at.desc()))).all()
    return events
