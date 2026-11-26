"""Сравнение поставщиков арматуры А500С на заявку (по умолчанию 28 т) — Excel для пользователя.

    python tools/compare_armatura.py Мониторинг_цен_Ташкент.xlsx сводки/Сравнение_арматура_28т_ДАТА.xlsx

Берёт из «Журнала цен» только данные пользователя (без сайтов/объявлений/биржи), по каждому поставщику —
последнюю дату цены (при нескольких строках в один день — самую низкую). Доставка и примечания —
данные/сравнение_арматура.json. Потом пересчитать файл recalc.py (формулы итогов).
"""
import json, os, sys
from datetime import date, datetime
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L

src, out = sys.argv[1], sys.argv[2]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cfg = json.load(open(os.path.join(ROOT, "данные", "сравнение_арматура.json"), encoding="utf-8"))
Q = cfg["order"]  # {"d10": 4, ...}
D = list(Q)
INTERNET = {"Сайт", "Объявление", "Биржа UZEX", "Сайт завода/склада"}

wb = load_workbook(src, data_only=True, read_only=True)
best = {}
for r in wb["Журнал цен"].iter_rows(min_row=2, values_only=True):
    if not r[1] or not str(r[1]).startswith("Арматура А500С ") or r[13] in INTERNET or "UZEX" in str(r[4] or ""):
        continue
    d = str(r[1]).split()[-1]
    if d not in Q or not isinstance(r[9], (int, float)):
        continue
    dt = r[0].date() if isinstance(r[0], datetime) else r[0]
    k = (r[4], d)
    if k not in best or dt > best[k][0] or (dt == best[k][0] and r[9] < best[k][1]):
        best[k] = (dt, r[9])
sups = {s for s, _ in best}
rows = []
for s in sups:
    p = {d: best.get((s, d)) for d in D}
    if not all(p.values()):
        continue  # only suppliers who quoted every diameter of the order
    tot = sum(Q[d] * p[d][1] for d in D)
    extra = cfg["suppliers"].get(s, {})
    rows.append((tot + (extra.get("delivery") or 0), tot, s, p, max(v[0] for v in p.values()), extra))
rows.sort(key=lambda x: (x[1], x[0]))

o = Workbook(); ws = o.active; ws.title = f"Арматура {sum(Q.values())} т"
thin = Side(style="thin", color="BBBBBB"); B = Border(left=thin, right=thin, top=thin, bottom=thin)
ws["A1"] = f"Сравнение цен на арматуру А500С — заявка {sum(Q.values())} т (цены за тонну с НДС)"; ws["A1"].font = Font(bold=True, size=14)
ws["A2"] = f"Только цены, которые дал пользователь (КП, договоры, прайсы, звонки). Сформировано {date.today():%d.%m.%Y}."; ws["A2"].font = Font(italic=True, color="666666")
hdr = ["Место", "Поставщик", "Дата цены"] + [f"{d}, {q} т — цена" for d, q in Q.items()] + ["Итого металл, сум", "Разница с лучшим, сум", "Доставка, сум", "Итого с доставкой, сум", "Примечание"]
H = 4
for i, t in enumerate(hdr, 1):
    c = ws.cell(H, i, t); c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="44546A")
    c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center"); c.border = B
first, last = H + 1, H + len(rows)
tc = 4 + len(D)  # total column
for k, (_, tot, s, p, dt, extra) in enumerate(rows):
    r = H + 1 + k
    for i, v in enumerate([k + 1, s, dt.strftime("%d.%m")] + [p[d][1] for d in D], 1):
        ws.cell(r, i, v)
    ws.cell(r, tc, "=" + "+".join(f"{L(4 + i)}{r}*{q}" for i, q in enumerate(Q.values())))
    ws.cell(r, tc + 1, f"={L(tc)}{r}-MIN(${L(tc)}${first}:${L(tc)}${last})")
    dl = extra.get("delivery")
    ws.cell(r, tc + 2, dl if dl is not None else extra.get("delivery_text", "самовывоз / не указано"))
    ws.cell(r, tc + 3, f"={L(tc)}{r}+{L(tc + 2)}{r}" if dl is not None else f"={L(tc)}{r}")
    ws.cell(r, tc + 4, extra.get("note", ""))
    for i in range(1, tc + 5):
        c = ws.cell(r, i); c.border = B
        if 4 <= i <= tc + 3: c.number_format = "# ### ### ##0"
        if k == 0: c.fill = PatternFill("solid", fgColor="E2EFDA")
    if k == 0:
        ws.cell(r, 2).font = Font(bold=True); ws.cell(r, tc).font = Font(bold=True)
r = last + 1
ws.cell(r, 2, "Лучшая цена по диаметру").font = Font(bold=True)
for i in range(len(D)):
    c = ws.cell(r, 4 + i, f"=MIN({L(4 + i)}{first}:{L(4 + i)}{last})"); c.number_format = "# ### ### ##0"; c.font = Font(bold=True)
c = ws.cell(r, tc, "=" + "+".join(f"{L(4 + i)}{r}*{q}" for i, q in enumerate(Q.values()))); c.number_format = "# ### ### ##0"; c.font = Font(bold=True)
for n, line in enumerate(cfg.get("footer", []), 3):
    ws.cell(last + n, 1, line)
for i, w in enumerate([7, 30, 10] + [13] * len(D) + [16, 16, 18, 18, 46], 1):
    ws.column_dimensions[L(i)].width = w
ws.row_dimensions[H].height = 34; ws.freeze_panes = "C5"
o.save(out)
for _, tot, s, *_ in rows:
    print(f"{s}: {tot:,.0f}".replace(",", " "))
