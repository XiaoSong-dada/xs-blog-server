import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from app.core.config import settings

async def send_mail(subject: str, content: str, to_email: str):
    sender = settings.EMAIL_SENDER
    password = settings.EMAIL_CODE

    msg = MIMEText(content, "plain", "utf-8")
    msg["From"] = formataddr((settings.EMAIL_FROM_NAME or "小宋博客", sender))
    msg["To"] = to_email
    msg["Subject"] = subject

    with smtplib.SMTP_SSL(
        settings.EMAIL_HOST,
        settings.EMAIL_PORT,
        timeout=10,
    ) as server:
        server.login(sender, password)
        server.sendmail(sender, [to_email], msg.as_string())
