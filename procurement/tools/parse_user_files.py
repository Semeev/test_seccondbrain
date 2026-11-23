"""Разбор файлов пользователя (по структуре, а не по имени — имена при загрузке искажаются).

Тип «КП» (запрошенные цены): на листах блоки с шапкой «№ | Наименование товара | <поставщик> | [ед изм] | кол-во | сумма | контакты…».
Блоки могут стоять рядом (слева и справа) и друг под другом.
Тип «Поставщики»: листы с шапкой «№ | Поставщик | Позиции | Контакты | коментарии | …».
"""
import re
from datetime import date

from openpyxl import load_workbook


def norm(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def detect(path):
    wb = load_workbook(path, data_only=True, read_only=True)
    for ws in wb.worksheets:
        for row in ws.iter_rows(max_row=5, values_only=True):
            vals = [norm(v).lower() for v in row]
            if "наименование товара" in vals:
                return "kp"
            if "поставщик" in vals and "контакты" in vals:
                return "suppliers"
    return None


def sheet_date(title, year):
    m = re.search(r"(\d{1,2})\.(\d{1,2})", title)
    if m:
        try:
            return date(year, int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None
    return None


def parse_kp(path, year=2026):
    """Возвращает список записей: sheet, block (адрес шапки), supplier_raw, contacts, item, price, unit, qty, sheet_date."""
    wb = load_workbook(path, data_only=True)
    out = []
    for ws in wb.worksheets:
        grid = [[c for c in row] for row in ws.iter_rows(values_only=True)]
        heads = []
        for r, row in enumerate(grid):
            for c in range(len(row) - 1):
                if norm(row[c]) == "№" and norm(row[c + 1]).lower() == "наименование товара":
                    heads.append((r, c))
        for i, (r, c) in enumerate(heads):
            row = grid[r]
            get = lambda rr, cc: grid[rr][cc] if rr < len(grid) and cc < len(grid[rr]) else None
            supplier = norm(get(r, c + 2))
            has_unit = norm(get(r, c + 3)).lower().startswith("ед")
            qcol = c + 4 if has_unit else c + 3
            scol = qcol + 1
            contacts = [norm(v) for v in row[scol + 1:scol + 5] if norm(v)]
            # граница блока — следующая шапка в тех же колонках
            end = len(grid)
            for r2, c2 in heads[i + 1:]:
                if c2 == c and r2 > r:
                    end = r2
                    break
            for rr in range(r + 1, end):
                item = norm(get(rr, c + 1))
                price = get(rr, c + 2)
                if not item and isinstance(price, (int, float)) and price > 0 and isinstance(get(rr, c), (int, float)):
                    item = norm(ws.title)  # цена есть, а наименование не заполнено — берём название вкладки
                if not item or not isinstance(price, (int, float)) or price <= 0:
                    # строка с контактом под блоком (например «912753000 | Алишер»)
                    if isinstance(get(rr, c + 1), (int, float)) and get(rr, c + 2):
                        contacts.append(f"{get(rr, c + 1)} {norm(get(rr, c + 2))}")
                    continue
                out.append(dict(sheet=norm(ws.title), block=f"{ws.title}!R{r + 1}C{c + 1}", supplier_raw=supplier,
                                contacts=contacts, item=item, price=float(price),
                                unit=norm(get(rr, c + 3)) if has_unit else "", qty=get(rr, qcol),
                                sheet_date=sheet_date(ws.title, year)))
    return out


def parse_suppliers(path):
    wb = load_workbook(path, data_only=True)
    out = []
    for ws in wb.worksheets:
        hdr = None
        for row in ws.iter_rows(values_only=True):
            vals = [norm(v) for v in row]
            if hdr is None:
                if "Поставщик" in vals and "Контакты" in vals:
                    hdr = {v.lower(): i for i, v in enumerate(vals) if v}
                continue
            g = lambda k: vals[hdr[k]] if k in hdr and hdr[k] < len(vals) else ""
            name, items, contacts, comment = g("поставщик"), g("позиции"), g("контакты"), g("коментарии")
            extra = [v for i, v in enumerate(vals) if v and i not in hdr.values() and v.lower().startswith("http")]
            if not (name or contacts):
                continue
            out.append(dict(sheet=norm(ws.title), name=name, items=items, contacts=contacts, comment=comment,
                            site=extra[0] if extra else ""))
    return out
