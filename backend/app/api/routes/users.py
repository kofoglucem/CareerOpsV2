from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.base import get_db
from app.models.user import User
from app.models.job import TokenTransaction
from app.api.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


class UpdateCVRequest(BaseModel):
    cv_text: str


class UpdateLanguageRequest(BaseModel):
    language: str  # tr or en


@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "tokens": user.tokens,
        "role": user.role.value,
        "language": user.language,
        "has_cv": bool(user.cv_text),
        "created_at": user.created_at,
    }


@router.patch("/me/cv")
def update_cv(body: UpdateCVRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    user = db.merge(user)
    user.cv_text = body.cv_text
    db.commit()
    return {"message": "CV güncellendi" if user.language == "tr" else "CV updated"}


@router.patch("/me/language")
def update_language(
    body: UpdateLanguageRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if body.language not in ("tr", "en"):
        raise HTTPException(400, "Geçersiz dil seçeneği")
    user = db.merge(user)
    user.language = body.language
    db.commit()
    return {"message": "Dil güncellendi"}


@router.get("/me/transactions")
def get_my_transactions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    txs = (
        db.query(TokenTransaction)
        .filter(TokenTransaction.user_id == user.id)
        .order_by(TokenTransaction.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {"amount": t.amount, "reason": t.reason, "created_at": t.created_at}
        for t in txs
    ]
