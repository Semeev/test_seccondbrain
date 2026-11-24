"""Общие функции для изменения рабочего файла без пересоздания (ручные данные сохраняются)."""
from copy import copy

from openpyxl.formatting.rule import FormulaRule
from openpyxl.formula.translate import Translator
from openpyxl.styles import Font, PatternFill

SUMMARY_HEADER_ROW = 8
SUMMARY_OFFSET = 7  # строка сводки = строка позиции + 7
N_JOURNAL = 2001
SUP_COLS = ["Поставщик", "Тип", "Категории", "Район / адрес", "Телефон / Telegram", "Сайт / где найден",
            "Проверен лично (Да/Нет)", "Условия (мин. партия, отсрочка, доставка)", "Комментарий",
            "Работаем (Да/Нет)", "Контактное лицо"]


def last_position_row(ws):
    r = 1
    while ws[f"B{r + 1}"].value:
        r += 1
    return r


def ensure_v2(wb):
    """Колонки «Работаем»/«Контактное лицо» у поставщиков, флаг «Наш поставщик» в журнале,
    колонки «Мин. у наших поставщиков» в сводке. Повторный запуск ничего не ломает."""
    sup, j, s, pos = wb["Поставщики"], wb["Журнал цен"], wb["Сводка"], wb["Позиции"]
    if sup["J1"].value != "Работаем (Да/Нет)":
        for col, title, w in (("J", SUP_COLS[9], 12), ("K", SUP_COLS[10], 22)):
            c = sup[f"{col}1"]
            c.value = title
            for attr in ("font", "fill", "alignment", "border"):
                setattr(c, attr, copy(getattr(sup["I1"], attr)))
            sup.column_dimensions[col].width = w
            for r in range(2, 301):
                sup[f"{col}{r}"].font = copy(sup["A2"].font)
                sup[f"{col}{r}"].border = copy(sup["A2"].border)
                sup[f"{col}{r}"].alignment = copy(sup["A2"].alignment)
        from openpyxl.worksheet.datavalidation import DataValidation
        dv = DataValidation(type="list", formula1='"Да,Нет"', allow_blank=True)
        sup.add_data_validation(dv)
        dv.add("J2:J300")
        sup.conditional_formatting.add("A2:A300", FormulaRule(formula=['$J2="Да"'], fill=PatternFill("solid", fgColor="FFF2CC"), font=Font(bold=True)))
    if j["S1"].value != "Наш поставщик":
        j["S1"] = "Наш поставщик"
        for attr in ("font", "fill", "alignment", "border"):
            setattr(j["S1"], attr, copy(getattr(j["Q1"], attr)))
        for r in range(2, N_JOURNAL + 1):
            j[f"S{r}"] = f'=IF(E{r}="","",IFERROR(IF(INDEX(Поставщики!$J:$J,MATCH(E{r},Поставщики!$A:$A,0))="Да","Да","Нет"),"Нет"))'
            j[f"S{r}"].font = copy(j[f"Q{r}"].font)
            j[f"S{r}"].fill = copy(j[f"Q{r}"].fill)
            j[f"S{r}"].border = copy(j[f"Q{r}"].border)
        j.column_dimensions["S"].width = 10
        j.auto_filter.ref = f"A1:S{N_JOURNAL}"
    if s.cell(row=SUMMARY_HEADER_ROW, column=17).value != "Мин. у наших поставщиков, сум":
        H = SUMMARY_HEADER_ROW
        for col, title, w in (("Q", "Мин. у наших поставщиков, сум", 16), ("R", "Наш поставщик (мин.)", 28), ("S", "Наша цена к рынку (мин.)", 12)):
            c = s[f"{col}{H}"]
            c.value = title
            for attr in ("font", "fill", "alignment", "border"):
                setattr(c, attr, copy(getattr(s[f"N{H}"], attr)))
            s.column_dimensions[col].width = w
        last = last_position_row(pos)
        for pr in range(2, last + 1):
            write_summary_extra(s, pr + SUMMARY_OFFSET)
        add_summary_cf(s, H + 1, last + SUMMARY_OFFSET)
        s.auto_filter.ref = f"A{H}:S{last + SUMMARY_OFFSET}"
    # подсказка внизу «Позиций» мешает дописыванию — убираем
    last = last_position_row(pos)
    for r in range(last + 1, last + 4):
        if pos[f"A{r}"].value and str(pos[f"A{r}"].value).startswith("Новую позицию"):
            pos[f"A{r}"] = None


def jc(col):
    return f"'Журнал цен'!${col}$2:${col}${N_JOURNAL}"


def write_summary_extra(s, r):
    JA, JB, JE, JJ, JS, JR = jc("A"), jc("B"), jc("E"), jc("J"), jc("S"), jc("R")
    cond = f'{JB},B{r},{JA},">="&$B$5,{JA},"<="&$B$3,{JJ},">0",{JS},"Да"'
    s[f"Q{r}"] = f'=IF(COUNTIFS({cond})=0,"",_xlfn.MINIFS({JJ},{cond}))'
    s[f"R{r}"] = (f'=IF(Q{r}="","",IFERROR(INDEX({JE},SUMPRODUCT(MAX(({JB}=B{r})*({JJ}=Q{r})*({JS}="Да")*ROW({JB})))-1),""))')
    s[f"S{r}"] = f'=IF(OR(Q{r}="",E{r}=""),"",Q{r}/E{r}-1)'
    for col in "QRS":
        s[f"{col}{r}"].font = copy(s[f"N{r}"].font)
        s[f"{col}{r}"].border = copy(s[f"N{r}"].border)
    s[f"Q{r}"].number_format = '#,##0;-#,##0;"-"'
    s[f"S{r}"].number_format = '+0.0%;-0.0%;0.0%'


def add_summary_cf(s, r1, r2):
    s.conditional_formatting.add(f"Q{r1}:R{r2}", FormulaRule(formula=[f'$Q{r1}<>""'], fill=PatternFill("solid", fgColor="FFF2CC")))
    s.conditional_formatting.add(f"S{r1}:S{r2}", FormulaRule(formula=[f'AND(ISNUMBER(S{r1}),S{r1}>0.05)'], font=Font(color="9C0006", bold=True)))


def add_positions(wb, items):
    """items: [(категория, позиция, ед., примечание, этап, частота)]. Возвращает число добавленных."""
    pos, s = wb["Позиции"], wb["Сводка"]
    existing = {pos[f"B{r}"].value for r in range(2, last_position_row(pos) + 1)}
    src_pr = last_position_row(pos)
    src_sr = src_pr + SUMMARY_OFFSET
    added = 0
    for it in items:
        if it[1] in existing:
            continue
        pr = last_position_row(pos) + 1
        for i, col in enumerate("ABCDEF"):
            pos[f"{col}{pr}"] = it[i]
            pos[f"{col}{pr}"].font = copy(pos[f"{col}{src_pr}"].font)
            pos[f"{col}{pr}"].border = copy(pos[f"{col}{src_pr}"].border)
            pos[f"{col}{pr}"].alignment = copy(pos[f"{col}{src_pr}"].alignment)
        sr = pr + SUMMARY_OFFSET
        for col in "ABCDEFGHIJKLMNOPQRSTUV":
            src = s[f"{col}{src_sr}"]
            v = src.value
            if isinstance(v, str) and v.startswith("="):
                v = Translator(v, origin=f"{col}{src_sr}").translate_formula(f"{col}{sr}")
            s[f"{col}{sr}"] = v
            for attr in ("font", "border", "number_format", "alignment"):
                setattr(s[f"{col}{sr}"], attr, copy(getattr(src, attr)))
        existing.add(it[1])
        added += 1
    if added:
        last = last_position_row(pos)
        first_new = last - added + 1 + SUMMARY_OFFSET
        H = SUMMARY_HEADER_ROW
        s.conditional_formatting.add(f"N{first_new}:N{last + SUMMARY_OFFSET}", FormulaRule(formula=[f'AND(ISNUMBER(N{first_new}),N{first_new}>$B$6)'], fill=PatternFill("solid", fgColor="FFC7CE"), font=Font(color="9C0006", bold=True)))
        s.conditional_formatting.add(f"N{first_new}:N{last + SUMMARY_OFFSET}", FormulaRule(formula=[f'AND(ISNUMBER(N{first_new}),N{first_new}<-$B$6)'], fill=PatternFill("solid", fgColor="C6EFCE"), font=Font(color="006100", bold=True)))
        s.conditional_formatting.add(f"O{first_new}:O{last + SUMMARY_OFFSET}", FormulaRule(formula=[f'$O{first_new}="Ежедневно"'], fill=PatternFill("solid", fgColor="FFE699"), font=Font(bold=True)))
        add_summary_cf(s, first_new, last + SUMMARY_OFFSET)
        s.auto_filter.ref = f"A{H}:V{last + SUMMARY_OFFSET}"
        pos.auto_filter.ref = f"A1:F{last}"
    return added


def upsert_supplier(wb, name, **kw):
    """kw: type, cats, addr, phone, site, checked, terms, comment, works, contact. Пустые значения не затирают имеющиеся."""
    sup = wb["Поставщики"]
    cols = dict(type="B", cats="C", addr="D", phone="E", site="F", checked="G", terms="H", comment="I", works="J", contact="K", basis="L")
    row = None
    r = 2
    while sup[f"A{r}"].value:
        if str(sup[f"A{r}"].value).strip().lower() == name.strip().lower():
            row = r
        r += 1
    new = row is None
    if new:
        row = r
        sup[f"A{row}"] = name
    for k, v in kw.items():
        if v in (None, ""):
            continue
        cell = sup[f"{cols[k]}{row}"]
        if (k in ("checked", "works") or (k == "type" and v == "Не проверено")) and cell.value not in (None, ""):
            continue  # не затираем то, что пользователь уже отметил
        if k == "phone" and cell.value:
            import re as _re
            digits = lambda t: _re.sub(r"\D", "", str(t))
            have = digits(cell.value)
            if all(len(digits(p)) >= 7 and digits(p)[-9:] in have for p in _re.split(r"[;,]", str(v)) if digits(p)):
                continue
        if k in ("comment", "phone", "cats") and cell.value and str(v) not in str(cell.value):
            cell.value = f"{cell.value}; {v}"
        elif k in ("comment", "phone", "cats") and cell.value:
            pass
        else:
            cell.value = v
    return new


def ensure_v3(wb):
    """Колонка «Основание» у поставщиков; в сводке — кол-во/средняя/макс по заводам и складам; источник «Сайт завода/склада»."""
    sup, s, pos, j = wb["Поставщики"], wb["Сводка"], wb["Позиции"], wb["Журнал цен"]
    if sup["L1"].value != "Основание (почему завод/склад/перекуп)":
        c = sup["L1"]
        c.value = "Основание (почему завод/склад/перекуп)"
        for attr in ("font", "fill", "alignment", "border"):
            setattr(c, attr, copy(getattr(sup["I1"], attr)))
        sup.column_dimensions["L"].width = 44
        for r in range(2, 301):
            for attr in ("font", "border", "alignment"):
                setattr(sup[f"L{r}"], attr, copy(getattr(sup["A2"], attr)))
    for dv in j.data_validations.dataValidation:
        if "N2" in str(dv.sqref) and "Сайт завода" not in (dv.formula1 or ""):
            dv.formula1 = '"Сайт завода/склада,КП (письменное),Звонок,Сайт,Объявление,Биржа UZEX,Визит"'
    H = SUMMARY_HEADER_ROW
    if s[f"T{H}"].value != "Цен у заводов/складов":
        for col, title, w in (("T", "Цен у заводов/складов", 10), ("U", "Средняя заводы/склады, сум", 15), ("V", "Макс. заводы/склады, сум", 15)):
            c = s[f"{col}{H}"]
            c.value = title
            for attr in ("font", "fill", "alignment", "border"):
                setattr(c, attr, copy(getattr(s[f"G{H}"], attr)))
            s.column_dimensions[col].width = w
        last = last_position_row(pos)
        for pr in range(2, last + 1):
            write_summary_direct(s, pr + SUMMARY_OFFSET)
        s.auto_filter.ref = f"A{H}:V{last + SUMMARY_OFFSET}"
        s.conditional_formatting.add(f"T{H + 1}:V{last + SUMMARY_OFFSET}", FormulaRule(formula=[f'$T{H + 1}>0'], fill=PatternFill("solid", fgColor="E2EFDA")))


def write_summary_direct(s, r):
    JA, JB, JJ, JQ = jc("A"), jc("B"), jc("J"), jc("Q")
    cond = f'{JB},B{r},{JA},">="&$B$5,{JA},"<="&$B$3,{JJ},">0",{JQ},"Да"'
    s[f"T{r}"] = f"=COUNTIFS({cond})"
    s[f"U{r}"] = f'=IF(T{r}=0,"",AVERAGEIFS({JJ},{cond}))'
    s[f"V{r}"] = f'=IF(T{r}=0,"",_xlfn.MAXIFS({JJ},{cond}))'
    for col in "TUV":
        s[f"{col}{r}"].font = copy(s[f"N{r}"].font)
        s[f"{col}{r}"].border = copy(s[f"N{r}"].border)
    s[f"U{r}"].number_format = '#,##0;-#,##0;"-"'
    s[f"V{r}"].number_format = '#,##0;-#,##0;"-"'


def delete_position(wb, name):
    """Удаляет позицию из «Позиций» и её строку из «Сводки», формулы сводки ниже пересобираются по шаблону строки 9."""
    from openpyxl.formula.translate import Translator
    p, s = wb["Позиции"], wb["Сводка"]
    pr = next((r for r in range(2, last_position_row(p) + 1) if p[f"B{r}"].value == name), None)
    if pr is None:
        return False
    tmpl = {c.column_letter: c.value for c in s[9]}
    p.delete_rows(pr)
    s.delete_rows(pr + SUMMARY_OFFSET)
    last = last_position_row(p)
    for r in range(pr + SUMMARY_OFFSET, last + SUMMARY_OFFSET + 1):
        for col, v in tmpl.items():
            if isinstance(v, str) and v.startswith("="):
                s[f"{col}{r}"] = Translator(v, origin=f"{col}9").translate_formula(f"{col}{r}")
    s.auto_filter.ref = f"A8:V{last + SUMMARY_OFFSET}"
    p.auto_filter.ref = f"A1:F{last}"
    return True
