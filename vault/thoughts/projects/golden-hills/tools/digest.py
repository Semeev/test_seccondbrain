"""PDF-сводка цен за день по данным «Журнала цен».

Использование:
    python digest.py ../Мониторинг_цен_Ташкент.xlsx ../сводки/Сводка_цен_2026-11-24.pdf [--date 2026-11-24] [--notes notes.txt]

Файл нужно сначала пересчитать (recalc.py), иначе формулы без значений.
notes.txt — выводы дня, по одному на строку (можно <b>жирный</b>).
Изменение считается: средняя цена позиции за выбранный день к средней за предыдущую дату с ценами.
"""
import argparse
import html
import os
import subprocess
from collections import OrderedDict, defaultdict
from datetime import date, datetime, timedelta
WINDOW = 30

from openpyxl import load_workbook

ap = argparse.ArgumentParser()
ap.add_argument("xlsx")
ap.add_argument("pdf")
ap.add_argument("--date")
ap.add_argument("--notes")
a = ap.parse_args()

wb = load_workbook(a.xlsx, data_only=True)
pos = OrderedDict((r[1], (r[0], r[2], r[4], r[5])) for r in wb["Позиции"].iter_rows(min_row=2, values_only=True) if r[1])
stype = {r[0]: r[1] for r in wb["Поставщики"].iter_rows(min_row=2, values_only=True) if r[0]}
ours = {r[0] for r in wb["Поставщики"].iter_rows(min_row=2, values_only=True) if r[0] and len(r) > 9 and r[9] == "Да"}


def as_date(v):
    return v.date() if isinstance(v, datetime) else v


by = defaultdict(lambda: defaultdict(list))  # position -> date -> [(price, supplier)]
for r in wb["Журнал цен"].iter_rows(min_row=2, values_only=True):
    if r[1] and r[0] and isinstance(r[9], (int, float)) and r[9] > 0:
        by[r[1]][as_date(r[0])].append((r[9], r[4]))
all_dates = sorted({d for p in by.values() for d in p})
D = datetime.strptime(a.date, "%Y-%m-%d").date() if a.date else all_dates[-1]


def f(x):
    return f"{x:,.0f}".replace(",", " ")


e = html.escape
stats = OrderedDict()
for name, (cat, unit, stage, freq) in pos.items():
    hist = by.get(name, {})
    latest = {}
    for dt in sorted(hist):
        if D - timedelta(days=WINDOW) <= dt <= D:
            for price, sup in hist[dt]:
                latest[sup] = (price, sup)
    if not latest:
        continue
    day = list(latest.values())
    v = [x[0] for x in day]
    mn = min(day, key=lambda x: x[0])
    our = [x for x in day if x[1] in ours]
    omn = min(our, key=lambda x: x[0]) if our else None
    prev = [d for d in hist if d < D]
    chg = None
    if D in hist and prev:
        dv = [x[0] for x in hist[D]]
        pv = [x[0] for x in hist[max(prev)]]
        chg = (sum(dv) / len(dv)) / (sum(pv) / len(pv)) - 1
    direct = [x for x in day if stype.get(x[1]) in ("Завод-производитель", "Склад/дистрибьютор")]
    stats[name] = dict(cat=cat, unit=unit, stage=stage, freq=freq, n=len(v), mn=mn, avg=sum(v) / len(v), mx=max(v),
                       spread=(max(v) / min(v) - 1) if len(v) > 1 else None, chg=chg,
                       dmn=min(direct, key=lambda x: x[0]) if direct else None, omn=omn,
                       dn=len(direct), davg=(sum(x[0] for x in direct) / len(direct)) if direct else None,
                       dmx=max(x[0] for x in direct) if direct else None,
                       trade=[x for x in day if x not in direct])

KEY = [("Бетон М300 (B22,5)", "Бетон М300"), ("Бетон М350 (B25)", "Бетон М350"), ("Арматура А500С d12", "Арматура А500С d12"),
       ("Цемент ПЦ 400 Д20 (навал)", "Цемент ПЦ 400 навал"), ("Газоблок автоклавный D500 (толщина не указана)", "Газоблок D500"),
       ("Пеноплекс / XPS 50 мм", "XPS 50 мм"), ("ПГС (шагал) несортированный, карьерный", "ПГС (шагал)")]


def chg_html(c):
    if c is None:
        return "—"
    cls = "up" if c > 0.03 else "down" if c < -0.03 else ""
    return f'<span class="{cls}">{c * 100:+.1f}%</span>'


def ours_html(s):
    o = s["omn"]
    if not o:
        return "—"
    d = o[0] / s["mn"][0] - 1
    tag = f' <span class="up">+{d * 100:.0f}% к мин.</span>' if d > 0.005 else ' <span class="down">лучшая</span>'
    return f'{f(o[0])}{tag}<br><span class="sm">{e(o[1])}</span>'


tiles = ""
for k, lbl in KEY:
    if k in stats:
        s = stats[k]
        tiles += (f'<div class="tile"><div class="tl">{e(lbl)}</div><div class="tv">{f(s["mn"][0])}</div>'
                  f'<div class="ts">мин., сум/{e(s["unit"])} · средн. {f(s["avg"])} · {s["n"]} цен · изм. {chg_html(s["chg"])}</div></div>')

notes = []
if a.notes and os.path.exists(a.notes):
    notes = [ln.strip() for ln in open(a.notes, encoding="utf-8") if ln.strip()]
moves = sorted([(n, s) for n, s in stats.items() if s["chg"] is not None and abs(s["chg"]) > 0.03], key=lambda x: -abs(x[1]["chg"]))
for n, s in moves[:6]:
    word = "подорожала" if s["chg"] > 0 else "подешевела"
    notes.append(f"<b>{e(n)}</b> {word} на {abs(s['chg']) * 100:.1f}% (средняя {f(s['avg'])} сум/{e(s['unit'])}).")
if not any(s["chg"] is not None for s in stats.values()):
    notes.append("Это первый день ведения журнала: изменения к прошлому дню появятся со следующей сводки.")
notes.append("Красным в колонке «Разброс» — разница между мин. и макс. ценой больше 30%: здесь торг даст больше всего.")

rows, cur = "", None
for n, s in stats.items():
    g = (s["stage"], s["cat"])
    if g != cur:
        rows += f'<tr class="grp"><td colspan="16">{e(g[0])} — {e(g[1])}</td></tr>'
        cur = g
    sp = f'{s["spread"] * 100:.0f}%' if s["spread"] is not None else "—"
    hi = " hi" if s["spread"] is not None and s["spread"] > 0.3 else ""
    dot = '<span class="d">●</span> ' if s["freq"] == "Ежедневно" else ""
    dm, tr = s["dmn"], s["trade"]
    dcells = (f'<td class="n dv">{s["dn"]}</td><td class="n b dv">{f(dm[0])}<br><span class="sm">{e(dm[1])}</span></td>'
              f'<td class="n dv">{f(s["davg"])}</td>') if dm else '<td class="n dv" colspan="3"><span class="sm">нет цен</span></td>'
    if tr:
        tm = min(tr, key=lambda x: x[0]); tav = sum(x[0] for x in tr) / len(tr)
        tcells = (f'<td class="n tv2">{len(tr)}</td><td class="n b tv2">{f(tm[0])}<br><span class="sm">{e(tm[1])}</span></td>'
                  f'<td class="n tv2">{f(tav)}</td>')
    else:
        tcells = '<td class="n tv2" colspan="3"><span class="sm">нет цен</span></td>'
    gap = "—"
    if dm and tr:
        g2 = tav / s["davg"] - 1
        gap = f'<span class="{"up" if g2 > 0.03 else "down" if g2 < -0.03 else ""}">{g2 * 100:+.0f}%</span>'
    rows += (f'<tr><td>{dot}{e(n)}</td><td>{e(s["unit"])}</td><td class="n">{s["n"]}</td><td class="n b">{f(s["mn"][0])}<br><span class="sm">{e(s["mn"][1])}</span></td>'
             f'<td class="n b">{f(s["avg"])}</td><td class="n">{f(s["mx"])}</td>'
             f'<td class="n{hi}">{sp}</td>{dcells}{tcells}<td class="n">{gap}</td><td class="n">{ours_html(s)}</td><td class="n">{chg_html(s["chg"])}</td></tr>')

nprice = sum(s["n"] for s in stats.values())
doc = f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><style>
@page {{ size: A4 landscape; margin: 12mm 12mm; }}
body {{ font-family: 'DejaVu Sans', Arial, sans-serif; color:#1a1a1a; font-size:8.6pt; }}
h1 {{ font-size:16pt; margin:0; color:#1F3864; }} .sub {{ color:#555; margin:2px 0 10px; }}
.tiles {{ display:grid; grid-template-columns:repeat(7,1fr); gap:6px; margin-bottom:10px; }}
.tile {{ border:1px solid #d0d7e2; border-radius:4px; padding:6px 8px; }} .tl {{ color:#555; font-size:8pt; }}
.tv {{ font-size:14pt; font-weight:bold; color:#1F3864; }} .ts {{ color:#666; font-size:7.4pt; }}
h2 {{ font-size:10.5pt; color:#1F3864; margin:12px 0 4px; }}
table {{ width:100%; border-collapse:collapse; }} th {{ background:#1F3864; color:#fff; text-align:left; padding:4px; font-size:7.8pt; }}
td {{ border-bottom:1px solid #e3e3e3; padding:3px 4px; vertical-align:top; }} .n {{ text-align:right; white-space:nowrap; }} .b {{ font-weight:bold; }}
tr.grp td {{ background:#eef2f8; font-weight:bold; color:#1F3864; }} .hi {{ color:#b00020; font-weight:bold; }} .d {{ color:#d4a017; }} .sm {{ color:#666; font-size:7pt; }}
.dv {{ background:#f1f8ec; }} .tv2 {{ background:#fdf3e7; }} th.th2 {{ background:#9a5b13; }} th.dh {{ background:#2e6b34; }} th.c {{ text-align:center; }} .up {{ color:#b00020; font-weight:bold; }} .down {{ color:#1e7b34; font-weight:bold; }}
ul {{ margin:4px 0 0 16px; padding:0; }} li {{ margin-bottom:3px; }} .note {{ color:#555; font-size:7.6pt; }} tr {{ page-break-inside:avoid; }}
</style></head><body>
<h1>Сводка цен на стройматериалы — весь рынок Ташкента</h1>
<div class="sub">Ташкент · {D:%d.%m.%Y} · {nprice} цен по {len(stats)} позициям (последняя цена каждого поставщика за {WINDOW} дней) · все цены в сумах</div>
<div class="tiles">{tiles}</div>
<h2>Что важно сегодня</h2><ul>{''.join(f'<li>{n}</li>' for n in notes)}</ul>
<h2>Цены по позициям</h2>
<table><thead><tr><th rowspan="2" style="width:17%">Позиция</th><th rowspan="2">Ед.</th><th colspan="5" class="c">Весь рынок (все продавцы)</th><th colspan="3" class="c dh">Заводы, склады, дистрибьюторы</th><th colspan="3" class="c th2">Магазины, трейдеры, прочие</th><th rowspan="2">Наценка посредников</th><th rowspan="2" style="width:11%">Наши поставщики (мин.)</th><th rowspan="2">Изм.</th></tr>
<tr><th>Цен</th><th>Мин. / у кого</th><th>Средняя</th><th>Макс.</th><th>Разброс</th><th class="dh">Цен</th><th class="dh">Мин. / у кого</th><th class="dh">Средняя</th><th class="th2">Цен</th><th class="th2">Мин. / у кого</th><th class="th2">Средняя</th></tr></thead>
<tbody>{rows}</tbody></table>
<p class="note">«Весь рынок» — все продавцы: заводы, склады, дистрибьюторы, трейдеры, строительные магазины, объявления. «Заводы, склады, дистрибьюторы» — с подтверждённым основанием в реестре (адрес производства/склада, официальный прайс). «Магазины, трейдеры, прочие» — магазины, перекупщики и ещё не проверенные продавцы. «Наценка посредников» — средняя цена магазинов/трейдеров к средней цене заводов/складов. ● — позиции ежедневной проверки. «Наши поставщики» — лучшая цена от поставщиков с отметкой «Работаем = Да» и насколько она выше рыночного минимума. «Изм.» — средняя цена дня к предыдущей дате, когда по позиции были цены (красный — рост больше 3%, зелёный — снижение).<br>
Цены из открытых объявлений и сайтов поставщиков — ориентир; для закупки нужна письменная КП.</p>
</body></html>"""
tmp = os.path.splitext(a.pdf)[0] + ".html"
open(tmp, "w", encoding="utf-8").write(doc)
here = os.path.dirname(os.path.abspath(__file__))
subprocess.run(["node", os.path.join(here, "render_pdf.js"), a.pdf, tmp], check=True)
os.remove(tmp)
print("PDF:", a.pdf)
