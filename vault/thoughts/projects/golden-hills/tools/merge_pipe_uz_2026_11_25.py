"""Объединение «Pipe UZ» с «Завод Махсус Полимер» (решение пользователя 25.11.2026, пока предварительно —
не подтверждено, что менеджер Ислом 93 515 55 85 работает на заводе; КП Pipe UZ выставлено на бланке завода)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from openpyxl import load_workbook
from wbtools import upsert_supplier

X = sys.argv[1]
OLD, NEW = "Pipe UZ", "Завод Махсус Полимер"
wb = load_workbook(X)
j, sup = wb["Журнал цен"], wb["Поставщики"]
n = 0
for r in range(2, j.max_row + 1):
    if j[f"E{r}"].value == OLD:
        j[f"E{r}"] = NEW
        j[f"P{r}"] = f'{j[f"P{r}"].value or ""}; поставщик в файле — «Pipe UZ» (Ислом), объединён с заводом 25.11.2026'.lstrip("; ")
        n += 1
row = next(r for r in range(2, sup.max_row + 1) if sup[f"A{r}"].value == OLD)
upsert_supplier(wb, NEW, phone="93 515 55 85 (Ислом, менеджер — через него пришло КП)", works="Да", checked=sup[f"G{row}"].value,
                contact="Ислом (93 515 55 85)",
                comment="В файлах пользователя — «Pipe UZ»; объединено 25.11.2026 по КП № 18/11-бн на бланке завода (предварительно: "
                        "номер Ислома на сайте pipe.uz не указан — подтвердить звонком на 71 295-03-04)")
# в комментарии завода убираем устаревшую пометку о двух карточках
for r in range(2, sup.max_row + 1):
    if sup[f"A{r}"].value == NEW and sup[f"I{r}"].value:
        sup[f"I{r}"] = "; ".join(p for p in str(sup[f"I{r}"].value).split("; ") if not p.startswith("Его КП пришло через «Pipe UZ»"))
sup.delete_rows(row)
wb.save(X)
p = os.path.join(os.path.dirname(os.path.abspath(X)), "данные", "сопоставление.json")
m = json.load(open(p, encoding="utf-8"))
m["suppliers"]["*|Pipe UZ"] = NEW
json.dump(m, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("строк журнала перенесено:", n, "| карточка Pipe UZ удалена (строка", row, ")")
