from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
from app.models.base import get_db
from app.models.user import User
from app.models.job import SearchConfig, JobListing, TokenSettings, SearchInterval, TokenTransaction
from app.models.proxy_session import LinkedInSession
from app.api.deps import get_current_user

router = APIRouter(prefix="/jobs", tags=["jobs"])


class CreateSearchConfigRequest(BaseModel):
    keywords: List[str]
    location: str | None = None
    interval: str = "4h"


@router.post("/search-config")
def create_search_config(
    body: CreateSearchConfigRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    li_session = db.query(LinkedInSession).filter(
        LinkedInSession.user_id == user.id, LinkedInSession.is_logged_in == True
    ).first()
    if not li_session:
        raise HTTPException(400, "LinkedIn'e giriş yapmalısınız")

    settings = db.query(TokenSettings).filter(TokenSettings.id == 1).first()

    # 2h interval costs extra tokens
    if body.interval == "2h":
        cost = settings.cost_search_2h if settings else 100
        if user.tokens < cost:
            raise HTTPException(400, f"2 saatlik arama için {cost} token gerekli")
        user.tokens -= cost
        tx = TokenTransaction(user_id=user.id, amount=-cost, reason="2 saatlik arama aktivasyonu")
        db.add(tx)

    interval_enum = SearchInterval.two_hours if body.interval == "2h" else SearchInterval.four_hours
    interval_hours = 2 if body.interval == "2h" else 4

    config = SearchConfig(
        user_id=user.id,
        keywords=body.keywords,
        location=body.location,
        interval=interval_enum,
        next_run_at=datetime.utcnow() + timedelta(minutes=1),
    )
    db.add(config)
    db.commit()

    # Schedule first run
    from app.tasks.search_tasks import run_linkedin_search
    run_linkedin_search.apply_async(
        args=[str(config.id)],
        countdown=60,
        queue="linkedin",
    )

    return {"message": "Arama konfigürasyonu oluşturuldu", "config_id": str(config.id)}


@router.get("/search-configs")
def list_search_configs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    configs = db.query(SearchConfig).filter(SearchConfig.user_id == user.id).all()
    return [
        {
            "id": str(c.id),
            "keywords": c.keywords,
            "location": c.location,
            "interval": c.interval.value,
            "is_active": c.is_active,
            "next_run_at": c.next_run_at,
            "last_run_at": c.last_run_at,
        }
        for c in configs
    ]


@router.delete("/search-configs/{config_id}")
def delete_search_config(
    config_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    config = db.query(SearchConfig).filter(
        SearchConfig.id == config_id, SearchConfig.user_id == user.id
    ).first()
    if not config:
        raise HTTPException(404, "Bulunamadı")
    config.is_active = False
    db.commit()
    return {"message": "Arama durduruldu"}


@router.get("/listings")
def list_job_listings(
    page: int = 1,
    per_page: int = 20,
    is_new: bool | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(JobListing).filter(JobListing.user_id == user.id)
    if is_new is not None:
        q = q.filter(JobListing.is_new == is_new)
    total = q.count()
    listings = q.order_by(JobListing.found_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [
            {
                "id": str(j.id),
                "title": j.title,
                "company": j.company,
                "location": j.location,
                "description": j.description,
                "url": j.url,
                "posted_at": j.posted_at,
                "is_new": j.is_new,
                "ai_match_score": j.ai_match_score,
                "ai_analysis": j.ai_analysis,
                "found_at": j.found_at,
            }
            for j in listings
        ],
    }


@router.patch("/listings/{listing_id}/read")
def mark_as_read(
    listing_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    listing = db.query(JobListing).filter(
        JobListing.id == listing_id, JobListing.user_id == user.id
    ).first()
    if not listing:
        raise HTTPException(404, "Bulunamadı")
    listing.is_new = False
    db.commit()
    return {"message": "Okundu olarak işaretlendi"}
