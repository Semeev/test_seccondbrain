"""Дописывает новые цены в «Журнал цен», не трогая формулы и ручные правки.

Использование:
    python add_prices.py ../Мониторинг_цен_Ташкент.xlsx prices_2026-11-24.json

JSON — список объектов:
    {"date": "2026-11-24", "position": "Бетон М300 (B22,5)", "supplier": "EKOBETON",
     "price": 500250, "unit": "м³", "coef": null, "vat": "", "delivery": "", "availability": "",
     "source": "Сайт", "link": "https://...", "comment": ""}

- position должна точно совпадать с листом «Позиции» (неизвестные пропускаются с предупреждением).
- Новый поставщик добавляется в «Поставщики» со статусом «Не проверено».
- Дубль (та же дата + позиция + поставщик + цена) не добавляется.
После запуска обязательно пересчитать файл (recalc.py из навыка xlsx) — иначе формулы без значений.
"""
import json
import sys
from datetime import date, datetime
from copy import copy

from openpyxl import load_workbook

xlsx, js = sys.argv[1], sys.argv[2]
rows = json.load(open(js, encoding="utf-8"))
wb = load_workbook(xlsx)
j, pos, sup = wb["Журнал цен"], wb["Позиции"], wb["Поставщики"]

positions = {r[1] for r in pos.iter_rows(min_row=2, values_only=True) if r[1]}
suppliers = {r[0] for r in sup.iter_rows(min_row=2, values_only=True) if r[0]}


def as_date(v):
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return datetime.strptime(str(v), "%Y-%m-%d").date()


existing = set()
first_free = None
for r in range(2, j.max_row + 1):
    b = j[f"B{r}"].value
    if b is None:
        if first_free is None:
            first_free = r
        continue
    if j[f"A{r}"].value is not None:
        existing.add((as_date(j[f"A{r}"].value), b, j[f"E{r}"].value, j[f"G{r}"].value))
if first_free is None:
    sys.exit("Журнал заполнен: нет свободных строк с формулами")

sup_next = max((r for r in range(2, sup.max_row + 1) if sup[f"A{r}"].value), default=1) + 1
added, skipped = 0, []
r = first_free
for x in rows:
    p = x["position"]
    if p not in positions:
        skipped.append(f"нет позиции в справочнике: {p}")
        continue
    d = as_date(x["date"])
    key = (d, p, x["supplier"], x["price"])
    if key in existing:
        skipped.append(f"дубль: {p} / {x['supplier']}")
        continue
    while j[f"B{r}"].value is not None:
        r += 1
    j[f"A{r}"] = d
    j[f"B{r}"] = p
    j[f"E{r}"] = x["supplier"]
    j[f"G{r}"] = x["price"]
    j[f"H{r}"] = x.get("unit") or ""
    if x.get("coef"):
        j[f"I{r}"] = x["coef"]
    for col, k in zip("KLMNOP", ["vat", "delivery", "availability", "source", "link", "comment"]):
        v = x.get(k)
        if v:
            j[f"{col}{r}"] = v
    existing.add(key)
    added += 1
    if x["supplier"] not in suppliers:
        sup[f"A{sup_next}"] = x["supplier"]
        sup[f"B{sup_next}"] = "Не проверено"
        sup[f"F{sup_next}"] = x.get("link") or ""
        sup[f"G{sup_next}"] = "Нет"
        sup[f"I{sup_next}"] = f"Добавлен автоматически {d:%d.%m.%Y}"
        for col in "ABCDEFGHI":
            sup[f"{col}{sup_next}"].font = copy(sup["A2"].font)
            sup[f"{col}{sup_next}"].border = copy(sup["A2"].border)
            sup[f"{col}{sup_next}"].alignment = copy(sup["A2"].alignment)
        suppliers.add(x["supplier"])
        sup_next += 1
    r += 1

wb.save(xlsx)
print(f"добавлено строк: {added}")
for s in skipped:
    print("пропущено —", s)
