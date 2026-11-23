from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.comments import Comment
from datetime import date
import sys

OUT = sys.argv[1]
F = "Arial"
HDR_FILL = PatternFill("solid", fgColor="1F3864")
HDR_FONT = Font(name=F, bold=True, color="FFFFFF", size=10)
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
CALC_FILL = PatternFill("solid", fgColor="F2F2F2")
BLUE = Font(name=F, color="0000FF", size=10)
BLACK = Font(name=F, size=10)
BOLD = Font(name=F, bold=True, size=10)
thin = Side(style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
NUM = '#,##0;-#,##0;"-"'
PCT = '+0.0%;-0.0%;0.0%'
DFMT = "DD.MM.YYYY"
N_ROWS = 2000  # rows prepared in the journal

wb = Workbook()

# ---------------- Позиции ----------------
pos = wb.active
pos.title = "Позиции"
from positions import P
positions = [(c, n, u, note, st, fr) for (st, c, n, u, note, fr) in P]
pos.append(["Категория", "Позиция", "Базовая ед.", "Требования / примечание", "Этап стройки", "Как часто проверять цену"])
for r in positions:
    pos.append(list(r))
POS_LAST = len(positions) + 1
for c in pos[1]:
    c.fill, c.font, c.alignment, c.border = HDR_FILL, HDR_FONT, CENTER, BORDER
for row in pos.iter_rows(min_row=2, max_row=POS_LAST):
    for c in row:
        c.font, c.border, c.alignment = BLUE, BORDER, WRAP
for col, w in zip("ABCDEF", [24, 48, 10, 52, 26, 16]):
    pos.column_dimensions[col].width = w
pos.freeze_panes = "C2"
pos.auto_filter.ref = f"A1:F{POS_LAST}"
dv_f = DataValidation(type="list", formula1='"Ежедневно,Еженедельно,Ежемесячно"', allow_blank=True)
pos.add_data_validation(dv_f); dv_f.add("F2:F500")
pos[f"A{POS_LAST+2}"] = "Новую позицию добавляйте в конец списка (синий текст — вводимые данные). Выпадающий список в «Журнале цен» берёт позиции до строки 500; чтобы позиция попала в «Сводку», скопируйте последнюю строку сводки вниз."
pos[f"A{POS_LAST+2}"].font = Font(name=F, italic=True, size=9, color="595959")

# ---------------- Поставщики ----------------
sup = wb.create_sheet("Поставщики")
TYPES = ["Завод-производитель", "Склад/дистрибьютор", "Перекупщик", "Частник", "Не проверено"]
sup.append(["Поставщик", "Тип", "Категории", "Район / адрес", "Телефон / Telegram",
            "Сайт / где найден", "Проверен лично (Да/Нет)", "Условия (мин. партия, отсрочка, доставка)", "Комментарий"])
suppliers = [
    ("АО «Узметкомбинат» (Бекабад)", "Завод-производитель", "Арматура", "Ташкентская обл., г. Бекабад", "", "Крупнейший металлургический завод РУз; цены также смотреть на бирже UZEX", "Нет", "", "Запросить прямой договор / список официальных дилеров"),
    ("POYTAXT BETON", "Не проверено", "Бетон", "Ташкент", "", "https://www.goldenpages.uz/rubrics/?Id=102963", "Нет", "", "В каталоге значится как бетонный завод"),
    ("CENTRAL BETON", "Не проверено", "Бетон", "Ташкент", "", "https://www.goldenpages.uz/rubrics/?Id=102963", "Нет", "", "В каталоге значится как бетонный завод"),
    ("BSD завод", "Не проверено", "Бетон", "Ташкент", "", "https://www.goldenpages.uz/rubrics/?Id=102963", "Нет", "", "В каталоге значится как завод"),
    ("ZNK Beton", "Не проверено", "Бетон", "", "", "https://glotr.uz/showcase/znk-beton-21889/", "Нет", "", ""),
    ("Nurafshon Beton", "Не проверено", "Бетон", "", "", "https://glotr.uz/showcase/ooo-nurafshon-beton-40062/", "Нет", "", ""),
    ("Best Beton", "Не проверено", "Бетон", "", "", "https://glotr.uz/showcase/best-beton-26890/", "Нет", "", "Регион не подтверждён"),
    ("Orient Construction Services Group", "Не проверено", "Бетон", "Ташкент", "", "https://www.prom.uz/company/orient-construction-services-group/beton/", "Нет", "", ""),
    ("Olmos Blok", "Не проверено", "Бетон", "", "", "https://www.prom.uz/company/olmos-blok/", "Нет", "", "Цена М300/М350 — договорная"),
    ("Alyans-Neo-Prom", "Не проверено", "Бетон", "", "", "https://www.prom.uz/company/alyans-neo-prom-12386/beton/", "Нет", "", ""),
    ("SPK Metall Industry", "Не проверено", "Арматура", "Ташкент", "", "https://www.prom.uz/company/spk-metall-industry/armatura/", "Нет", "", ""),
    ("Metall Kent", "Не проверено", "Арматура", "", "", "https://www.prom.uz/company/metall-kent-1/armatura/", "Нет", "", ""),
    ("Matiyn Metall", "Не проверено", "Арматура", "", "", "https://www.prom.uz/company/matiyn-metall-1/", "Нет", "", ""),
    ("Metal City", "Не проверено", "Арматура", "", "", "glotr.uz", "Нет", "", ""),
    ("Modern Inshaat", "Не проверено", "Газоблок", "", "", "https://www.prom.uz/company/modern-inshaat/", "Нет", "", "D500 / D600 / D700"),
    ("BSgroup Gazobeton", "Не проверено", "Газоблок", "", "", "https://www.prom.uz/section/gazobetonnye-bloki/", "Нет", "", ""),
    ("GAGARIN GB", "Не проверено", "Газоблок", "", "", "https://www.goldenpages.uz/rubrics/?Id=108181", "Нет", "", "В рубрике «Автоклавный газобетон»"),
    ("FERETON", "Не проверено", "Газоблок", "", "", "https://www.goldenpages.uz/rubrics/?Id=108181", "Нет", "", "В рубрике «Автоклавный газобетон»"),
    ("ZEN (газоблок)", "Не проверено", "Газоблок", "", "", "https://www.olx.uz/d/obyavlenie/avtoklavnyy-gazablok-539-000-tys-zen-ID47vo5.html", "Нет", "", ""),
    ("ТехноНИКОЛЬ (Ангрен)", "Не проверено", "Пеноплекс (XPS)", "Ташкентская обл., г. Ангрен", "", "Анонсирован завод XPS в Ангрене — статус запуска уточнить", "Нет", "", "Если завод работает — прямой производитель XPS"),
    ("Thermozon", "Не проверено", "Пеноплекс (XPS)", "Ташкент", "", "https://www.prom.uz/company/thermozon/", "Нет", "", ""),
    ("AKFA / IMZO (офиц. дистрибьютор)", "Не проверено", "Окна", "", "", "glotr.uz / prom.uz", "Нет", "", "Профиль AKFA — производитель РУз"),
    ("Vitrokon Lux (Ангрен)", "Не проверено", "Окна", "Ангрен, доставка в Ташкент", "", "https://www.prom.uz/section/okna/", "Нет", "", ""),
    ("Winplast System", "Не проверено", "Окна", "", "", "https://www.prom.uz/company/winplast-system/", "Нет", "", ""),
    ("UMID I YA (ЧПКФ)", "Не проверено", "Окна", "Ташкент, Яшнабадский р-н", "", "https://www.goldenpages.uz/rubrics/?Id=107628", "Нет", "", "В каталоге указан как производитель"),
    ("Неизвестный продавец (объявление)", "Не проверено", "Все", "", "", "", "Нет", "", "Для цен из объявлений без названия продавца"),
]
from prices import NEW_SUP
_known = {x[0] for x in suppliers}
for n in NEW_SUP:
    if n == "Биржа UZEX (средневзвеш.)":
        suppliers.append((n, "Завод-производитель", "Цемент, металл", "", "", "https://uzex.uz", "Да", "", "Биржевая цена заводов-производителей, без доставки"))
    elif n not in _known:
        suppliers.append((n, "Не проверено", "", "", "", "stroyka.uz / prom.uz / glotr.uz", "Нет", "", "Добавлен при сборе цен 23.11.2026"))
for s in suppliers:
    sup.append(list(s))
for c in sup[1]:
    c.fill, c.font, c.alignment, c.border = HDR_FILL, HDR_FONT, CENTER, BORDER
for row in sup.iter_rows(min_row=2, max_row=300):
    for c in row:
        c.font, c.border, c.alignment = BLUE, BORDER, WRAP
for col, w in zip("ABCDEFGHI", [34, 22, 18, 26, 20, 44, 14, 30, 36]):
    sup.column_dimensions[col].width = w
sup.freeze_panes = "B2"
dv_type = DataValidation(type="list", formula1='"' + ",".join(TYPES) + '"', allow_blank=True)
sup.add_data_validation(dv_type); dv_type.add("B2:B300")
dv_yn = DataValidation(type="list", formula1='"Да,Нет"', allow_blank=True)
sup.add_data_validation(dv_yn); dv_yn.add("G2:G300")
sup.conditional_formatting.add("B2:B300", FormulaRule(formula=['$B2="Завод-производитель"'], fill=PatternFill("solid", fgColor="C6EFCE")))
sup.conditional_formatting.add("B2:B300", FormulaRule(formula=['$B2="Склад/дистрибьютор"'], fill=PatternFill("solid", fgColor="DDEBF7")))
sup.conditional_formatting.add("B2:B300", FormulaRule(formula=['OR($B2="Перекупщик",$B2="Частник")'], fill=PatternFill("solid", fgColor="FCE4D6")))

# ---------------- Журнал цен ----------------
j = wb.create_sheet("Журнал цен")
heads = ["Дата", "Позиция", "Категория", "Базовая ед.", "Поставщик", "Тип поставщика",
         "Цена в прайсе, сум", "Ед. в прайсе", "Коэф. пересчёта (ед. прайса в 1 баз. ед.)",
         "Цена за баз. ед., сум", "НДС включён", "Доставка включена", "Наличие", "Источник",
         "Ссылка / контакт", "Комментарий", "Прямой (завод/склад)", "ключ"]
j.append(heads)
for c in j[1]:
    c.fill, c.font, c.alignment, c.border = HDR_FILL, HDR_FONT, CENTER, BORDER
j.row_dimensions[1].height = 45
d = date(2026, 11, 23)
U = "Объявление"
from prices import R as samples, d
for i, s in enumerate(samples, start=2):
    p, su, price, unit, coef, vat, dlv, avail, src, link, com = s
    dt = d
    j[f"A{i}"], j[f"B{i}"], j[f"E{i}"], j[f"G{i}"], j[f"H{i}"] = dt, p, su, price, unit
    if coef: j[f"I{i}"] = coef
    j[f"K{i}"], j[f"L{i}"], j[f"M{i}"], j[f"N{i}"], j[f"O{i}"], j[f"P{i}"] = vat, dlv, avail, src, link, com
for r in range(2, N_ROWS + 2):
    j[f"C{r}"] = f'=IF(B{r}="","",IFERROR(INDEX(Позиции!$A:$A,MATCH(B{r},Позиции!$B:$B,0)),"нет в справочнике"))'
    j[f"D{r}"] = f'=IF(B{r}="","",IFERROR(INDEX(Позиции!$C:$C,MATCH(B{r},Позиции!$B:$B,0)),""))'
    j[f"F{r}"] = f'=IF(E{r}="","",IFERROR(INDEX(Поставщики!$B:$B,MATCH(E{r},Поставщики!$A:$A,0)),"нет в реестре"))'
    j[f"J{r}"] = f'=IF(G{r}="","",G{r}*IF(I{r}="",1,I{r}))'
    j[f"Q{r}"] = f'=IF(OR(F{r}="Завод-производитель",F{r}="Склад/дистрибьютор"),"Да","Нет")'
    j[f"R{r}"] = f'=IF(J{r}="","",B{r}&"|"&J{r}&"|"&Q{r})'
    for col in "ABCDEFGHIJKLMNOPQR":
        c = j[f"{col}{r}"]
        c.border = BORDER
        c.font = BLACK if col in "CDFJQR" else BLUE
        if col in "CDFJQ":
            c.fill = CALC_FILL
    j[f"A{r}"].number_format = DFMT
    j[f"G{r}"].number_format = NUM
    j[f"J{r}"].number_format = NUM
    j[f"I{r}"].number_format = "0.00"
for col, w in zip("ABCDEFGHIJKLMNOPQR", [12, 40, 16, 9, 32, 20, 15, 14, 14, 15, 9, 10, 10, 13, 34, 44, 10, 6]):
    j.column_dimensions[col].width = w
j.column_dimensions["R"].hidden = True
j.freeze_panes = "C2"
j.auto_filter.ref = f"A1:Q{N_ROWS+1}"
rng = f"{N_ROWS+1}"
for ref, f1 in [(f"B2:B{rng}", "=Позиции!$B$2:$B$500"), (f"E2:E{rng}", "=Поставщики!$A$2:$A$300"),
                (f"K2:L{rng}", '"Да,Нет"'), (f"M2:M{rng}", '"Есть,Нет,Под заказ"'),
                (f"N2:N{rng}", '"Звонок,КП (письменное),Сайт,Объявление,Биржа UZEX,Визит"')]:
    dv = DataValidation(type="list", formula1=f1, allow_blank=True)
    j.add_data_validation(dv); dv.add(ref)
j["I1"].comment = Comment("Сколько единиц из прайса входит в 1 базовую единицу.\nПример: XPS 50 мм лист 1200×600 → 27,78 листа в 1 м³.\nПусто = 1 (прайс уже в базовой ед.).", "Снабжение")
j.conditional_formatting.add(f"F2:F{rng}", FormulaRule(formula=['$F2="Завод-производитель"'], fill=PatternFill("solid", fgColor="C6EFCE")))
j.conditional_formatting.add(f"F2:F{rng}", FormulaRule(formula=['OR($F2="Перекупщик",$F2="Частник")'], fill=PatternFill("solid", fgColor="FCE4D6")))

# ---------------- Сводка ----------------
s = wb.create_sheet("Сводка", 0)
s["A1"] = "Ежедневная сводка цен — ЖК, г. Ташкент"
s["A1"].font = Font(name=F, bold=True, size=14, color="1F3864")
s["A3"], s["B3"] = "Дата отчёта", "=TODAY()"
s["A4"], s["B4"] = "Период анализа, дней", 30
s["A5"], s["B5"] = "Начало периода", "=B3-B4"
s["A6"], s["B6"] = "Порог тревоги по изменению", 0.03
for a in ["A3", "A4", "A5", "A6"]:
    s[a].font = BOLD
s["B3"].number_format = DFMT; s["B5"].number_format = DFMT; s["B6"].number_format = "0%"
s["B3"].font = BLACK; s["B5"].font = BLACK
s["B4"].font = BLUE; s["B6"].font = BLUE
s["B4"].fill = INPUT_FILL; s["B6"].fill = INPUT_FILL
s["D3"] = "Жёлтые ячейки можно менять. Все цены — в сумах за базовую единицу (м³, т, м² …)."
s["D4"] = "«Прямые» = поставщики с типом «Завод-производитель» или «Склад/дистрибьютор» в листе «Поставщики»."
s["D6"] = "Фильтр в колонке «Как часто проверять»: «Ежедневно» — короткий список на утро, остальное — раз в неделю / месяц."
s["D5"] = "Изменение = последняя средняя цена дня к предыдущей дате, когда была цена. Красный — рост выше порога, зелёный — снижение."
for a in ["D3", "D4", "D5", "D6"]:
    s[a].font = Font(name=F, italic=True, size=9, color="595959")

H = 8
sh = ["Категория", "Позиция", "Ед.", "Цен за период", "Мин. цена (все), сум", "У кого (все)",
      "Мин. цена — заводы/склады, сум", "У кого (прямые)", "Средняя за период, сум",
      "Последняя дата", "Последняя цена (ср. дня), сум", "Предыдущая дата", "Предыдущая цена, сум", "Изменение", "Как часто проверять", "Этап стройки"]
for ci, t in enumerate(sh, start=1):
    c = s.cell(row=H, column=ci, value=t)
    c.fill, c.font, c.alignment, c.border = HDR_FILL, HDR_FONT, CENTER, BORDER
s.row_dimensions[H].height = 45
JR = f"$2:$" + str(N_ROWS + 1)
def jc(col):
    return f"'Журнал цен'!${col}$2:${col}${N_ROWS+1}"
JA, JB, JE, JJ, JQ, JRk = jc("A"), jc("B"), jc("E"), jc("J"), jc("Q"), jc("R")
cur_cat = None
for idx, (cat, name, unit, _, stage, freq) in enumerate(positions):
    r = H + 1 + idx
    pr = idx + 2
    s[f"A{r}"] = f"=Позиции!A{pr}"
    s[f"B{r}"] = f"=Позиции!B{pr}"
    s[f"C{r}"] = f"=Позиции!C{pr}"
    s[f"D{r}"] = f'=COUNTIFS({JB},B{r},{JA},">="&$B$5,{JA},"<="&$B$3,{JJ},">0")'
    s[f"E{r}"] = f'=IF(D{r}=0,"",_xlfn.MINIFS({JJ},{JB},B{r},{JA},">="&$B$5,{JA},"<="&$B$3,{JJ},">0"))'
    s[f"F{r}"] = f'=IF(E{r}="","",IFERROR(INDEX({JE},MATCH(B{r}&"|"&E{r}&"|*",{JRk},0)),""))'
    s[f"G{r}"] = f'=IF(COUNTIFS({JB},B{r},{JA},">="&$B$5,{JA},"<="&$B$3,{JJ},">0",{JQ},"Да")=0,"",_xlfn.MINIFS({JJ},{JB},B{r},{JA},">="&$B$5,{JA},"<="&$B$3,{JJ},">0",{JQ},"Да"))'
    s[f"H{r}"] = f'=IF(G{r}="","",IFERROR(INDEX({JE},MATCH(B{r}&"|"&G{r}&"|Да",{JRk},0)),""))'
    s[f"I{r}"] = f'=IF(D{r}=0,"",AVERAGEIFS({JJ},{JB},B{r},{JA},">="&$B$5,{JA},"<="&$B$3,{JJ},">0"))'
    s[f"J{r}"] = f'=IF(COUNTIFS({JB},B{r},{JJ},">0")=0,"",_xlfn.MAXIFS({JA},{JB},B{r},{JJ},">0"))'
    s[f"K{r}"] = f'=IF(J{r}="","",AVERAGEIFS({JJ},{JB},B{r},{JA},J{r},{JJ},">0"))'
    s[f"L{r}"] = f'=IF(J{r}="","",IF(COUNTIFS({JB},B{r},{JA},"<"&J{r},{JJ},">0")=0,"",_xlfn.MAXIFS({JA},{JB},B{r},{JA},"<"&J{r},{JJ},">0")))'
    s[f"M{r}"] = f'=IF(L{r}="","",AVERAGEIFS({JJ},{JB},B{r},{JA},L{r},{JJ},">0"))'
    s[f"N{r}"] = f'=IF(OR(K{r}="",M{r}=""),"",K{r}/M{r}-1)'
    s[f"O{r}"] = f"=Позиции!F{pr}"
    s[f"P{r}"] = f"=Позиции!E{pr}"
    for col in "ABCDEFGHIJKLMNOP":
        c = s[f"{col}{r}"]
        c.font, c.border = BLACK, BORDER
    for col in "EGIKM":
        s[f"{col}{r}"].number_format = NUM
    for col in "JL":
        s[f"{col}{r}"].number_format = DFMT
    s[f"N{r}"].number_format = PCT
    if cat != cur_cat:
        for col in "ABCDEFGHIJKLMNOP":
            s[f"{col}{r}"].border = Border(left=thin, right=thin, bottom=thin, top=Side(style="medium", color="1F3864"))
        cur_cat = cat
LAST = H + len(positions)
s.conditional_formatting.add(f"N{H+1}:N{LAST}", FormulaRule(formula=[f'AND(ISNUMBER(N{H+1}),N{H+1}>$B$6)'], fill=PatternFill("solid", fgColor="FFC7CE"), font=Font(color="9C0006", bold=True)))
s.conditional_formatting.add(f"N{H+1}:N{LAST}", FormulaRule(formula=[f'AND(ISNUMBER(N{H+1}),N{H+1}<-$B$6)'], fill=PatternFill("solid", fgColor="C6EFCE"), font=Font(color="006100", bold=True)))
s.conditional_formatting.add(f"G{H+1}:H{LAST}", FormulaRule(formula=[f'$G{H+1}<>""'], fill=PatternFill("solid", fgColor="E2EFDA")))
for col, w in zip("ABCDEFGHIJKLMNOP", [22, 44, 7, 9, 15, 30, 16, 30, 15, 12, 16, 12, 15, 11, 14, 24]):
    s.column_dimensions[col].width = w
s.freeze_panes = f"C{H+1}"
s.auto_filter.ref = f"A{H}:P{LAST}"
s.conditional_formatting.add(f"O{H+1}:O{LAST}", FormulaRule(formula=[f'$O{H+1}="Ежедневно"'], fill=PatternFill("solid", fgColor="FFE699"), font=Font(bold=True)))

# ---------------- Инструкция ----------------
ins = wb.create_sheet("Инструкция")
lines = [
    ("Как пользоваться (5–10 минут в день)", True),
    ("0. В «Сводке» включите фильтр «Ежедневно» (бетон, арматура, цемент) — это утренний список. «Еженедельно» — по понедельникам, «Ежемесячно» — 1-го числа.", False),
    ("1. Утром обзвоните / проверьте поставщиков и внесите каждую полученную цену одной строкой в «Журнал цен».", False),
    ("   Синие ячейки — ввод, серые — считаются сами. Позицию и поставщика выбирайте из выпадающего списка.", False),
    ("2. Если цена в прайсе не за базовую единицу (за лист, за штуку, за поддон) — заполните «Коэф. пересчёта».", False),
    ("   Примеры: XPS 50 мм лист 1200×600 → 27,78 листа в м³; газоблок 600×300×200 → 27,78 шт в м³; арматура — сколько прутков в тонне.", False),
    ("3. Откройте «Сводку»: минимальная цена по всем и отдельно по заводам/складам, средняя за период, изменение к прошлой цене.", False),
    ("4. Новый поставщик → сначала добавьте его в «Поставщики» и укажите тип. Перекупщиков и частников помечайте честно —", False),
    ("   тогда колонка «Мин. цена — заводы/склады» покажет реальную цену без наценки посредника.", False),
    ("5. Цены из объявлений — только ориентир. Для решения о закупке нужна письменная КП (Источник = «КП (письменное)»).", False),
    ("", False),
    ("Как отличить завод/склад от перекупщика", True),
    ("• Попросите адрес производства или склада и приедьте / проверьте в 2GIS или Яндекс.Картах.", False),
    ("• Бетон: завод даёт паспорт на каждую партию и называет свой РБУ; перекупщик «везёт с разных заводов».", False),
    ("• Арматура: попросите сертификат качества с номером плавки — по нему видно завод-изготовитель (Узметкомбинат, импорт РФ/КЗ).", False),
    ("• Газоблок / XPS / окна: юр. лицо производителя на упаковке и в сертификате должно совпадать с продавцом либо он — официальный дилер.", False),
    ("• Проверьте ИНН (СТИР) продавца в открытых реестрах — вид деятельности «производство» или «оптовая торговля».", False),
    ("", False),
    ("Где искать цены по всему Ташкенту", True),
    ("• UZEX — Узбекская республиканская товарно-сырьевая биржа: биржевые цены на арматуру, цемент (база для торга).", False),
    ("• prom.uz, glotr.uz — каталоги компаний с прайсами; goldenpages.uz, yellowpages.uz — адреса и телефоны заводов.", False),
    ("• olx.uz — частники и мелкие склады (ориентир нижней границы рынка).", False),
    ("• 2GIS — поиск «бетонный завод», «газоблок завод», «металлобаза» по районам: Сергели, Бектемир, Янгихаёт, Чиланзар, Алмазар, Яшнабад.", False),
    ("", False),
    ("Важно", True),
    ("• Стартовые строки в «Журнале цен» — ориентиры из открытых объявлений на 23.11.2026, не проверенные звонком. Удалите или замените их своими.", False),
    ("• Поставщики в реестре найдены в открытых каталогах; тип у всех, кроме Узметкомбината, — «Не проверено», пока вы не проверите их сами.", False),
    ("• Если Excel не показывает формулы со «MINIFS/MAXIFS» — нужен Excel 2019 / Microsoft 365 (или Google Таблицы, LibreOffice).", False),
]
for i, (t, b) in enumerate(lines, start=1):
    c = ins.cell(row=i, column=1, value=t)
    c.font = Font(name=F, bold=b, size=12 if b else 10, color="1F3864" if b else "000000")
ins.column_dimensions["A"].width = 140

wb.move_sheet("Инструкция", offset=-(len(wb.sheetnames) - 1))
wb.active = 1
wb.save(OUT)
print("saved", OUT)
