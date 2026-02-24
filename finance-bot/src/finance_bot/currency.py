"""Currency conversion utilities."""

import logging
import urllib.request
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Резервные курсы (1 единица валюты = X тенге)
FALLBACK_RATES = {
    "KZT": 1.0,
    "UZS": 0.038,   # ~26 сум за 1 тенге
    "USD": 520.0,
}

SYMBOLS = {"KZT": "тг", "UZS": "сум", "USD": "$"}

_cached_rates: dict = {}
_cache_time: datetime | None = None
_CACHE_TTL = timedelta(hours=6)


def get_rates() -> dict:
    """Курсы относительно KZT (1 единица = X тенге). Кэш 6 часов."""
    global _cached_rates, _cache_time

    now = datetime.now()
    if _cached_rates and _cache_time and (now - _cache_time) < _CACHE_TTL:
        return _cached_rates

    try:
        url = "https://open.er-api.com/v6/latest/KZT"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
        if data.get("result") == "success":
            r = data["rates"]  # 1 KZT = X другой валюты
            _cached_rates = {
                "KZT": 1.0,
                "UZS": 1.0 / r["UZS"] if r.get("UZS") else FALLBACK_RATES["UZS"],
                "USD": 1.0 / r["USD"] if r.get("USD") else FALLBACK_RATES["USD"],
            }
            _cache_time = now
            logger.info("Rates updated: %s", _cached_rates)
            return _cached_rates
    except Exception as e:
        logger.warning("Rate fetch failed: %s, using fallback", e)

    return FALLBACK_RATES


def to_kzt(amount: float, currency: str) -> float:
    """Конвертировать сумму в тенге."""
    rate = get_rates().get(currency.upper(), 1.0)
    return amount * rate


def fmt(amount: float, currency: str) -> str:
    """Отформатировать сумму с символом валюты."""
    cur = currency.upper()
    symbol = SYMBOLS.get(cur, cur)
    if cur == "USD":
        return f"${amount:,.0f}"
    return f"{amount:,.0f} {symbol}"
