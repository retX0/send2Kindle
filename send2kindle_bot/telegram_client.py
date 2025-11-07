"""Minimal Telegram Bot API client using the public HTTPS endpoints."""

from __future__ import annotations

import json
import logging
import shutil
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TelegramAPIError(RuntimeError):
    """Raised when the Telegram API returns an error response."""


class TelegramClient:
    def __init__(self, token: str) -> None:
        self._token = token
        self._api_base = f"https://api.telegram.org/bot{token}"
        self._file_base = f"https://api.telegram.org/file/bot{token}"

    def get_updates(self, offset: Optional[int], timeout: int = 30) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {"timeout": timeout}
        if offset is not None:
            payload["offset"] = offset
        result = self._request("getUpdates", payload)
        return result if isinstance(result, list) else []

    def send_message(self, chat_id: int, text: str) -> None:
        self._request("sendMessage", {"chat_id": chat_id, "text": text})

    def send_chat_action(self, chat_id: int, action: str) -> None:
        self._request("sendChatAction", {"chat_id": chat_id, "action": action})

    def get_file(self, file_id: str) -> Dict[str, Any]:
        result = self._request("getFile", {"file_id": file_id})
        if not isinstance(result, dict):
            raise TelegramAPIError("Unexpected getFile response format")
        return result

    def download_file(self, file_path: str, destination: Path) -> None:
        url = f"{self._file_base}/{file_path}"
        try:
            with urllib.request.urlopen(url, timeout=120) as response, destination.open(
                "wb"
            ) as file_obj:
                shutil.copyfileobj(response, file_obj)
        except urllib.error.URLError as exc:  # pragma: no cover - network
            raise TelegramAPIError("Failed to download Telegram file") from exc

    def _request(self, method: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self._api_base}/{method}"
        data = json.dumps(payload or {}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                parsed = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:  # pragma: no cover - network
            logger.error(
                "Telegram API HTTP error on %s: %s %s",
                method,
                exc.code,
                exc.reason,
            )
            raise TelegramAPIError(f"HTTP error calling {method}") from exc
        except urllib.error.URLError as exc:  # pragma: no cover - network
            raise TelegramAPIError(f"Network error calling {method}") from exc

        if not isinstance(parsed, dict) or not parsed.get("ok"):
            description = parsed.get("description") if isinstance(parsed, dict) else ""
            raise TelegramAPIError(f"Telegram API error on {method}: {description}")

        return parsed.get("result")
