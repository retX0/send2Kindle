"""Configuration loading utilities for the Send2Kindle bot."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class Settings:
    telegram_bot_token: str
    allowed_user_ids: List[int]
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_starttls: bool
    smtp_from_email: str
    kindle_recipient_email: str
    email_subject: str

    @classmethod
    def load(cls) -> "Settings":
        _load_env_file()

        token = _require("TELEGRAM_BOT_TOKEN")
        allowed = _parse_allowed_users(_require("ALLOWED_TELEGRAM_IDS"))
        smtp_host = _require("SMTP_HOST")
        smtp_port = int(_require("SMTP_PORT"))
        smtp_username = _require("SMTP_USERNAME")
        smtp_password = _require("SMTP_PASSWORD")
        smtp_starttls = _parse_bool(os.getenv("SMTP_STARTTLS", "true"))
        smtp_from_email = _require("SMTP_FROM_EMAIL")
        kindle_recipient_email = _require("KINDLE_RECIPIENT_EMAIL")
        email_subject = os.getenv("EMAIL_SUBJECT", "convert")

        return cls(
            telegram_bot_token=token,
            allowed_user_ids=allowed,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            smtp_starttls=smtp_starttls,
            smtp_from_email=smtp_from_email,
            kindle_recipient_email=kindle_recipient_email,
            email_subject=email_subject,
        )


def _require(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value.strip()


def _parse_allowed_users(value: str) -> List[int]:
    ids: List[int] = []
    for chunk in value.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            ids.append(int(chunk))
        except ValueError as exc:  # pragma: no cover - defensive
            raise RuntimeError(
                f"Invalid Telegram user id '{chunk}' in ALLOWED_TELEGRAM_IDS"
            ) from exc
    if not ids:
        raise RuntimeError("ALLOWED_TELEGRAM_IDS must list at least one id")
    return ids


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_env_file(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = _strip_quotes(value.strip())


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value
