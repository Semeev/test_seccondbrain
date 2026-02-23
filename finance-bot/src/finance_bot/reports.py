"""Report generation."""

from finance_bot.categories import CATEGORIES
from finance_bot.storage import FinanceStorage


def format_report(records: list[dict], title: str) -> str:
    if not records:
        return f"📊 <b>{title}</b>\n\nЗаписей нет."

    storage = FinanceStorage.__new__(FinanceStorage)
    totals = {}
    for r in records:
        cat = r["category"]
        totals[cat] = totals.get(cat, 0) + r["amount"]
    totals = dict(sorted(totals.items(), key=lambda x: x[1], reverse=True))

    total_sum = sum(totals.values())

    lines = [f"📊 <b>{title}</b>\n"]

    for cat_key, amount in totals.items():
        label = CATEGORIES.get(cat_key, cat_key)
        pct = (amount / total_sum * 100) if total_sum else 0
        lines.append(f"{label}: <b>{amount:,.0f}</b> ({pct:.0f}%)")

    lines.append(f"\n💰 <b>Итого: {total_sum:,.0f}</b>")
    lines.append(f"📝 Записей: {len(records)}")

    return "\n".join(lines)
