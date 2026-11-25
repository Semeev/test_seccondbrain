"""Reply keyboards for Telegram bot.

Design: large, calm buttons that are easy to read and hard to miss.
- Two buttons per row at most, so each button is wide.
- resize_keyboard=False: Telegram stretches the buttons to the full
  keyboard height, so they become noticeably taller.
- Plain words instead of colourful emoji.
"""

from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

BTN_STATUS = "Сегодня"
BTN_PROCESS = "Разобрать записи"
BTN_WEEKLY = "Итоги недели"
BTN_DO = "Задать вопрос"
BTN_HELP = "Помощь"

# Old labels, so keyboards already shown to the user keep working
# until Telegram replaces them with the new one.
LEGACY_LABELS = {
    BTN_STATUS: "📊 Статус",
    BTN_PROCESS: "⚙️ Обработать",
    BTN_WEEKLY: "📅 Неделя",
    BTN_DO: "✨ Запрос",
    BTN_HELP: "❓ Помощь",
}


def labels(button: str) -> set[str]:
    """All texts (new and legacy) that trigger the given button."""
    return {button, LEGACY_LABELS[button]}


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Main reply keyboard: 2 + 2 + 1 large buttons."""
    builder = ReplyKeyboardBuilder()
    builder.button(text=BTN_STATUS)
    builder.button(text=BTN_WEEKLY)
    builder.button(text=BTN_PROCESS)
    builder.button(text=BTN_DO)
    builder.button(text=BTN_HELP)
    builder.adjust(2, 2, 1)
    return builder.as_markup(
        resize_keyboard=False,
        is_persistent=True,
        input_field_placeholder="Напишите или скажите голосом…",
    )
