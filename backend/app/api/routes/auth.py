from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.models.base import get_db
from app.models.user import User, UserRole
from app.core.security import hash_password, verify_password, create_access_token, decode_token
from app.services.email import send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    language: str = "tr"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(400, "Bu e-posta zaten kayıtlı / Email already registered")
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(400, "Bu kullanıcı adı alınmış / Username already taken")

    user = User(
        email=body.email,
        username=body.username,
        hashed_password=hash_password(body.password),
        language=body.language,
        is_active=False,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    try:
        await send_verification_email(body.email, body.username, body.language)
    except Exception:
        # SMTP not configured — activate user directly so system is usable without email setup
        user.is_verified = True
        user.is_active = True
        db.commit()
        return {"message": "Kayıt başarılı. (E-posta servisi yapılandırılmamış, hesap otomatik aktifleştirildi.)" if body.language == "tr" else "Registered. (Email service not configured, account activated automatically.)"}
    return {"message": "Kayıt başarılı. E-postanızı kontrol edin." if body.language == "tr" else "Registered. Check your email."}


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    payload = decode_token(token)
    if not payload or payload.get("type") != "verify":
        raise HTTPException(400, "Geçersiz veya süresi dolmuş token")
    user = db.query(User).filter(User.email == payload["sub"]).first()
    if not user:
        raise HTTPException(404, "Kullanıcı bulunamadı")
    user.is_verified = True
    user.is_active = True
    db.commit()
    return {"message": "E-posta doğrulandı." if user.language == "tr" else "Email verified."}


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(401, "Geçersiz kimlik bilgileri")
    if not user.is_verified:
        raise HTTPException(403, "E-postanızı doğrulayın")
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return {"access_token": token}
