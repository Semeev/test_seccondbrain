"""Claude service for parsing expenses."""

import json
import logging
import anthropic

from finance_bot.categories import CATEGORIES, CATEGORIES_FOR_PROMPT

logger = logging.getLogger(__name__)


class ExpenseParser:
    def __init__(self, api_key: str) -> None:
        self.client = anthropic.Anthropic(api_key=api_key)

    def parse(self, text: str) -> dict | None:
        """Parse expense from text. Returns {amount, category, description} or None."""
        prompt = f"""Из текста извлеки расход. Ответь ТОЛЬКО JSON без пояснений.

Текст: "{text}"

Категории:
{CATEGORIES_FOR_PROMPT}

JSON формат:
{{"amount": число, "category": "ключ_категории", "description": "краткое описание"}}

Если это не расход — верни: {{"amount": 0, "category": "", "description": ""}}
Если сумма не указана — попробуй угадать или верни amount: 0."""

        try:
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            # Убираем markdown если есть
            raw = raw.replace("```json", "").replace("```", "").strip()
            data = json.loads(raw)
            if data.get("amount", 0) > 0 and data.get("category"):
                return data
            return None
        except Exception as e:
            logger.error("Claude parse error: %s", e)
            return None
