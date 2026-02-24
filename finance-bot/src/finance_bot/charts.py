"""Text-based visual chart for Telegram."""

from finance_bot.categories import CATEGORIES, INCOME_CATEGORIES

BAR_LEN = 10


def _bar(filled: int, total: int, full: str, empty: str) -> str:
    f = round(filled / total * BAR_LEN) if total else 0
    return full * f + empty * (BAR_LEN - f)


def generate_chart(records: list[dict], title: str) -> str | None:
    if not records:
        return None

    expenses = [r for r in records if r.get("type", "expense") == "expense"]
    incomes = [r for r in records if r.get("type") == "income"]

    total_expense = sum(r["amount"] for r in expenses)
    total_income = sum(r["amount"] for r in incomes)
    balance = total_income - total_expense
    max_val = max(total_income, total_expense, 1)

    lines = [f"<b>{title}</b>\n"]

    # Баланс — крупно вверху
    if total_income > 0:
        sign = "+" if balance >= 0 else ""
        emoji = "✅" if balance >= 0 else "⚠️"
        lines.append(f"{emoji} <b>Остаток: {sign}{balance:,.0f} тг</b>\n")

        # Сравнение доход/расход
        lines.append(f"📈 Доход   {_bar(total_income, max_val, '🟩', '⬜')}  <b>+{total_income:,.0f}</b>")
        lines.append(f"📉 Расход  {_bar(total_expense, max_val, '🟥', '⬜')}  <b>-{total_expense:,.0f}</b>\n")
    else:
        lines.append(f"📉 <b>Расходы: {total_expense:,.0f} тг</b>\n")

    # Топ расходов по категориям
    if expenses:
        exp_totals: dict = {}
        for r in expenses:
            cat = r["category"]
            exp_totals[cat] = exp_totals.get(cat, 0) + r["amount"]
        sorted_exp = sorted(exp_totals.items(), key=lambda x: x[1], reverse=True)[:8]
        max_exp = sorted_exp[0][1]

        lines.append("— Расходы по категориям —")
        for cat_key, amount in sorted_exp:
            label = CATEGORIES.get(cat_key, cat_key)
            pct = amount / total_expense * 100 if total_expense else 0
            bar = _bar(amount, max_exp, "🟥", "⬜")
            lines.append(f"{label}\n<code>{bar}</code> <b>{amount:,.0f}</b> · {pct:.0f}%\n")

    return "\n".join(lines)
