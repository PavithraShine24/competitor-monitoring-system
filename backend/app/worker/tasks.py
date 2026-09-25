import asyncio
from sqlalchemy import select
from ..db import SessionLocal
from ..models import Competitor, MonitoringConfig
from ..services.monitoring import run_check
from .celery_app import celery_app

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def check_competitor(self, competitor_id: int):
    return asyncio.run(_check_competitor(competitor_id, self.request.retries))

async def _check_competitor(competitor_id: int, retry_count: int):
    async with SessionLocal() as session:
        competitor = await session.get(Competitor, competitor_id)
        config = await session.scalar(select(MonitoringConfig).where(MonitoringConfig.competitor_id == competitor_id))
        if not competitor or not config or not competitor.enabled or not config.enabled:
            return {"status": "skipped"}
        check = await run_check(session, competitor, config, retry_count)
        return {"status": check.status, "new_articles": check.new_articles_found}

@celery_app.task
def enqueue_enabled():
    asyncio.run(_enqueue_enabled())

async def _enqueue_enabled():
    async with SessionLocal() as session:
        competitors = (await session.scalars(select(Competitor).where(Competitor.enabled.is_(True)))).all()
        for competitor in competitors:
            check_competitor.delay(competitor.id)
