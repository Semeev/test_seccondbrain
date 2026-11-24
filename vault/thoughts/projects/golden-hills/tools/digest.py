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
        # сравнение «тех же с теми же»: продавцы с ценой сегодня и раньше (их последняя прошлая цена)
        before = {}
        for dt in sorted(d for d in hist if d < D):
            for price, sup in hist[dt]:
                before[sup] = price
        today = {sup: price for price, sup in hist[D]}
        common = [today[s_] / before[s_] - 1 for s_ in today if s_ in before]
        if common:
            chg = sum(common) / len(common)
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
    if abs(c) < 0.0005:
        return '<span class="no">0%</span>'
    cls = "up" if c > 0.03 else "down" if c < -0.03 else ""
    return f'<span class="{cls}" style="white-space:nowrap">{c * 100:+.1f}%</span>'


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
notes.append("Красным в «Диапазоне» — разница между мин. и макс. больше 30%: здесь торг даст больше всего.")

TYPE = {"Завод-производитель": ("завод", "tz"), "Склад/дистрибьютор": ("склад", "tsk"), "Магазин (розница)": ("магазин", "tm"),
        "Перекупщик": ("трейдер", "tt")}


def who(sup):
    lab, cls = TYPE.get(stype.get(sup), ("не пров.", "tn"))
    return f'<span class="who">{e(sup)}</span> <span class="tag {cls}">{lab}</span>'


def fk(x):  # компактно: 8 610 тыс. / 470 тыс. / 13 600
    return f(x)


stage_ix = {}
for nm, st in stats.items():
    stage_ix.setdefault((st["stage"], st["cat"]), len(stage_ix))
ordered = sorted(stats.items(), key=lambda kv: (kv[1]["stage"].split(".")[0].zfill(3), stage_ix[(kv[1]["stage"], kv[1]["cat"])]))

rows, cur = "", None
for n, s in ordered:
    g = (s["stage"], s["cat"])
    if g != cur:
        rows += f'<tr class="grp"><td colspan="9">{e(g[0])} · {e(g[1])}</td></tr>'
        cur = g
    dot = '<span class="d">●</span> ' if s["freq"] == "Ежедневно" else ""
    dm, tr = s["dmn"], s["trade"]
    rng = "—" if s["n"] == 1 else f'{f(s["mn"][0])} – {f(s["mx"])}'
    hi = ' class="hi"' if s["spread"] is not None and s["spread"] > 0.3 else ""
    rng_html = f'<span{hi}>{rng}</span><span class="sm">{s["n"]} цен' + (f' · разброс {s["spread"]*100:.0f}%' if s["spread"] else "") + '</span>'
    dcell = f'<b>{f(dm[0])}</b><span class="sm">средн. {f(s["davg"])} · {s["dn"]} цен</span>' if dm else '<span class="no">нет цен</span>'
    gap = ""
    if tr:
        tm = min(tr, key=lambda x: x[0]); tav = sum(x[0] for x in tr) / len(tr)
        tcell = f'<b>{f(tm[0])}</b><span class="sm">средн. {f(tav)} · {len(tr)} цен</span>'
        if dm:
            g2 = tav / s["davg"] - 1
            gap = f'<span class="{"up" if g2 > 0.03 else "down" if g2 < -0.03 else ""}">{g2 * 100:+.0f}%</span>'
    else:
        tcell = '<span class="no">нет цен</span>'
    o = s["omn"]
    if o:
        d = o[0] / s["mn"][0] - 1
        our = (f'<b>{f(o[0])}</b> ' + (f'<span class="up">+{d * 100:.0f}%</span>' if d > 0.005 else '<span class="best">лучшая</span>')
               + f'<span class="sm">{e(o[1])}</span>')
    else:
        our = '<span class="no">—</span>'
    rows += (f'<tr><td class="pos">{dot}{e(n)} <span class="unit">{e(s["unit"])}</span></td>'
             f'<td class="best-c"><span class="big">{f(s["mn"][0])}</span>{who(s["mn"][1])}</td>'
             f'<td class="n">{f(s["avg"])}</td><td class="n">{rng_html}</td>'
             f'<td class="n dv">{dcell}</td><td class="n tv2">{tcell}</td><td class="n">{gap or "—"}</td>'
             f'<td class="n">{our}</td><td class="n">{chg_html(s["chg"])}</td></tr>')

nprice = sum(s["n"] for s in stats.values())
doc = f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><style>
@page {{ size: A4 landscape; margin: 12mm 12mm; }}
body {{ font-family: 'DejaVu Sans', Arial, sans-serif; color:#1a1a1a; font-size:8.6pt; }}
h1 {{ font-size:16pt; margin:0; color:#1F3864; }} .sub {{ color:#555; margin:2px 0 10px; }}
.tiles {{ display:grid; grid-template-columns:repeat(7,1fr); gap:6px; margin-bottom:10px; }}
.tile {{ border:1px solid #d0d7e2; border-radius:4px; padding:6px 8px; }} .tl {{ color:#555; font-size:8pt; }}
.tv {{ font-size:14pt; font-weight:bold; color:#1F3864; }} .ts {{ color:#666; font-size:7.4pt; }}
h2 {{ font-size:10.5pt; color:#1F3864; margin:12px 0 4px; }}
table {{ width:100%; border-collapse:collapse; table-layout:fixed; font-size:8.2pt; }}
th {{ background:#1F3864; color:#fff; text-align:left; padding:5px 4px; font-size:7.4pt; font-weight:bold; vertical-align:bottom; }}
th.r {{ text-align:right; }} th.dh {{ background:#2e6b34; }} th.th2 {{ background:#9a5b13; }} .thu {{ font-weight:normal; opacity:.75; }}
td {{ border-bottom:1px solid #e6e6e6; padding:5px 4px; vertical-align:middle; overflow-wrap:anywhere; }}
tr:nth-child(even) td {{ background-color:#fafbfc; }}
.n {{ text-align:right; }} .pos {{ font-weight:bold; }} .unit {{ font-weight:normal; color:#888; font-size:7pt; }}
.big {{ display:block; font-size:10.5pt; font-weight:bold; color:#1F3864; }} .who {{ color:#444; font-size:7pt; }}
.tag {{ font-size:6.2pt; padding:0 4px; border-radius:6px; white-space:nowrap; }} .tz {{ background:#d8f0dc; color:#1e6b2e; }} .tsk {{ background:#dceaf8; color:#1d4f8a; }}
.tm {{ background:#fbe8d3; color:#8a4b0f; }} .tt {{ background:#f8d7da; color:#8a1c25; }} .tn {{ background:#eee; color:#666; }}
tr.grp td {{ background:#1F3864 !important; color:#fff; font-weight:bold; font-size:8pt; padding:4px 6px; }}
.hi {{ color:#b00020; font-weight:bold; }} .d {{ color:#d4a017; }} .no {{ color:#bbb; font-size:7pt; }}
.sm {{ display:block; color:#777; font-size:6.6pt; font-weight:normal; line-height:1.2; }}
td.dv {{ background-color:#f3f9f1 !important; }} td.tv2 {{ background-color:#fdf6ee !important; }}
.up {{ color:#b00020; font-weight:bold; }} .down {{ color:#1e7b34; font-weight:bold; }} .best {{ color:#1e7b34; font-weight:bold; }}
ul {{ margin:4px 0 0 16px; padding:0; }} li {{ margin-bottom:3px; }} .note {{ color:#555; font-size:7.6pt; }} tr {{ page-break-inside:avoid; }}
</style></head><body>
<h1>Сводка цен на стройматериалы — весь рынок Ташкента</h1>
<div class="sub">Ташкент · {D:%d.%m.%Y} · {nprice} цен по {len(stats)} позициям (последняя цена каждого поставщика за {WINDOW} дней) · все цены в сумах</div>
<div class="tiles">{tiles}</div>
<h2>Что важно сегодня</h2><ul>{''.join(f'<li>{n}</li>' for n in notes)}</ul>
<h2>Цены по позициям</h2>
<table><colgroup><col style="width:20%"><col style="width:17%"><col style="width:8%"><col style="width:12%"><col style="width:11%"><col style="width:11%"><col style="width:6%"><col style="width:11%"><col style="width:4%"></colgroup><thead>
<tr><th>Позиция <span class="thu">ед.</span></th><th>Лучшая цена · у кого</th><th class="r">Средняя по рынку</th><th class="r">Диапазон мин–макс</th><th class="r dh">Заводы и склады</th><th class="r th2">Магазины и трейдеры</th><th class="r">Посредники дороже на</th><th class="r">Наша лучшая КП</th><th class="r">Изм.</th></tr></thead>
<tbody>{rows}</tbody></table>
<p class="note"><b>Как читать:</b> «Лучшая цена» — минимум по всему рынку и кто его даёт (метка: завод / склад / магазин / трейдер / не проверен). «Средняя» и «Диапазон» — по всем продавцам за 30 дней (последняя цена каждого). Зелёная колонка — только заводы, склады и официальные дистрибьюторы; оранжевая — магазины, трейдеры и непроверенные. «Посредники дороже на» — средняя у магазинов/трейдеров к средней у заводов/складов. «Наша лучшая КП» — лучшая цена от ваших поставщиков и насколько она выше рыночного минимума. «Изм.» — изменение у тех же продавцов к их прошлой цене. ● — позиции ежедневной проверки. Цены из объявлений — ориентир; для закупки нужна письменная КП.</p>
</body></html>"""
tmp = os.path.splitext(a.pdf)[0] + ".html"
open(tmp, "w", encoding="utf-8").write(doc)
here = os.path.dirname(os.path.abspath(__file__))
subprocess.run(["node", os.path.join(here, "render_pdf.js"), a.pdf, tmp], check=True)
os.remove(tmp)
print("PDF:", a.pdf)
