"""Claude service for parsing expenses and income."""

import json
import logging
import anthropic

from finance_bot.categories import CATEGORIES, CATEGORIES_FOR_PROMPT, INCOME_CATEGORIES_FOR_PROMPT

logger = logging.getLogger(__name__)


class ExpenseParser:
    def __init__(self, api_key: str) -> None:
        self.client = anthropic.Anthropic(api_key=api_key)

    def parse(self, text: str) -> dict | None:
        """Parse expense or income from text.
        Returns {type, amount, category, description} or None.
        """
        prompt = f"""Из текста извлеки финансовую операцию. Ответь ТОЛЬКО JSON без пояснений.

Текст: "{text}"

Определи тип ОЧЕНЬ ВАЖНО:
- "income" — доход: получил/получила, заработал/а, пришло, перевели, дивиденды, зарплата, фриланс, вернули, подарили, дал муж
- "expense" — расход: потратил/а, купил/а, заплатил/а, оплатил/а, потратили
Если есть слово "получил/а", "пришло", "дивиденды" — это ВСЕГДА "income".

Определи валюту:
- "KZT" — тг, тенге, или валюта не указана (по умолчанию)
- "UZS" — сум, сума, сумм, сумов, uzs
- "USD" — $, долларов, баксов, usd, доллар

Категории расходов:
{CATEGORIES_FOR_PROMPT}

Категории доходов:
{INCOME_CATEGORIES_FOR_PROMPT}

JSON формат:
{{"type": "expense"|"income", "amount": число, "currency": "KZT"|"UZS"|"USD", "category": "ключ_категории", "description": "краткое описание"}}

Если это не финансовая операция — верни: {{"type": "", "amount": 0, "currency": "KZT", "category": "", "description": ""}}"""

        try:
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            data = json.loads(raw)
            if data.get("amount", 0) > 0 and data.get("category") and data.get("type"):
                return data
            return None
        except Exception as e:
            logger.error("Claude parse error: %s", e)
            return None
