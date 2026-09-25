from datetime import datetime, timedelta, timezone
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from ..db import get_db
from ..models import Article, Competitor, MonitoringCheck

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/overview")
async def overview(db: AsyncSession = Depends(get_db)):
    total = await db.scalar(select(func.count(Competitor.id))) or 0
    online = await db.scalar(select(func.count(Competitor.id)).where(Competitor.status == "online")) or 0
    offline = await db.scalar(select(func.count(Competitor.id)).where(Competitor.status == "offline")) or 0
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = await db.scalar(select(func.count(Article.id)).where(Article.detected_at >= today)) or 0
    delays = (await db.scalars(select(Article.detection_delay_seconds).where(Article.detection_delay_seconds.is_not(None)))).all()
    failed = await db.scalar(select(func.count(MonitoringCheck.id)).where(MonitoringCheck.status == "failed")) or 0
    within = sum(delay <= 300 for delay in delays)
    return {"total_competitors": total, "online_competitors": online, "offline_competitors": offline, "checking_competitors": 0, "articles_detected_today": today_count, "average_detection_delay_seconds": sum(delays) / len(delays) if delays else None, "fastest_detection_seconds": min(delays) if delays else None, "slowest_detection_seconds": max(delays) if delays else None, "within_five_minutes": within, "over_five_minutes": len(delays) - within, "failed_checks": failed}

@router.get("/delays")
async def delays(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Article.detected_at, Article.detection_delay_seconds, Article.detection_method, Article.competitor_id).where(Article.detection_delay_seconds.is_not(None)).order_by(Article.detected_at))).all()
    return [{"detected_at": row[0], "delay_seconds": row[1], "method": row[2], "competitor_id": row[3]} for row in rows]

@router.get("/methods")
async def methods(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Article.detection_method, func.count(Article.id)).group_by(Article.detection_method))).all()
    return [{"method": row[0], "count": row[1]} for row in rows]

@router.get("/competitors")
async def competitor_metrics(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Article.competitor_id, func.count(Article.id), func.avg(Article.detection_delay_seconds)).group_by(Article.competitor_id))).all()
    return [{"competitor_id": row[0], "article_count": row[1], "average_delay_seconds": row[2]} for row in rows]
