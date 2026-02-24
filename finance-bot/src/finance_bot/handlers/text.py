"""Text message handler."""

import logging
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, BufferedInputFile

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
        [KeyboardButton(text="📈 График недели"), KeyboardButton(text="📈 График месяца")],
        [KeyboardButton(text="↩️ Отменить последнее"), KeyboardButton(text="📖 Категории")],
    ],
    resize_keyboard=True,
    persistent=True,
)

CATEGORIES_HELP = """📖 <b>Как записывать расходы:</b>

Просто напиши <b>сумму + что</b>, например:
<i>«15 000 на такси»</i> или <i>«8 000 стики»</i>

<b>💆 Бьюти</b>
• косметолог, ногти, ресницы, волосы
• макияж, лазер, массаж, процедура

<b>🧴 Косметика</b>
• тушь, помада, тональный, пудра (декор)
• крем, сыворотка, уходовая (уход)

<b>🛒 Покупки</b>
• продукты, базар — еда домой
• вещи, одежда, обувь
• для дома, посуда
• техника, телефон, гаджет
• золото, украшение, кольцо

<b>👶 Селин</b>
• вещи для Селин, игрушка
• няня, садик, курсы Селин

<b>🏠 Дом</b>
• аренда, за квартиру
• ремонт
• коммуналка, свет, вода, интернет

<b>🚗 Транспорт</b>
• бензин, заправила, зарядка машины
• такси, доехала на такси, на дорогу

<b>🚬 Айкос</b>
• стики, heets, айкос

<b>🍽 Еда вне дома</b>
• кафе, ресторан, кофейня, бизнес-ланч
• пицца, суши, бургер, доставка еды

<b>🎉 Прочее</b>
• тусовка, отпуск, путешествие
• книга, курс (саморазвитие)
• для Джона, маме
• собака, кот
• благотворительность, садака

<b>📈 Доходы</b>
• дал муж, подарок, возврат долга
• за услуги, фриланс"""


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


@router.message(F.text == "↩️ Отменить последнее")
async def cmd_undo(message: Message, storage: FinanceStorage) -> None:
    if not _check_access(message.from_user.id):
        return
    record = storage.delete_last(message.from_user.id)
    if not record:
        await message.answer("Нечего отменять.", reply_markup=MAIN_KEYBOARD)
        return
    from finance_bot.categories import CATEGORIES, INCOME_CATEGORIES
    all_cats = {**CATEGORIES, **INCOME_CATEGORIES}
    cat_label = all_cats.get(record["category"], record["category"])
    rtype = record.get("type", "expense")
    icon = "📈" if rtype == "income" else "📉"
    await message.answer(
        f"↩️ Удалено #{record['id']}\n{icon} {cat_label} — <b>{record['amount']:,.0f} тг</b>",
        parse_mode="HTML",
        reply_markup=MAIN_KEYBOARD,
    )


@router.message(F.text == "📖 Категории")
async def cmd_categories(message: Message) -> None:
    if not _check_access(message.from_user.id):
        return
    await message.answer(CATEGORIES_HELP, parse_mode="HTML", reply_markup=MAIN_KEYBOARD)


@router.message(F.text.startswith("/chart_week") | F.text == "📈 График недели")
async def cmd_chart_week(message: Message, storage: FinanceStorage) -> None:
    if not _check_access(message.from_user.id):
        return
    from finance_bot.charts import generate_chart
    records = storage.get_weekly(message.from_user.id)
    text = generate_chart(records, "📈 Расходы за неделю")
    if not text:
        await message.answer("Нет данных за неделю.", reply_markup=MAIN_KEYBOARD)
        return
    await message.answer(text, parse_mode="HTML", reply_markup=MAIN_KEYBOARD)


@router.message(F.text.startswith("/chart_month") | F.text == "📈 График месяца")
async def cmd_chart_month(message: Message, storage: FinanceStorage) -> None:
    if not _check_access(message.from_user.id):
        return
    from finance_bot.charts import generate_chart
    records = storage.get_monthly(message.from_user.id)
    text = generate_chart(records, "📈 Расходы за месяц")
    if not text:
        await message.answer("Нет данных за месяц.", reply_markup=MAIN_KEYBOARD)
        return
    await message.answer(text, parse_mode="HTML", reply_markup=MAIN_KEYBOARD)


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
        await message.answer("Не похоже на финансовую операцию. Напиши как-то так: «потратила 3000 на еду» или «получила зарплату 150000»")
        return

    record_id = storage.add_record(
        user_id=message.from_user.id,
        record_type=result["type"],
        amount=result["amount"],
        category=result["category"],
        description=result["description"],
        raw_text=text,
    )

    from finance_bot.categories import CATEGORIES, INCOME_CATEGORIES
    is_income = result["type"] == "income"
    all_cats = {**CATEGORIES, **INCOME_CATEGORIES}
    cat_label = all_cats.get(result["category"], result["category"])
    sign = "+" if is_income else "-"
    icon = "📈" if is_income else "📉"

    await message.answer(
        f"{icon} Сохранено #{record_id}\n"
        f"{cat_label}\n"
        f"<b>{sign}{result['amount']:,.0f} тг</b> — {result['description']}",
        parse_mode="HTML",
        reply_markup=MAIN_KEYBOARD,
    )
