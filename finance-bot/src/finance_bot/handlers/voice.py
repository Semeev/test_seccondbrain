"""Voice message handler."""

import logging
import tempfile
from pathlib import Path

import httpx
from aiogram import Router, F
from aiogram.types import Message

from finance_bot.config import ALLOWED_USERS, DEEPGRAM_API_KEY
from finance_bot.storage import FinanceStorage
from finance_bot.services.claude import ExpenseParser
from finance_bot.categories import CATEGORIES

logger = logging.getLogger(__name__)
router = Router()


def _check_access(user_id: int) -> bool:
    return not ALLOWED_USERS or user_id in ALLOWED_USERS


async def _transcribe(ogg_path: Path) -> str | None:
    """Transcribe audio via Deepgram API."""
    if not DEEPGRAM_API_KEY:
        return None

    url = "https://api.deepgram.com/v1/listen?language=ru&model=nova-2"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "audio/ogg",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        with open(ogg_path, "rb") as f:
            resp = await client.post(url, headers=headers, content=f.read())
        resp.raise_for_status()
        data = resp.json()
        return data["results"]["channels"][0]["alternatives"][0]["transcript"]


@router.message(F.voice)
async def handle_voice(message: Message, storage: FinanceStorage, parser: ExpenseParser) -> None:
    if not _check_access(message.from_user.id):
        return

    if not DEEPGRAM_API_KEY:
        await message.answer("Голосовые сообщения не настроены. Напиши текстом.")
        return

    await message.answer("🎤 Слушаю...")

    # Download voice file
    voice = message.voice
    bot = message.bot
    file = await bot.get_file(voice.file_id)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    await bot.download_file(file.file_path, destination=str(tmp_path))

    try:
        text = await _transcribe(tmp_path)
    except Exception as e:
        logger.error("Transcription error: %s", e)
        await message.answer("Не смогла распознать голос. Попробуй написать текстом.")
        return
    finally:
        tmp_path.unlink(missing_ok=True)

    if not text or not text.strip():
        await message.answer("Ничего не услышала. Попробуй ещё раз.")
        return

    await message.answer(f"📝 Распознала: <i>{text}</i>", parse_mode="HTML")

    result = parser.parse(text)
    if not result:
        await message.answer("Не похоже на расход. Скажи как-то так: «потратила три тысячи на еду»")
        return

    from finance_bot.currency import fmt, to_kzt
    currency = result.get("currency", "KZT").upper()

    expense_id = storage.add_record(
        user_id=message.from_user.id,
        record_type=result.get("type", "expense"),
        amount=result["amount"],
        category=result["category"],
        description=result["description"],
        raw_text=text,
        currency=currency,
    )

    cat_label = CATEGORIES.get(result["category"], result["category"])
    amount_str = fmt(result["amount"], currency)
    if currency != "KZT":
        amount_str += f" ≈ {to_kzt(result['amount'], currency):,.0f} тг"
    await message.answer(
        f"✅ Сохранено #{expense_id}\n"
        f"{cat_label}\n"
        f"<b>{amount_str}</b> — {result['description']}",
        parse_mode="HTML",
    )
