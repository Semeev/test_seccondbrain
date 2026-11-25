"""Лист «Мелочь (вне сводки)»: все цены по позициям из данные/скрыть_в_сводке.json — хранятся отдельно, в PDF-сводку не попадают.

Использование (после add_prices.py, лист пересоздаётся целиком, остальные листы не трогаются):
    python tools/minor_sheet.py Мониторинг_цен_Ташкент.xlsx
"""
import json, os, sys
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

X = sys.argv[1]
HIDE = json.load(open(os.path.join(os.path.dirname(os.path.abspath(X)), "данные", "скрыть_в_сводке.json"), encoding="utf-8"))["positions"]
NAME = "Мелочь (вне сводки)"
wb = load_workbook(X)
pos = {r[1]: r for r in wb["Позиции"].iter_rows(min_row=2, values_only=True) if r[1]}
order = {n: i for i, n in enumerate(HIDE)}
rows = []
for r in wb["Журнал цен"].iter_rows(min_row=2, values_only=True):
    if r[1] in order and isinstance(r[6], (int, float)):
        price = r[6] * (r[8] if isinstance(r[8], (int, float)) else 1)
        p = pos.get(r[1], (None,) * 6)
        rows.append((order[r[1]], [p[0], r[1], p[2], r[4], round(price, 2), r[19], r[0], r[13], r[14], r[15]]))
rows.sort(key=lambda x: (x[0], x[1][4]))

if NAME in wb.sheetnames:
    del wb[NAME]
ws = wb.create_sheet(NAME)
ws["A1"] = "Мелочь: хранится в базе, в PDF-сводку не выводится (список — данные/скрыть_в_сводке.json). Лист пересоздаётся скриптом tools/minor_sheet.py — правки вносить в «Журнал цен»."
ws["A1"].font = Font(italic=True, color="555555")
H = ["Категория", "Позиция", "Ед.", "Поставщик", "Цена за ед., сум (с НДС)", "Дата КП", "Дата внесения", "Источник", "Ссылка", "Комментарий"]
fill = PatternFill("solid", fgColor="1F3864")
for i, h in enumerate(H, 1):
    c = ws.cell(row=3, column=i, value=h)
    c.font, c.fill, c.alignment = Font(bold=True, color="FFFFFF"), fill, Alignment(wrap_text=True, vertical="center")
for k, (_, v) in enumerate(rows, 4):
    for i, x in enumerate(v, 1):
        c = ws.cell(row=k, column=i, value=x.date() if isinstance(x, datetime) else x)
        if i == 5:
            c.number_format = "#,##0"
        if i in (6, 7):
            c.number_format = "DD.MM.YYYY"
        if i in (2, 10):
            c.alignment = Alignment(wrap_text=True, vertical="top")
for col, w in zip("ABCDEFGHIJ", (24, 46, 8, 24, 16, 12, 12, 16, 34, 70)):
    ws.column_dimensions[col].width = w
ws.freeze_panes = "A4"
ws.auto_filter.ref = f"A3:J{max(3, len(rows) + 3)}"
wb.save(X)
print(f"{NAME}: {len(rows)} цен по {len({v[1] for _, v in rows})} позициям")
