"""SMTP utilities for delivering files to Kindle mailboxes."""

from __future__ import annotations

import mimetypes
import smtplib
from email.message import EmailMessage
from pathlib import Path

from .config import Settings


def send_file_via_email(settings: Settings, file_path: Path, display_name: str) -> None:
    """Send the provided file to the configured Kindle inbox."""

    mime_type, _ = mimetypes.guess_type(display_name)
    maintype, subtype = (mime_type or "application/octet-stream").split("/", maxsplit=1)

    msg = EmailMessage()
    msg["Subject"] = settings.email_subject
    msg["From"] = settings.smtp_from_email
    msg["To"] = settings.kindle_recipient_email
    msg.set_content("Sent via Telegram Send2Kindle bot.")

    msg.add_attachment(
        file_path.read_bytes(),
        maintype=maintype,
        subtype=subtype,
        filename=display_name,
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        if settings.smtp_starttls:
            server.starttls()
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)
