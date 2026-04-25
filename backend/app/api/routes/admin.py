from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from app.models.base import get_db
from app.models.user import User
from app.models.job import TokenTransaction, TokenSettings
from app.api.deps import require_admin
import uuid

router = APIRouter(prefix="/admin", tags=["admin"])


class AddTokensRequest(BaseModel):
    user_id: str
    amount: int
    reason: str = "Admin tarafından yüklendi"


class UpdateTokenSettingsRequest(BaseModel):
    cost_residential_ip: int | None = None
    cost_search_2h: int | None = None
    cost_ai_evaluation: int | None = None


@router.get("/users")
def list_users(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    users = db.query(User).all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "username": u.username,
            "tokens": u.tokens,
            "is_active": u.is_active,
            "is_verified": u.is_verified,
            "role": u.role.value,
            "created_at": u.created_at,
        }
        for u in users
    ]


@router.post("/tokens/add")
def add_tokens(body: AddTokensRequest, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(404, "Kullanıcı bulunamadı")
    user.tokens += body.amount
    tx = TokenTransaction(
        user_id=user.id,
        admin_id=admin.id,
        amount=body.amount,
        reason=body.reason,
    )
    db.add(tx)
    db.commit()
    return {"message": f"{body.amount} token yüklendi", "new_balance": user.tokens}


@router.get("/tokens/settings")
def get_token_settings(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    settings = db.query(TokenSettings).filter(TokenSettings.id == 1).first()
    if not settings:
        settings = TokenSettings(id=1)
        db.add(settings)
        db.commit()
    return {
        "cost_residential_ip": settings.cost_residential_ip,
        "cost_search_2h": settings.cost_search_2h,
        "cost_ai_evaluation": settings.cost_ai_evaluation,
    }


@router.patch("/tokens/settings")
def update_token_settings(
    body: UpdateTokenSettingsRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    settings = db.query(TokenSettings).filter(TokenSettings.id == 1).first()
    if not settings:
        settings = TokenSettings(id=1)
        db.add(settings)
    if body.cost_residential_ip is not None:
        settings.cost_residential_ip = body.cost_residential_ip
    if body.cost_search_2h is not None:
        settings.cost_search_2h = body.cost_search_2h
    if body.cost_ai_evaluation is not None:
        settings.cost_ai_evaluation = body.cost_ai_evaluation
    db.commit()
    return {"message": "Token ayarları güncellendi"}


@router.get("/transactions")
def list_transactions(
    user_id: str | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    q = db.query(TokenTransaction)
    if user_id:
        q = q.filter(TokenTransaction.user_id == user_id)
    txs = q.order_by(TokenTransaction.created_at.desc()).limit(100).all()
    return [
        {
            "id": str(t.id),
            "user_id": str(t.user_id),
            "admin_id": str(t.admin_id) if t.admin_id else None,
            "amount": t.amount,
            "reason": t.reason,
            "created_at": t.created_at,
        }
        for t in txs
    ]
