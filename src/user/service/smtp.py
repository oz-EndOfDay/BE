import smtplib
from email.mime.text import MIMEText

from src.config import Settings

settings = Settings()


async def send_email(to: str, subject: str, body: str) -> None:
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = "devmon724@gmail.com"
    msg["To"] = to

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login("devmon724@gmail.com", settings.EMAIL_PASSWORD)
        server.send_message(msg)
