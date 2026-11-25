"""Voice message handler."""

import asyncio
import html
import logging
from datetime import datetime

from aiogram import Bot, Router
from aiogram.types import Message

from d_brain.bot.formatters import format_error
from d_brain.config import get_settings
from d_brain.services.git import VaultGit
from d_brain.services.session import SessionStore
from d_brain.services.storage import VaultStorage
from d_brain.services.transcription import DeepgramTranscriber

router = Router(name="voice")
logger = logging.getLogger(__name__)


@router.message(lambda m: m.voice is not None)
async def handle_voice(message: Message, bot: Bot) -> None:
    """Handle voice messages."""
    if not message.voice or not message.from_user:
        return

    await message.chat.do(action="typing")

    settings = get_settings()
    storage = VaultStorage(settings.vault_path)
    transcriber = DeepgramTranscriber(settings.deepgram_api_key)

    try:
        file = await bot.get_file(message.voice.file_id)
        if not file.file_path:
            await message.answer("Не получилось получить голосовое. Попробуйте ещё раз.")
            return

        file_bytes = await bot.download_file(file.file_path)
        if not file_bytes:
            await message.answer("Не получилось получить голосовое. Попробуйте ещё раз.")
            return

        audio_bytes = file_bytes.read()
        transcript = await transcriber.transcribe(audio_bytes)

        if not transcript:
            await message.answer("Не получилось разобрать слова. Попробуйте сказать ещё раз.")
            return

        timestamp = datetime.fromtimestamp(message.date.timestamp())
        storage.append_to_daily(transcript, timestamp, "[voice]")

        # Log to session
        session = SessionStore(settings.vault_path)
        session.append(
            message.from_user.id,
            "voice",
            text=transcript,
            duration=message.voice.duration,
            msg_id=message.message_id,
        )

        # Push to GitHub in background
        git = VaultGit(settings.vault_path)
        asyncio.create_task(asyncio.to_thread(git.commit_and_push, "chore: add voice entry"))

        await message.answer(f"<b>Сохранено.</b>\n\n{html.escape(transcript)}")
        logger.info("Voice message saved: %d chars", len(transcript))

    except Exception as e:
        logger.exception("Error processing voice message")
        await message.answer(format_error(str(e)))
