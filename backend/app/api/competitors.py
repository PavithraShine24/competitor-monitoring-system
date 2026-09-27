from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import Competitor, MonitoringConfig
from ..schemas import CompetitorCreate, CompetitorRead, CompetitorUpdate
from ..services.analysis import analyze_website
from ..utils.urls import validate_public_url
from ..security import require_user
from ..worker.tasks import check_competitor

router = APIRouter(prefix="/api/competitors", tags=["competitors"])

@router.post("", response_model=CompetitorRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_user)])
async def create_competitor(payload: CompetitorCreate, db: AsyncSession = Depends(get_db)):
    try:
        website_url = validate_public_url(str(payload.website_url))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    competitor = Competitor(name=payload.name, website_url=website_url, blog_url=str(payload.blog_url) if payload.blog_url else None, feed_url=str(payload.feed_url) if payload.feed_url else None, sitemap_url=str(payload.sitemap_url) if payload.sitemap_url else None, enabled=payload.enabled, status="pending")
    db.add(competitor)
    await db.flush()
    db.add(MonitoringConfig(competitor_id=competitor.id, strategy=payload.strategy, enabled=payload.enabled))
    await db.commit()
    await db.refresh(competitor)
    return competitor

@router.get("", response_model=list[CompetitorRead])
async def list_competitors(db: AsyncSession = Depends(get_db)):
    return (await db.scalars(select(Competitor).order_by(Competitor.created_at.desc()))).all()

@router.get("/{competitor_id}", response_model=CompetitorRead)
async def get_competitor(competitor_id: int, db: AsyncSession = Depends(get_db)):
    competitor = await db.get(Competitor, competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return competitor

@router.put("/{competitor_id}", response_model=CompetitorRead, dependencies=[Depends(require_user)])
async def update_competitor(competitor_id: int, payload: CompetitorUpdate, db: AsyncSession = Depends(get_db)):
    competitor = await db.get(Competitor, competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(competitor, key, str(value) if key.endswith("_url") and value else value)
    await db.commit()
    await db.refresh(competitor)
    return competitor

@router.delete("/{competitor_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_user)])
async def delete_competitor(competitor_id: int, db: AsyncSession = Depends(get_db)):
    competitor = await db.get(Competitor, competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    await db.delete(competitor)
    await db.commit()

@router.post("/{competitor_id}/analyze", dependencies=[Depends(require_user)])
async def analyze_competitor(competitor_id: int, db: AsyncSession = Depends(get_db)):
    competitor = await db.get(Competitor, competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    try:
        result = await analyze_website(competitor.website_url, competitor.feed_url, competitor.sitemap_url)
    except Exception as error:
        competitor.status = "analysis_failed"
        await db.commit()
        raise HTTPException(status_code=502, detail=f"Website analysis failed: {error}") from error
    if result["rss"]["found"]:
        competitor.feed_url = result["rss"]["url"]
    if result["sitemap"]["found"]:
        competitor.sitemap_url = result["sitemap"]["url"]
    if result["blog"]["found"] and not competitor.blog_url:
        competitor.blog_url = result["blog"]["urls"][0]
    config = await db.scalar(select(MonitoringConfig).where(MonitoringConfig.competitor_id == competitor.id))
    config.strategy = result["recommended_strategy"]
    config.discovered_sources = result
    competitor.status = "ready"
    await db.commit()
    return result

@router.post("/{competitor_id}/check", dependencies=[Depends(require_user)])
async def check_now(competitor_id: int, db: AsyncSession = Depends(get_db)):
    competitor = await db.get(Competitor, competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    check_competitor.delay(competitor_id)
    return {"status": "queued", "competitor_id": competitor_id}

@router.post("/{competitor_id}/{action}", response_model=CompetitorRead, dependencies=[Depends(require_user)])
async def set_monitoring(competitor_id: int, action: str, db: AsyncSession = Depends(get_db)):
    if action not in {"enable", "disable"}:
        raise HTTPException(status_code=404, detail="Unknown action")
    competitor = await db.get(Competitor, competitor_id)
    config = await db.scalar(select(MonitoringConfig).where(MonitoringConfig.competitor_id == competitor_id))
    if not competitor or not config:
        raise HTTPException(status_code=404, detail="Competitor not found")
    enabled = action == "enable"
    competitor.enabled = enabled
    config.enabled = enabled
    competitor.status = "ready" if enabled else "disabled"
    await db.commit()
    await db.refresh(competitor)
    return competitor
