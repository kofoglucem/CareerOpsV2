import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
from app.core.security import create_access_token
from datetime import timedelta


def create_verification_token(email: str) -> str:
    return create_access_token({"sub": email, "type": "verify"}, timedelta(hours=24))


def create_password_reset_token(email: str) -> str:
    return create_access_token({"sub": email, "type": "reset"}, timedelta(hours=1))


async def send_email(to: str, subject: str, html: str):
    message = MIMEMultipart("alternative")
    message["From"] = settings.EMAIL_FROM
    message["To"] = to
    message["Subject"] = subject
    message.attach(MIMEText(html, "html"))

    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=True,
    )


async def send_verification_email(email: str, username: str, lang: str = "tr"):
    token = create_verification_token(email)
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    if lang == "tr":
        subject = "CareerOpsV2 - E-posta Doğrulama"
        html = f"""
        <h2>Merhaba {username},</h2>
        <p>Hesabınızı doğrulamak için aşağıdaki bağlantıya tıklayın:</p>
        <a href="{verify_url}" style="background:#2563eb;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;display:inline-block;">
            E-postayı Doğrula
        </a>
        <p>Bu bağlantı 24 saat geçerlidir.</p>
        """
    else:
        subject = "CareerOpsV2 - Email Verification"
        html = f"""
        <h2>Hello {username},</h2>
        <p>Click the link below to verify your account:</p>
        <a href="{verify_url}" style="background:#2563eb;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;display:inline-block;">
            Verify Email
        </a>
        <p>This link is valid for 24 hours.</p>
        """
    await send_email(email, subject, html)
