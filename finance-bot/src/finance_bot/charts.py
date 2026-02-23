"""Text-based visual chart for Telegram."""

from finance_bot.categories import CATEGORIES

BAR_FULL = "🟩"
BAR_EMPTY = "⬜"
BAR_LEN = 10


def generate_chart(records: list[dict], title: str) -> str | None:
    """Generate beautiful text chart with emoji and progress bars."""
    totals: dict[str, float] = {}
    for r in records:
        cat = r["category"]
        totals[cat] = totals.get(cat, 0) + r["amount"]

    if not totals:
        return None

    sorted_items = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:10]
    total_sum = sum(totals.values())
    max_val = sorted_items[0][1]

    lines = [f"<b>{title}</b>\n"]

    for cat_key, amount in sorted_items:
        label = CATEGORIES.get(cat_key, cat_key)
        pct = amount / total_sum * 100
        bar_fill = round(amount / max_val * BAR_LEN)
        bar = BAR_FULL * bar_fill + BAR_EMPTY * (BAR_LEN - bar_fill)

        lines.append(
            f"{label}\n"
            f"<code>{bar}</code>  <b>{amount:,.0f} тг</b>  {pct:.0f}%\n"
        )

    lines.append(f"💰 <b>Итого: {total_sum:,.0f} тг</b>")
    return "\n".join(lines)
