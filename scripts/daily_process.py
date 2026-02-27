#!/usr/bin/env python
"""Daily process script."""
import asyncio, logging, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Extend PATH so claude/uv are found when run from systemd
home = Path.home()
for p in [home / ".local/bin", Path("/usr/local/bin")]:
    if str(p) not in os.environ.get("PATH", ""):
        os.environ["PATH"] = str(p) + ":" + os.environ.get("PATH", "")

# Load .env explicitly before Settings (pydantic-settings also searches cwd)
_project_dir = Path(__file__).parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(_project_dir / ".env", override=False)
except ImportError:
    pass

from datetime import date
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from d_brain.config import get_settings
from d_brain.services.git import VaultGit
from d_brain.services.processor import ClaudeProcessor

async def main():
    settings = get_settings()
    processor = ClaudeProcessor(settings.vault_path, settings.todoist_api_key)
    git = VaultGit(settings.vault_path)
    result = processor.process_daily(date.today())
    if 'error' in result:
        report = f'❌ Ошибка: {result["error"]}'
    else:
        report = result.get('report', 'No output')
        git.commit_and_push(f'chore: process daily {date.today()}')
    bot = Bot(token=settings.telegram_bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        user_id = settings.allowed_user_ids[0]
        try:
            await bot.send_message(chat_id=user_id, text=report)
        except Exception:
            await bot.send_message(chat_id=user_id, text=report, parse_mode=None)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())
