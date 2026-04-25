from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.base import get_db
from app.models.user import User
from app.models.job import JobListing, TokenSettings, TokenTransaction
from app.models.proxy_session import AISession
from app.api.deps import get_current_user
from app.services.browser import create_browser_context, save_cookies
from datetime import datetime

router = APIRouter(prefix="/ai", tags=["ai"])


class AILoginRequest(BaseModel):
    provider: str  # deepseek or chatgpt
    email: str
    password: str


class EvaluateJobRequest(BaseModel):
    job_listing_id: str


LOGIN_URLS = {
    "deepseek": "https://chat.deepseek.com/sign_in",
    "chatgpt": "https://chat.openai.com/auth/login",
}


@router.post("/login")
async def ai_login(
    body: AILoginRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if body.provider not in ("deepseek", "chatgpt"):
        raise HTTPException(400, "Desteklenen sağlayıcılar: deepseek, chatgpt")

    proxy = db.query(
        __import__("app.models.proxy_session", fromlist=["ProxySession"]).ProxySession
    ).filter_by(user_id=user.id, is_active=True).first()

    proxy_config = None
    if proxy:
        proxy_config = {
            "server": proxy.proxy_host,
            "port": proxy.proxy_port,
            "username": proxy.proxy_username,
            "password": proxy.proxy_password,
        }

    existing = db.query(AISession).filter(
        AISession.user_id == user.id, AISession.provider == body.provider
    ).first()
    existing_cookies = existing.cookies if existing else None

    context = await create_browser_context(
        f"{user.id}_{body.provider}", proxy_config, existing_cookies
    )
    page = await context.new_page()
    success = False
    try:
        await page.goto(LOGIN_URLS[body.provider], wait_until="networkidle", timeout=30000)
        # Basic login attempt — may need 2FA handling in production
        email_sel = 'input[type="email"], input[name="email"]'
        pass_sel = 'input[type="password"]'
        await page.fill(email_sel, body.email)
        await page.fill(pass_sel, body.password)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(5000)
        cookies = await save_cookies(context)
        success = True
    except Exception:
        cookies = []
    finally:
        await page.close()

    if not success:
        raise HTTPException(400, "AI servisine giriş başarısız")

    if existing:
        existing.cookies = cookies
        existing.is_logged_in = True
        existing.last_login_at = datetime.utcnow()
    else:
        ai_sess = AISession(
            user_id=user.id,
            provider=body.provider,
            cookies=cookies,
            is_logged_in=True,
            last_login_at=datetime.utcnow(),
        )
        db.add(ai_sess)
    db.commit()
    return {"message": f"{body.provider} oturumu kaydedildi"}


@router.post("/evaluate")
async def evaluate_job(
    body: EvaluateJobRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.cv_text:
        raise HTTPException(400, "Önce CV'nizi yüklemelisiniz")

    settings = db.query(TokenSettings).filter(TokenSettings.id == 1).first()
    cost = settings.cost_ai_evaluation if settings else 50
    if user.tokens < cost:
        raise HTTPException(400, f"AI değerlendirme için {cost} token gerekli")

    job = db.query(JobListing).filter(
        JobListing.id == body.job_listing_id, JobListing.user_id == user.id
    ).first()
    if not job:
        raise HTTPException(404, "İş ilanı bulunamadı")

    ai_session = db.query(AISession).filter(
        AISession.user_id == user.id, AISession.is_logged_in == True
    ).first()
    if not ai_session:
        raise HTTPException(400, "Bir AI servisine giriş yapmalısınız (DeepSeek veya ChatGPT)")

    proxy = db.query(
        __import__("app.models.proxy_session", fromlist=["ProxySession"]).ProxySession
    ).filter_by(user_id=user.id, is_active=True).first()
    proxy_config = None
    if proxy:
        proxy_config = {
            "server": proxy.proxy_host,
            "port": proxy.proxy_port,
            "username": proxy.proxy_username,
            "password": proxy.proxy_password,
        }

    context = await create_browser_context(
        f"{user.id}_{ai_session.provider}_eval", proxy_config, ai_session.cookies
    )

    prompt = f"""CV:
{user.cv_text}

---
İş İlanı: {job.title} - {job.company}
{job.description}

---
Bu CV bu iş ilanına ne kadar uygun? 0-100 arası bir skor ver ve kısa bir analiz yaz.
Format: SKOR: [sayı]/100\nANALİZ: [metin]"""

    chat_url = "https://chat.deepseek.com" if ai_session.provider == "deepseek" else "https://chat.openai.com"
    page = await context.new_page()
    score = None
    analysis = None
    try:
        await page.goto(chat_url, wait_until="networkidle", timeout=30000)
        textarea = await page.wait_for_selector('textarea', timeout=10000)
        await textarea.fill(prompt)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(15000)

        response_el = await page.query_selector(".markdown-body, .prose, [data-message-author-role='assistant']")
        if response_el:
            text = await response_el.inner_text()
            import re
            score_match = re.search(r"SKOR:\s*(\d+)/100", text)
            analysis_match = re.search(r"ANALİZ:\s*(.+)", text, re.DOTALL)
            if score_match:
                score = float(score_match.group(1))
            if analysis_match:
                analysis = analysis_match.group(1).strip()[:1000]
    except Exception:
        pass
    finally:
        await page.close()

    if score is None:
        raise HTTPException(500, "AI yanıtı alınamadı, lütfen tekrar deneyin")

    job.ai_match_score = score
    job.ai_analysis = analysis
    user = db.merge(user)
    user.tokens -= cost
    tx = TokenTransaction(user_id=user.id, amount=-cost, reason=f"AI değerlendirme: {job.title}")
    db.add(tx)
    db.commit()

    return {
        "score": score,
        "analysis": analysis,
        "remaining_tokens": user.tokens,
    }
