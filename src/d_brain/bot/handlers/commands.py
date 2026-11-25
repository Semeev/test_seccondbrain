"""Command handlers for /start, /help, /status."""

from datetime import date

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from d_brain.bot.keyboards import (
    BTN_DO,
    BTN_PROCESS,
    BTN_STATUS,
    BTN_WEEKLY,
    get_main_keyboard,
)
from d_brain.config import get_settings
from d_brain.services.session import SessionStore
from d_brain.services.storage import VaultStorage

router = Router(name="commands")

MONTHS = (
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
)
WEEKDAYS = (
    "понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье",
)
TYPE_NAMES = {
    "voice": "голосовые",
    "text": "текст",
    "photo": "фото",
    "forward": "пересланные",
    "command": "команды",
}


def _human_date(day: date) -> str:
    """25 ноября, среда — easier to read than 2026-11-25."""
    return f"{day.day} {MONTHS[day.month - 1]}, {WEEKDAYS[day.weekday()]}"


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    await message.answer(
        "<b>Здравствуйте!</b>\n\n"
        "Я ваш помощник-дневник.\n"
        "Просто напишите мне или скажите голосом — я всё запишу.\n\n"
        "Можно присылать:\n"
        "• голосовые сообщения\n"
        "• текст\n"
        "• фотографии\n"
        "• пересланные сообщения\n\n"
        "Внизу экрана — большие кнопки.\n"
        "Нажмите <b>Помощь</b>, если что-то непонятно.",
        reply_markup=get_main_keyboard(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    await message.answer(
        "<b>Как пользоваться</b>\n\n"
        "<b>Записать мысль</b>\n"
        "Напишите или скажите голосом. Я сохраню.\n\n"
        f"<b>{BTN_STATUS}</b>\n"
        "Сколько записей сделано сегодня.\n\n"
        f"<b>{BTN_PROCESS}</b>\n"
        "Разложу записи по местам: мысли — в заметки, дела — в задачи. "
        "Удобно нажимать вечером.\n\n"
        f"<b>{BTN_WEEKLY}</b>\n"
        "Короткий рассказ о прошедшей неделе.\n\n"
        f"<b>{BTN_DO}</b>\n"
        "Попросите что угодно. Например:\n"
        "<i>перенеси просроченные дела на понедельник</i>",
        reply_markup=get_main_keyboard(),
    )


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    """Handle /status command."""
    user_id = message.from_user.id if message.from_user else 0
    settings = get_settings()
    storage = VaultStorage(settings.vault_path)

    # Log command
    session = SessionStore(settings.vault_path)
    session.append(user_id, "command", cmd="/status")

    today = date.today()
    content = storage.read_daily(today)

    if not content:
        await message.answer(f"<b>{_human_date(today)}</b>\n\nЗаписей пока нет.")
        return

    lines = content.strip().split("\n")
    entries = [line for line in lines if line.startswith("## ")]

    voice_count = sum(1 for e in entries if "[voice]" in e)
    text_count = sum(1 for e in entries if "[text]" in e)
    photo_count = sum(1 for e in entries if "[photo]" in e)
    forward_count = sum(1 for e in entries if "[forward from:" in e)

    total = len(entries)

    # Get weekly stats from session
    week_stats = ""
    stats = session.get_stats(user_id, days=7)
    if stats:
        week_stats = "\n\n<b>За 7 дней:</b>"
        for entry_type, count in sorted(stats.items()):
            week_stats += f"\n• {TYPE_NAMES.get(entry_type, entry_type)}: {count}"

    await message.answer(
        f"<b>{_human_date(today)}</b>\n\n"
        f"Всего записей: <b>{total}</b>\n\n"
        f"• Голосовых: {voice_count}\n"
        f"• Текстовых: {text_count}\n"
        f"• Фото: {photo_count}\n"
        f"• Пересланных: {forward_count}"
        f"{week_stats}"
    )
