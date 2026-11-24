"""Ответы пользователя 24.11.2026: НДС в КП, даты КП, классы арматуры, типы, правки комментариев, удаление дубля ПГС."""
import json, re, sys, os
from copy import copy
sys.path.insert(0, os.path.dirname(__file__))
from openpyxl import load_workbook
from openpyxl.formula.translate import Translator
from wbtools import upsert_supplier, SUMMARY_OFFSET, last_position_row

X = "Мониторинг_цен_Ташкент.xlsx"
wb = load_workbook(X)
j, p, s = wb["Журнал цен"], wb["Позиции"], wb["Сводка"]
NODATE = "дата КП в файле не указана — проставлена дата загрузки"

# колонка «Дата КП» (из документа) — только если дата есть
j["A1"] = "Дата внесения"
if j["T1"].value != "Дата КП (из документа)":
    j["T1"] = "Дата КП (из документа)"
    for a in ("font", "fill", "alignment", "border"):
        setattr(j["T1"], a, copy(getattr(j["A1"], a)))
    j.column_dimensions["T"].width = 12
    for r in range(2, 2002):
        j[f"T{r}"].number_format = "DD.MM.YYYY"
        j[f"T{r}"].font = copy(j[f"A{r}"].font); j[f"T{r}"].border = copy(j[f"A{r}"].border)

log = []
for r in range(2, 2002):
    pos, sup, src = j[f"B{r}"].value, j[f"E{r}"].value, j[f"N{r}"].value
    if not pos:
        continue
    com = str(j[f"P{r}"].value or "")
    if src == "КП (письменное)":
        if not j[f"K{r}"].value:
            j[f"K{r}"] = "Да"                                   # КП по умолчанию с НДС
        if NODATE in com:
            com = com.replace("; " + NODATE, "").replace(NODATE, "")
        if "Электрика" in str(sup) or "лист «Электрика 16.11»" in str(j[f"O{r}"].value or ""):
            j[f"T{r}"] = j[f"A{r}"].value
        if sup == "BVB-ALYANS (ББВ Альянс)" and "RV-4325" in com:
            from datetime import date
            j[f"T{r}"] = date(2026, 11, 23)
    # Бекабад Файзулла — вся арматура А400 (местная, Бекабадский завод)
    if sup == "Бекабад Файзулла" and pos.startswith("Арматура А500С"):
        j[f"B{r}"] = pos.replace("А500С", "А400"); log.append(f"Файзулла: {pos} → А400")
        com = (com + "; ").lstrip("; ") + "Класс А400 — местная арматура Бекабадского завода (со слов пользователя 24.11.2026)"
    if sup == "Бекабад Файзулла" and "подтверждён пользователем" in com:
        com = "Класс А400 — местная арматура Бекабадского завода (подтверждено пользователем)" + com[com.find(";"):] if ";" in com else com
    if sup == "Модуль (металл)" and "А1" in com:
        com = com.replace("В КП: «А400-8мм А1» — уточнить класс", "А400 d8 — 9,3 млн подтверждено пользователем")
    if "В 5 раз дороже Ар Пласт — проверить диаметр/позицию" in com:
        com = com.replace("В 5 раз дороже Ар Пласт — проверить диаметр/позицию", "Цена как прислал поставщик (подтверждено пользователем)")
    if "за метр втрое дороже Ар Пласт — проверить" in com:
        com = com.replace("за метр втрое дороже Ар Пласт — проверить", "цена как прислал поставщик (подтверждено пользователем)")
    com = com.replace("В КП «М100» — вероятно М10", "В КП «М100» = М10 (подтверждено)")
    if pos == "Доводчик дверной":
        com = com.replace("Модель в КП не указана", "Доводчики на двери 60–120 кг (по данным поставщика)")
    if pos == "Пеноплекс / XPS 50 мм" and sup == "ПЕНОПЛЭКС (Ангрен / Ташкент)":
        j[f"L{r}"] = "Да"
    if pos.startswith("Плёнка полиэтиленовая 200"):
        com = com if "200 мкм" in com else (com + "; потребность — 200 мкм").lstrip("; ")
    j[f"P{r}"] = com.strip("; ") or None

upsert_supplier(wb, "Модуль (металл)", type="Склад/дистрибьютор", basis="Сталь-компания в промзоне со своим складом (со слов пользователя 24.11.2026)")
upsert_supplier(wb, "Бекабад Файзулла", cats="Арматура А400 (Бекабадский завод)", basis="Продаёт местную арматуру А400 производства Бекабадского завода (со слов пользователя)")

# удаление дубля «ПГС (песчано-гравийная смесь)»: строка в «Позициях» и в «Сводке», формулы сводки ниже — пересобрать
pr = next(r for r in range(2, last_position_row(p) + 1) if p[f"B{r}"].value == "ПГС (песчано-гравийная смесь)")
sr = pr + SUMMARY_OFFSET
tmpl = {c.column_letter: c.value for c in s[9]}
p.delete_rows(pr)
s.delete_rows(sr)
last = last_position_row(p)
for r in range(sr, last + SUMMARY_OFFSET + 1):
    for col, v in tmpl.items():
        if isinstance(v, str) and v.startswith("="):
            s[f"{col}{r}"] = Translator(v, origin=f"{col}9").translate_formula(f"{col}{r}")
s.auto_filter.ref = f"A8:V{last + SUMMARY_OFFSET}"
p.auto_filter.ref = f"A1:F{last}"
wb.save(X)
print("\n".join(log)); print("удалена позиция ПГС, строка", pr)

# сопоставление для повторных загрузок
m = json.load(open("данные/сопоставление.json", encoding="utf-8"))
m["supplier_class_override"] = {
    "BVB-ALYANS (ББВ Альянс)": {"from": "А400", "to": "А500С"},
    "Металл Центр": {"from": "А400", "to": "А500С"},
    "Бекабад Файзулла": {"from": "А500С", "to": "А400"},
}
json.dump(m, open("данные/сопоставление.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
