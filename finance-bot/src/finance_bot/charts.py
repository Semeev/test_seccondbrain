"""Premium dark chart generation."""

import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

from finance_bot.categories import CATEGORIES

# Premium color palette
BG_COLOR = "#1a1215"          # тёмный бордово-серый фон
CARD_COLOR = "#231820"
IVORY = "#f5f0e8"             # слоновая кость
MILK = "#faf6ef"              # молочный
BURGUNDY = "#6b1f2a"          # богатый бордовый
BURGUNDY_LIGHT = "#8b2d3a"
BURGUNDY_BRIGHT = "#a83348"
LACOSTE = "#4a7c59"           # зелёный Lacoste
LACOSTE_LIGHT = "#5f9970"
GRAY = "#8a8a8a"              # серый
GRAY_LIGHT = "#b0a8a0"        # тёплый серый
TEXT_COLOR = IVORY
TEXT_DIM = GRAY_LIGHT

BAR_COLORS = [
    "#8b2d3a",   # бордо
    "#6b1f2a",   # тёмный бордо
    "#4a7c59",   # lacoste зелёный
    "#a83348",   # яркий бордо
    "#5f9970",   # светлый lacoste
    "#7a3040",   # средний бордо
    "#3d6b4a",   # тёмный lacoste
    "#c05070",   # розово-бордовый
    "#8a7a72",   # тёплый серый
    "#6b8f76",   # серо-зелёный
]


def generate_chart(records: list[dict], title: str) -> io.BytesIO:
    """Generate premium dark bar chart, return PNG bytes."""
    # Aggregate by category
    totals: dict[str, float] = {}
    for r in records:
        cat = r["category"]
        totals[cat] = totals.get(cat, 0) + r["amount"]

    if not totals:
        return None

    # Sort by amount, take top 10
    sorted_items = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:10]
    labels = [CATEGORIES.get(k, k).split(" ", 1)[-1] for k, _ in sorted_items]  # remove emoji
    emojis = [CATEGORIES.get(k, k).split(" ", 1)[0] for k, _ in sorted_items]
    values = [v for _, v in sorted_items]
    total_sum = sum(totals.values())

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    # Horizontal bars
    n = len(values)
    colors = [BAR_COLORS[i % len(BAR_COLORS)] for i in range(n)]
    bars = ax.barh(range(n), values, color=colors, height=0.6, zorder=3)

    # Add value labels inside/outside bars
    max_val = max(values)
    for i, (bar, val) in enumerate(zip(bars, values)):
        pct = val / total_sum * 100
        label = f"{val:,.0f} тг  {pct:.0f}%"
        x_pos = val + max_val * 0.01
        ax.text(x_pos, i, label, va="center", ha="left",
                color=TEXT_DIM, fontsize=8.5, fontweight="normal")

    # Y axis labels with emoji
    full_labels = [f"{e}  {l}" for e, l in zip(emojis, labels)]
    ax.set_yticks(range(n))
    ax.set_yticklabels(full_labels, color=TEXT_COLOR, fontsize=9.5)
    ax.invert_yaxis()

    # Remove axes clutter
    ax.set_xticks([])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_color("#333333")

    # Grid lines subtle
    ax.xaxis.grid(True, color="#222222", linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)

    # Title
    ax.set_title(title, color=IVORY, fontsize=14, fontweight="bold",
                 pad=15, loc="left")

    # Total sum subtitle
    fig.text(0.13, 0.93, f"Итого: {total_sum:,.0f} тг",
             color=GRAY_LIGHT, fontsize=10, ha="left")

    # Burgundy top border line
    fig.add_artist(plt.Line2D([0.05, 0.95], [0.97, 0.97],
                               transform=fig.transFigure,
                               color=BURGUNDY_LIGHT, linewidth=1.5))

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=BG_COLOR, edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf
