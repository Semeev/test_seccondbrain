"""Main bot entry point."""

import asyncio
import logging
from datetime import date, time

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from finance_bot.config import BOT_TOKEN, ANTHROPIC_API_KEY, DB_PATH, ALLOWED_USERS
from finance_bot.storage import FinanceStorage
from finance_bot.services.claude import ExpenseParser
from finance_bot.reports import format_report
from finance_bot.handlers import text as text_handler
from finance_bot.handlers import voice as voice_handler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def send_report(bot: Bot, storage: FinanceStorage, report_type: str) -> None:
    """Send auto report to all allowed users."""
    for user_id in ALLOWED_USERS:
        try:
            if report_type == "weekly":
                records = storage.get_weekly(user_id)
                title = "Расходы за неделю"
            else:
                records = storage.get_monthly(user_id)
                title = f"Расходы за {date.today().strftime('%B')}"

            text = format_report(records, title)
            await bot.send_message(user_id, text, parse_mode="HTML")
        except Exception as e:
            logger.error("Failed to send report to %s: %s", user_id, e)


async def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    storage = FinanceStorage(DB_PATH)
    parser = ExpenseParser(ANTHROPIC_API_KEY)

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Pass dependencies via middleware data
    dp["storage"] = storage
    dp["parser"] = parser

    dp.include_router(text_handler.router)
    dp.include_router(voice_handler.router)

    # Scheduled reports
    scheduler = AsyncIOScheduler(timezone="Asia/Almaty")

    # Weekly report — Sunday at 21:00
    scheduler.add_job(
        send_report,
        "cron",
        day_of_week="sun",
        hour=21,
        minute=0,
        args=[bot, storage, "weekly"],
    )

    # Monthly report — last day of month at 21:00
    scheduler.add_job(
        send_report,
        "cron",
        day="last",
        hour=21,
        minute=0,
        args=[bot, storage, "monthly"],
    )

    scheduler.start()

    logger.info("Finance bot started")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
