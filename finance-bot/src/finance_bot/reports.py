"""Report generation."""

from finance_bot.categories import CATEGORIES, INCOME_CATEGORIES
from finance_bot.currency import to_kzt


def _kzt(r: dict) -> float:
    """Конвертировать запись в тенге."""
    return to_kzt(r["amount"], r.get("currency", "KZT"))


def format_report(records: list[dict], title: str) -> str:
    if not records:
        return f"📊 <b>{title}</b>\n\nЗаписей нет."

    expenses = [r for r in records if r.get("type", "expense") == "expense"]
    incomes = [r for r in records if r.get("type") == "income"]

    total_expense = sum(_kzt(r) for r in expenses)
    total_income = sum(_kzt(r) for r in incomes)
    balance = total_income - total_expense

    lines = [f"📊 <b>{title}</b>\n"]

    # Balance — главное вверху
    if total_income > 0:
        balance_emoji = "✅" if balance >= 0 else "⚠️"
        sign = "+" if balance >= 0 else ""
        lines.append(f"{balance_emoji} <b>Баланс: {sign}{balance:,.0f} тг</b>")
        lines.append(f"📈 Доходы:  <b>+{total_income:,.0f} тг</b>")
        lines.append(f"📉 Расходы: <b>-{total_expense:,.0f} тг</b>\n")
    else:
        lines.append(f"📉 <b>Расходы: {total_expense:,.0f} тг</b>\n")

    # Расходы по категориям (суммируем в тенге)
    if expenses:
        exp_totals: dict = {}
        for r in expenses:
            cat = r["category"]
            exp_totals[cat] = exp_totals.get(cat, 0) + _kzt(r)
        exp_totals = dict(sorted(exp_totals.items(), key=lambda x: x[1], reverse=True))
        for cat_key, amount in exp_totals.items():
            label = CATEGORIES.get(cat_key, cat_key)
            pct = (amount / total_expense * 100) if total_expense else 0
            lines.append(f"{label}: <b>{amount:,.0f}</b> · {pct:.0f}%")

    # Доходы по категориям
    if incomes:
        lines.append("")
        income_totals: dict = {}
        for r in incomes:
            cat = r["category"]
            income_totals[cat] = income_totals.get(cat, 0) + _kzt(r)
        for cat_key, amount in sorted(income_totals.items(), key=lambda x: x[1], reverse=True):
            label = INCOME_CATEGORIES.get(cat_key, cat_key)
            lines.append(f"{label}: <b>+{amount:,.0f} тг</b>")

    lines.append(f"\n📝 Записей: {len(records)}")
    return "\n".join(lines)
