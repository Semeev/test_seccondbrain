"""Handler for /vocalists command — sends PDF of vocalist database."""

import logging
import os

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from d_brain.config import get_settings

router = Router(name="vocalists")
logger = logging.getLogger(__name__)


@router.message(Command("vocalists"))
async def cmd_vocalists(message: Message) -> None:
    """Generate and send vocalist database as PDF."""
    await message.answer("⏳ Генерирую PDF...")

    try:
        settings = get_settings()
        from d_brain.services.pdf_vocalists import generate_vocalists_pdf
        pdf_path = generate_vocalists_pdf(settings.vault_path)

        pdf_bytes = pdf_path.read_bytes()
        os.unlink(pdf_path)  # cleanup temp file

        await message.answer_document(
            BufferedInputFile(pdf_bytes, filename="SunGroup_Vocalists.pdf"),
            caption="🎤 <b>База вокалистов SUN Group</b>",
        )

    except Exception as e:
        logger.exception("Failed to generate vocalists PDF")
        await message.answer(f"❌ Ошибка: {e}")
