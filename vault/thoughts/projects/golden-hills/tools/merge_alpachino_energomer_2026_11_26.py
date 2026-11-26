"""«Альпачино (спецодежда)» = ENERGOMER INVEST, менеджер Али (решение пользователя 26.11.2026): оставляем название компании, карточку Альпачино удаляем."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from openpyxl import load_workbook
from wbtools import upsert_supplier

X = sys.argv[1]
OLD, NEW = "Альпачино (спецодежда)", "ENERGOMER INVEST"
wb = load_workbook(X)
j, sup = wb["Журнал цен"], wb["Поставщики"]
row = next(r for r in range(2, sup.max_row + 1) if sup[f"A{r}"].value == OLD)
old = {c: sup[f"{c}{row}"].value for c in "BCDEFGHIJKL"}
n = 0
for r in range(2, j.max_row + 1):
    if j[f"E{r}"].value == OLD:
        j[f"E{r}"] = NEW
        j[f"P{r}"] = f'{j[f"P{r}"].value or ""}; в КП 23.11 — «Альпачино», это ENERGOMER INVEST (менеджер Али)'.lstrip("; ")
        n += 1
    elif j[f"E{r}"].value == NEW and j[f"P{r}"].value:
        j[f"P{r}"] = str(j[f"P{r}"].value).replace("вероятно, юрлицо «Альпачино (спецодежда)» — цены и кол-во совпадают с его КП 23.11 (уточнить у пользователя)",
                                                   "это «Альпачино» из КП 23.11 (менеджер Али) — подтвердил пользователь")
upsert_supplier(wb, NEW, phone=old["E"], works="Да", contact="Али (менеджер)", type=old["B"] if old["B"] not in (None, "Не проверено") else None,
                basis=old["L"], comment=f"В файлах пользователя — «Альпачино»; объединено 26.11.2026 (подтвердил пользователь). {old['I'] or ''}".strip())
for r in range(2, sup.max_row + 1):
    if sup[f"A{r}"].value == NEW:
        sup[f"I{r}"] = str(sup[f"I{r}"].value).replace("; вероятно, юрлицо «Альпачино (спецодежда)» — не объединено, ждёт подтверждения", "")
        sup[f"J{r}"] = "Да"
sup.delete_rows(row)
wb.save(X)
p = os.path.join(os.path.dirname(os.path.abspath(X)), "данные", "сопоставление.json")
m = json.load(open(p, encoding="utf-8")); m["suppliers"]["*|Альпачино (спецодежда)"] = NEW; m["suppliers"]["*|Альпачино"] = NEW
json.dump(m, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("строк журнала перенесено:", n, "| карточка Альпачино удалена (строка", row, ")")
