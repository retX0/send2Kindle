# Send2Kindle Telegram Bot

This repository contains a lightweight Telegram bot that forwards any document you send to your Kindle email address via SMTP. Only approved Telegram user IDs can interact with the bot.

## Features

- Whitelist enforcement through the `ALLOWED_TELEGRAM_IDS` environment variable.
- Handles Telegram `Document` uploads (PDF, EPUB, DOCX, etc.).
- Streams files to a temporary path and emails them as attachments to Kindle.
- Pure standard-library implementation (no third-party packages required).

## Prerequisites

- Python 3.10 or newer.
- Telegram Bot Token from [@BotFather](https://t.me/BotFather).
- SMTP account that can send email (Gmail, Outlook, SES, etc.).
- Kindle settings updated to approve the SMTP sender address under **Personal Document Settings**.

## Setup

1. (Optional) Install [uv](https://docs.astral.sh/uv/) for reproducible virtual environments:

   ```bash
   uv sync
   ```

   The project has zero dependencies, so you can also run it directly with the system interpreter if you prefer.

2. Copy the sample environment file and fill in real values:

   ```bash
   cp .env.example .env
   ```

   Required keys:

   - `TELEGRAM_BOT_TOKEN` – Bot token from BotFather.
   - `ALLOWED_TELEGRAM_IDS` – Comma-separated list of Telegram user IDs who can use the bot.
   - `SMTP_*` – SMTP host, port, username, password, TLS flag, and sender address.
   - `KINDLE_RECIPIENT_EMAIL` – Your Kindle address (e.g., `name@kindle.com`).
   - `EMAIL_SUBJECT` – Optional subject. Keep `convert` to ask Amazon to convert formats automatically.

## Running the Bot

```bash
uv run python -m send2kindle_bot.bot
# or, if you skipped uv:
python -m send2kindle_bot.bot
```

The bot uses long polling against the Telegram HTTP API. Only users listed in `ALLOWED_TELEGRAM_IDS` can issue `/start`, `/help`, or upload documents.

## Usage Flow

1. Send `/start` to receive a welcome message.
2. Optionally run `/help` for a short tutorial.
3. Upload a document; the bot will download it, send it via SMTP, and confirm delivery.

## Troubleshooting

- **Nothing arrives on Kindle** – Verify the sender email is approved in Amazon settings and that the attachment is under the ~50 MB limit.
- **SMTP authentication fails** – Check for app-specific passwords or two-factor requirements from your provider.
- **New users need access** – Edit `ALLOWED_TELEGRAM_IDS` in `.env` and restart the bot.

## Project Structure

- `send2kindle_bot/telegram_client.py` – Minimal wrapper around Telegram’s HTTPS Bot API.
- `send2kindle_bot/bot.py` – Authorization, command handling, and document workflow.
- `send2kindle_bot/mailer.py` – SMTP helper that builds and sends MIME messages.
- `send2kindle_bot/config.py` – Environment loader and validation helpers.

## Security Notes

- Never commit `.env` or credentials to version control.
- Keep your `.env` readable only by trusted users if deployed on shared hosts.
- When running in production, wrap the bot in a process manager (systemd, Docker, etc.) and monitor logs for failures.
