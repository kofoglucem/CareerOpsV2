import asyncio
from datetime import datetime, timedelta
from celery import shared_task
from sqlalchemy.orm import Session
from app.models.base import SessionLocal
from app.models.job import SearchConfig, JobListing, SearchInterval
from app.models.proxy_session import LinkedInSession
from app.services.browser import create_browser_context
from app.services.linkedin import search_linkedin_jobs
from .celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, queue="linkedin")
def run_linkedin_search(self, search_config_id: str):
    """Run LinkedIn job search for a single config. Queue ensures serial execution."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_async_search(search_config_id))
    finally:
        loop.close()


async def _async_search(search_config_id: str):
    db: Session = SessionLocal()
    try:
        config = db.query(SearchConfig).filter(SearchConfig.id == search_config_id).first()
        if not config or not config.is_active:
            return

        linkedin_session = db.query(LinkedInSession).filter(
            LinkedInSession.user_id == config.user_id,
            LinkedInSession.is_logged_in == True,
        ).first()

        if not linkedin_session or not linkedin_session.cookies:
            return

        proxy_session = db.query(
            __import__("app.models.proxy_session", fromlist=["ProxySession"]).ProxySession
        ).filter_by(user_id=config.user_id, is_active=True).first()

        proxy_config = None
        if proxy_session:
            proxy_config = {
                "server": proxy_session.proxy_host,
                "port": proxy_session.proxy_port,
                "username": proxy_session.proxy_username,
                "password": proxy_session.proxy_password,
            }

        context = await create_browser_context(
            str(config.user_id),
            proxy_config=proxy_config,
            cookies=linkedin_session.cookies,
        )

        jobs = await search_linkedin_jobs(
            context,
            keywords=config.keywords,
            location=None,
        )

        existing_ids = {
            r[0] for r in db.query(JobListing.linkedin_job_id).filter(
                JobListing.user_id == config.user_id,
                JobListing.linkedin_job_id.isnot(None),
            ).all()
        }

        for job in jobs:
            if job["linkedin_job_id"] and job["linkedin_job_id"] in existing_ids:
                continue
            listing = JobListing(
                user_id=config.user_id,
                search_config_id=config.id,
                **job,
            )
            db.add(listing)

        interval_hours = 2 if config.interval == SearchInterval.two_hours else 4
        config.last_run_at = datetime.utcnow()
        config.next_run_at = datetime.utcnow() + timedelta(hours=interval_hours)
        db.commit()

        # Schedule next run
        run_linkedin_search.apply_async(
            args=[str(config.id)],
            eta=config.next_run_at,
            queue="linkedin",
        )
    finally:
        db.close()
