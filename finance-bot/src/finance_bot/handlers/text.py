"""Text message handler."""

import logging
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from finance_bot.config import ALLOWED_USERS, ADMIN_USERS
from finance_bot.storage import FinanceStorage
from finance_bot.services.claude import ExpenseParser
from finance_bot.reports import format_report

logger = logging.getLogger(__name__)
router = Router()

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Сегодня"), KeyboardButton(text="📋 Последние")],
        [KeyboardButton(text="📅 Неделя"), KeyboardButton(text="🗓 Месяц")],
    ],
    resize_keyboard=True,
    persistent=True,
)


def _check_access(user_id: int) -> bool:
    return not ALLOWED_USERS or user_id in ALLOWED_USERS


def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_USERS


@router.message(F.text.startswith("/start"))
async def cmd_start(message: Message) -> None:
    if not _check_access(message.from_user.id):
        return
    await message.answer(
        "Привет! 👋\n\n"
        "Просто напиши или запиши голосом свой расход:\n"
        "<i>«потратила 5000 на ногти»</i>\n"
        "<i>«купила продукты 12000»</i>\n\n"
        "Я сам определю категорию и сохраню.",
        parse_mode="HTML",
        reply_markup=MAIN_KEYBOARD,
    )


@router.message(F.text.startswith("/today") | F.text == "📊 Сегодня")
async def cmd_today(message: Message, storage: FinanceStorage) -> None:
    if not _check_access(message.from_user.id):
        return
    records = storage.get_today(message.from_user.id)
    await message.answer(format_report(records, "Расходы сегодня"), parse_mode="HTML", reply_markup=MAIN_KEYBOARD)


@router.message(F.text.startswith("/last") | F.text == "📋 Последние")
async def cmd_last(message: Message, storage: FinanceStorage) -> None:
    if not _check_access(message.from_user.id):
        return
    records = storage.get_today(message.from_user.id)
    if not records:
        records = storage.get_weekly(message.from_user.id)
    if not records:
        await message.answer("Записей пока нет.", reply_markup=MAIN_KEYBOARD)
        return
    from finance_bot.categories import CATEGORIES
    lines = ["📋 <b>Последние записи:</b>\n"]
    for r in records[:10]:
        time = r["created_at"][11:16]
        cat = CATEGORIES.get(r["category"], r["category"])
        lines.append(f"{time} {cat} — <b>{r['amount']:,.0f} тг</b>")
    await message.answer("\n".join(lines), parse_mode="HTML", reply_markup=MAIN_KEYBOARD)


@router.message(F.text.startswith("/week") | F.text == "📅 Неделя")
async def cmd_week(message: Message, storage: FinanceStorage) -> None:
    if not _check_access(message.from_user.id):
        return
    records = storage.get_weekly(message.from_user.id)
    await message.answer(format_report(records, "Расходы за неделю"), parse_mode="HTML", reply_markup=MAIN_KEYBOARD)


@router.message(F.text.startswith("/month") | F.text == "🗓 Месяц")
async def cmd_month(message: Message, storage: FinanceStorage) -> None:
    if not _check_access(message.from_user.id):
        return
    records = storage.get_monthly(message.from_user.id)
    await message.answer(format_report(records, "Расходы за месяц"), parse_mode="HTML", reply_markup=MAIN_KEYBOARD)


@router.message(F.text)
async def handle_text(message: Message, storage: FinanceStorage, parser: ExpenseParser) -> None:
    if not _check_access(message.from_user.id):
        return

    text = message.text.strip()
    if text.startswith("/"):
        return

    await message.answer("⏳ Обрабатываю...")

    result = parser.parse(text)
    if not result:
        await message.answer("Не похоже на расход. Напиши как-то так: «потратила 3000 на еду»")
        return

    expense_id = storage.add_expense(
        user_id=message.from_user.id,
        amount=result["amount"],
        category=result["category"],
        description=result["description"],
        raw_text=text,
    )

    from finance_bot.categories import CATEGORIES
    cat_label = CATEGORIES.get(result["category"], result["category"])
    await message.answer(
        f"✅ Сохранено #{expense_id}\n"
        f"{cat_label}\n"
        f"<b>{result['amount']:,.0f} тг</b> — {result['description']}",
        parse_mode="HTML",
    )
