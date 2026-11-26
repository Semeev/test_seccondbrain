"""YANGI ASR INOVATSIYA — юрлицо Uz Meter (решение пользователя 26.11.2026): договор №364/X переносим на карточку Uz Meter."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from openpyxl import load_workbook
from wbtools import upsert_supplier

X = sys.argv[1]
OLD, NEW = "YANGI ASR INOVATSIYA", "Uz Meter"
wb = load_workbook(X)
j, sup = wb["Журнал цен"], wb["Поставщики"]
n = 0
for r in range(2, j.max_row + 1):
    if j[f"E{r}"].value == OLD:
        j[f"E{r}"] = NEW
        j[f"P{r}"] = f'{j[f"P{r}"].value or ""}; юрлицо по договору — «YANGI ASR INOVATSIYA» MCHJ (это Uz Meter)'.lstrip("; ")
        n += 1
upsert_supplier(wb, NEW,
    addr="г. Ташкент, Учтепинский р-н, Jurjoniy MFY, ул. Yusuf Sakkokiy, 3-а",
    terms="Предоплата 100%, самовывоз со склада, поставка в течение месяца, гарантия 1 год (договор №364/X)",
    comment="Юрлицо: «YANGI ASR INOVATSIYA» MCHJ, ИНН 304706335, директор Yodgorov Yusuf; договор №364/X от 25.11.2026 на 140 счётчиков WMBUS DN15 — отправлен через Didox, ждёт нашей подписи",
    site="исходники/Договор_364X_YANGI_ASR_INOVATSIYA_счетчики_25.11.2026.pdf")
row = next(r for r in range(2, sup.max_row + 1) if sup[f"A{r}"].value == OLD)
sup.delete_rows(row)
wb.save(X)
p = os.path.join(os.path.dirname(os.path.abspath(X)), "данные", "сопоставление.json")
m = json.load(open(p, encoding="utf-8"))
m["suppliers"]["*|YANGI ASR INOVATSIYA"] = NEW
json.dump(m, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("строк журнала перенесено:", n, "| карточка YANGI ASR удалена (строка", row, ")")
