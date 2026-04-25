from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.base import get_db
from app.models.user import User
from app.models.proxy_session import ProxySession, LinkedInSession
from app.models.job import TokenSettings
from app.api.deps import get_current_user
from app.services.oxylabs import oxylabs_service
from app.services.linkedin import linkedin_login
import secrets

router = APIRouter(prefix="/proxy", tags=["proxy"])


class LinkedInLoginRequest(BaseModel):
    email: str
    password: str


@router.post("/acquire")
async def acquire_residential_ip(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    settings = db.query(TokenSettings).filter(TokenSettings.id == 1).first()
    cost = settings.cost_residential_ip if settings else 20

    if user.tokens < cost:
        raise HTTPException(400, f"Yetersiz token. Gerekli: {cost}, Mevcut: {user.tokens}")

    # Check existing active session
    existing = db.query(ProxySession).filter(
        ProxySession.user_id == user.id, ProxySession.is_active == True
    ).first()
    if existing:
        return {"message": "Zaten aktif bir proxy bağlantınız var"}

    # Create Oxylabs sub-user
    sub_username = f"co_{str(user.id).replace('-', '')[:16]}"
    sub_password = secrets.token_urlsafe(12)

    result = await oxylabs_service.create_sub_user(sub_username, sub_password)
    if not result:
        raise HTTPException(500, "Proxy oluşturulamadı, lütfen tekrar deneyin")

    proxy = ProxySession(
        user_id=user.id,
        oxylabs_sub_user_id=result.get("id", sub_username),
        proxy_host="pr.oxylabs.io",
        proxy_port=7777,
        proxy_username=sub_username,
        proxy_password=sub_password,
    )
    db.add(proxy)
    user.tokens -= cost
    db.commit()
    return {"message": "Residential IP alındı", "remaining_tokens": user.tokens}


@router.post("/linkedin/login")
async def linkedin_login_endpoint(
    body: LinkedInLoginRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    proxy = db.query(ProxySession).filter(
        ProxySession.user_id == user.id, ProxySession.is_active == True
    ).first()
    if not proxy:
        raise HTTPException(400, "Önce residential IP almalısınız")

    proxy_config = {
        "server": proxy.proxy_host,
        "port": proxy.proxy_port,
        "username": proxy.proxy_username,
        "password": proxy.proxy_password,
    }

    existing_session = db.query(LinkedInSession).filter(LinkedInSession.user_id == user.id).first()
    existing_cookies = existing_session.cookies if existing_session else None

    success, cookies = await linkedin_login(
        str(user.id), body.email, body.password, proxy_config, existing_cookies
    )

    if not success:
        raise HTTPException(400, "LinkedIn girişi başarısız. Bilgilerinizi kontrol edin.")

    if existing_session:
        existing_session.cookies = cookies
        existing_session.is_logged_in = True
        existing_session.linkedin_email = body.email
        from datetime import datetime
        existing_session.last_login_at = datetime.utcnow()
    else:
        from datetime import datetime
        li_session = LinkedInSession(
            user_id=user.id,
            cookies=cookies,
            linkedin_email=body.email,
            is_logged_in=True,
            last_login_at=datetime.utcnow(),
        )
        db.add(li_session)
    db.commit()
    return {"message": "LinkedIn'e başarıyla giriş yapıldı"}


@router.get("/status")
def proxy_status(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    proxy = db.query(ProxySession).filter(
        ProxySession.user_id == user.id, ProxySession.is_active == True
    ).first()
    li_session = db.query(LinkedInSession).filter(LinkedInSession.user_id == user.id).first()
    return {
        "has_proxy": proxy is not None,
        "linkedin_logged_in": li_session.is_logged_in if li_session else False,
        "linkedin_email": li_session.linkedin_email if li_session else None,
    }
