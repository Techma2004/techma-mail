import re
from email.message import EmailMessage
from email.utils import parseaddr
from uuid import uuid4
import aiosmtplib
from app.config import Settings
from app.schemas import EmailRequest

class MailDeliveryError(Exception):
    pass

def parse_sender(value: str) -> tuple[str, str]:
    name, address = parseaddr(value)
    if not address or "@" not in address:
        raise ValueError("Invalid sender address")
    return name, address

async def send_email(payload: EmailRequest, settings: Settings) -> str:
    display_name, sender = parse_sender(payload.from_)
    domain = sender.rsplit("@", 1)[1].lower()
    if settings.from_domains and domain not in settings.from_domains:
        raise ValueError("Sender domain is not in ALLOWED_FROM_DOMAINS")

    message = EmailMessage()
    message["From"] = payload.from_ if display_name else f"{settings.smtp_from_name} <{sender}>"
    message["To"] = ", ".join(payload.as_list(payload.to))
    if payload.cc:
        message["Cc"] = ", ".join(payload.as_list(payload.cc))
    message["Subject"] = payload.subject
    if payload.reply_to_list:
        message["Reply-To"] = ", ".join(payload.reply_to_list)
    for key, value in (payload.headers or {}).items():
        # Avoid overriding transport and routing headers.
        if key.lower() not in {"from", "to", "cc", "bcc", "subject", "reply-to", "received"}:
            message[key] = value[:500]

    if payload.text is not None:
        message.set_content(payload.text)
    else:
        message.set_content("This message contains HTML content. Please view it in an HTML-capable email client.")
    if payload.html is not None:
        message.add_alternative(payload.html, subtype="html")

    recipients = payload.recipients
    try:
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            use_tls=settings.smtp_use_tls,
            start_tls=settings.smtp_start_tls,
            timeout=settings.smtp_timeout_seconds,
            recipients=recipients,
        )
    except Exception as exc:
        # Do not leak SMTP credentials or provider internals to API clients.
        raise MailDeliveryError("SMTP provider rejected or could not accept the message") from exc
    return f"email_{uuid4().hex}"
