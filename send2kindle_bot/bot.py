"""Telegram bot entrypoint for forwarding files to Kindle."""

from __future__ import annotations

import logging
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

from .config import Settings
from .mailer import send_file_via_email
from .telegram_client import TelegramAPIError, TelegramClient

logger = logging.getLogger(__name__)

WELCOME_MESSAGE = (
    "Send me the document you want on your Kindle.\n"
    "I will forward most common formats via email to your Kindle inbox."
)

HELP_MESSAGE = (
    "This bot forwards any document you send to your Kindle email address.\n"
    "Usage:\n"
    "1. Send /start to confirm I am online.\n"
    "2. Upload a supported document (PDF/EPUB/DOCX/etc.).\n"
    "3. Wait a few minutes for Amazon to deliver it to your Kindle."
)


def _is_authorized(settings: Settings, user_id: Optional[int]) -> bool:
    return bool(user_id and user_id in settings.allowed_user_ids)


def _get_chat_id(message: Dict[str, Any]) -> Optional[int]:
    chat = message.get("chat")
    chat_id = chat.get("id") if isinstance(chat, dict) else None
    return chat_id if isinstance(chat_id, int) else None


def _get_user_id(message: Dict[str, Any]) -> Optional[int]:
    user = message.get("from")
    user_id = user.get("id") if isinstance(user, dict) else None
    return user_id if isinstance(user_id, int) else None


def _send_start_message(client: TelegramClient, chat_id: int) -> None:
    client.send_message(chat_id, WELCOME_MESSAGE)


def _send_unauthorized(client: TelegramClient, chat_id: Optional[int]) -> None:
    if chat_id is not None:
        client.send_message(chat_id, "Sorry, you are not allowed to use this bot.")


def _send_help_message(client: TelegramClient, chat_id: int) -> None:
    client.send_message(chat_id, HELP_MESSAGE)


def _handle_document(
    settings: Settings,
    client: TelegramClient,
    chat_id: int,
    document: Dict[str, Any],
) -> None:
    file_id = document.get("file_id")
    if not isinstance(file_id, str):
        client.send_message(chat_id, "Could not read the file ID, please try again.")
        return

    file_name = document.get("file_name") or "document.bin"
    suffix = Path(file_name).suffix or ".bin"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        client.send_chat_action(chat_id, "upload_document")
        file_info = client.get_file(file_id)
        file_path = file_info.get("file_path") if isinstance(file_info, dict) else None
        if not isinstance(file_path, str):
            raise TelegramAPIError("Missing file_path in Telegram response")

        client.download_file(file_path, temp_path)
        send_file_via_email(settings, temp_path, file_name)
        client.send_message(chat_id, "Your file is on its way to your Kindle inbox.")
    except Exception:
        logger.exception("Failed to forward file for chat %s", chat_id)
        client.send_message(chat_id, "Something went wrong. Please try again later.")
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except Exception:
            logger.warning("Could not delete temporary file %s", temp_path)


def _process_message(settings: Settings, client: TelegramClient, message: Dict[str, Any]) -> None:
    chat_id = _get_chat_id(message)
    user_id = _get_user_id(message)
    if chat_id is None:
        return

    if not _is_authorized(settings, user_id):
        _send_unauthorized(client, chat_id)
        return

    text = message.get("text")
    if isinstance(text, str):
        if text.startswith("/start"):
            _send_start_message(client, chat_id)
            return
        if text.startswith("/help"):
            _send_help_message(client, chat_id)
            return

    document = message.get("document")
    if isinstance(document, dict):
        _handle_document(settings, client, chat_id, document)


def run_bot() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        level=logging.INFO,
    )

    settings = Settings.load()
    client = TelegramClient(settings.telegram_bot_token)
    offset: Optional[int] = None

    logger.info("Bot ready for %d authorized users", len(settings.allowed_user_ids))

    try:
        while True:
            try:
                updates = client.get_updates(offset=offset, timeout=40)
            except TelegramAPIError:
                logger.exception("Failed to fetch updates, retrying shortly")
                time.sleep(5)
                continue

            for update in updates:
                update_id = update.get("update_id")
                if isinstance(update_id, int):
                    next_offset = update_id + 1
                    offset = next_offset if offset is None or next_offset > offset else offset

                message = update.get("message")
                if isinstance(message, dict):
                    try:
                        _process_message(settings, client, message)
                    except Exception:
                        logger.exception("Failed to process message for update %s", update_id)
                        chat_id = _get_chat_id(message)
                        if chat_id is not None:
                            client.send_message(chat_id, "Unexpected error handling your message.")

    except KeyboardInterrupt:
        logger.info("Bot stopped via keyboard interrupt")


if __name__ == "__main__":
    run_bot()
