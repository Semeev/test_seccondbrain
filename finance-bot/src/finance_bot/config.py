"""Bot configuration."""

import os
from pathlib import Path

BOT_TOKEN = os.environ["FINANCE_BOT_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY", "")

# Все разрешённые пользователи
ALLOWED_USERS: list[int] = [
    int(uid) for uid in os.environ.get("ALLOWED_USER_IDS", "").split(",") if uid.strip()
]

# Админы — могут использовать команды /today /week /month /last
ADMIN_USERS: list[int] = [
    int(uid) for uid in os.environ.get("ADMIN_USER_IDS", "").split(",") if uid.strip()
]

DB_PATH = Path(os.environ.get("FINANCE_DB_PATH", "/home/dbrain/finance-bot/data/finance.db"))
