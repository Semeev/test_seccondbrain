"""Generate PDF of vocalist database from vault."""

import re
import tempfile
from pathlib import Path


def generate_vocalists_pdf(vault_path: Path) -> Path:
    """Read baza.md and generate a PDF file. Returns path to temp PDF."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

    # Find a Cyrillic-capable font
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ]
    regular = next((p for p in font_paths[::2] if Path(p).exists()), None)
    bold = next((p for p in font_paths[1::2] if Path(p).exists()), None)

    if regular and bold:
        pdfmetrics.registerFont(TTFont("CyrFont", regular))
        pdfmetrics.registerFont(TTFont("CyrFont-Bold", bold))
        fn, fn_bold = "CyrFont", "CyrFont-Bold"
    else:
        fn, fn_bold = "Helvetica", "Helvetica-Bold"

    # Read baza.md
    baza_path = vault_path / "thoughts" / "projects" / "sun-group" / "vocalists" / "baza.md"
    content = baza_path.read_text(encoding="utf-8")

    # Parse table rows
    rows = []
    in_table = False
    for line in content.splitlines():
        if line.startswith("| #") or line.startswith("|---|"):
            in_table = True
            continue
        if in_table and line.startswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            # Remove markdown links [text](url) → @text
            cells = [re.sub(r'\[(@[\w.]+)\]\([^)]+\)', r'\1', c) for c in cells]
            rows.append(cells)
        elif in_table and not line.startswith("|"):
            break

    # Build PDF
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()

    doc = SimpleDocTemplate(
        tmp.name,
        pagesize=landscape(A4),
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()

    def ps(name, size=8, bold=False, align="LEFT"):
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        return ParagraphStyle(
            name,
            parent=styles["Normal"],
            fontSize=size,
            fontName=fn_bold if bold else fn,
            leading=size + 3,
            alignment=TA_CENTER if align == "CENTER" else TA_LEFT,
        )

    title_style = ps("title", 15, bold=True, align="CENTER")
    sub_style = ps("sub", 9, align="CENTER")
    sub_style.textColor = colors.grey
    sub_style.spaceAfter = 12
    cell_s = ps("cell", 8)
    head_s = ps("head", 8, bold=True, align="CENTER")

    def p(text, style=None):
        return Paragraph(str(text) if text else "—", style or cell_s)

    headers = ["#", "Имя / Группа", "Instagram", "Telegram / Тел", "Формат", "Жанр / Стиль", "Ценник", "Комментарий"]
    col_widths = [1*cm, 3.5*cm, 3*cm, 3.5*cm, 4*cm, 4*cm, 2*cm, 5.6*cm]

    table_data = [[p(h, head_s) for h in headers]]
    for row in rows:
        table_data.append([p(c) for c in row])

    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#a8d5c2")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        *[("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f0f4f8"))
          for i in range(2, len(table_data), 2)],
        *[("BACKGROUND", (0, i), (-1, i), colors.white)
          for i in range(1, len(table_data), 2)],
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, colors.HexColor("#6bb89e")),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
    ]))

    from datetime import date
    doc.build([
        Paragraph("База вокалистов — SUN Group Ташкент", title_style),
        Paragraph(f"Обновлено: {date.today().strftime('%d.%m.%Y')} · {len(rows)} исполнителей", sub_style),
        table,
    ])

    return Path(tmp.name)
