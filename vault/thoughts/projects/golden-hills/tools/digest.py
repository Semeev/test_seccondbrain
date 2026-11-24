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
                       trade=[x for x in day if x not in direct], day=day)

KEY = ["Бетон М300 (B22,5)", "Бетон М350 (B25)", "Бетон М400 (B30)", "Арматура А500С d12", "Арматура А500С d16", "Арматура А500С d20",
       "Арматура А400 d12", "Цемент ПЦ 400 Д20 (навал)", "Цемент ПЦ 400 в мешках 50 кг", "Газоблок автоклавный D500 (толщина не указана)",
       "Пеноплекс / XPS 50 мм", "ПГС (шагал) несортированный, карьерный", "Щебень фр. 5–20", "Мембрана ПВХ армированная 1,5 мм",
       "Монтаж кровли из мембраны под ключ (по плоскости)"]
TYPE = {"Завод-производитель": ("завод", "tz"), "Склад/дистрибьютор": ("склад", "tsk"), "Магазин (розница)": ("магазин", "tm"),
        "Перекупщик": ("трейдер", "tt")}


def chg_html(c):
    if c is None:
        return '<span class="no">—</span>'
    if abs(c) < 0.0005:
        return '<span class="no">0%</span>'
    cls = "up" if c > 0.03 else "down" if c < -0.03 else ""
    return f'<span class="{cls}" style="white-space:nowrap">{c * 100:+.1f}%</span>'


def who(sup):
    lab, cls = TYPE.get(stype.get(sup), ("не пров.", "tn"))
    return f'<span class="who">{e(sup)}</span> <span class="tag {cls}">{lab}</span>'


def short(n):
    return (n.replace(" (толщина не указана)", "").replace(" несортированный, карьерный", " карьерный").replace("Цемент ПЦ 400 Д20 (навал)", "Цемент ПЦ 400 навал")
             .replace("Монтаж кровли из мембраны под ключ (по плоскости)", "Монтаж кровли (мембрана), м²").replace("Газоблок автоклавный", "Газоблок"))


def our_html(s, small=False):
    o = s["omn"]
    if not o:
        return '<span class="no">—</span>'
    d = o[0] / s["mn"][0] - 1
    tag = f'<span class="up">+{d * 100:.0f}%</span>' if d > 0.005 else '<span class="best">лучшая</span>'
    return f'<b>{f(o[0])}</b> {tag}' + ('' if small else f'<span class="sm">{e(o[1])}</span>')


def gap_html(s):
    tr = s["trade"]
    if not (tr and s["davg"]):
        return '<span class="no">—</span>'
    g = (sum(x[0] for x in tr) / len(tr)) / s["davg"] - 1
    return f'<span class="{"up" if g > 0.03 else "down" if g < -0.03 else "no"}">{g * 100:+.0f}%</span>'


# --- страница 1: главное
key_rows = ""
for k in KEY:
    if k not in stats:
        continue
    s = stats[k]
    rng = "" if s["n"] == 1 else f'<span class="sm rng" style="display:block">{f(s["mn"][0])}–{f(s["mx"])} · {s["n"]}</span>'
    key_rows += (f'<tr><td class="pos">{e(short(k))} <span class="unit">{e(s["unit"])}</span></td>'
                 f'<td><span class="big">{f(s["mn"][0])}</span>{who(s["mn"][1])}</td>'
                 f'<td class="n"><b>{f(s["avg"])}</b>{rng}</td><td class="n">{our_html(s, small=True)}</td><td class="n">{chg_html(s["chg"])}</td></tr>')

save = []
for n, s in stats.items():
    o = s["omn"]
    if not o:
        continue
    known = [(p_, sp) for sp, (p_, _) in ((x[1], x) for x in s["day"]) if stype.get(sp) in TYPE]
    if not known:
        continue
    km = min(known)
    if o[0] > km[0] * 1.05 and km[1] not in ours:
        save.append((o[0] / km[0] - 1, n, s, km))
save.sort(key=lambda x: -x[0])
save_rows = "".join(
    f'<tr><td class="pos">{e(short(n))} <span class="unit">{e(s["unit"])}</span></td><td class="n">{f(s["omn"][0])}<span class="sm">{e(s["omn"][1])}</span></td>'
    f'<td class="n"><b>{f(km[0])}</b><span class="sm">{e(km[1])} · {TYPE[stype.get(km[1])][0]}</span></td>'
    f'<td class="n up">+{d * 100:.0f}%</td></tr>' for d, n, s, km in save[:8]) or '<tr><td colspan="4" class="no">Ваши КП везде на уровне рыночного минимума</td></tr>'

notes = []
if a.notes and os.path.exists(a.notes):
    notes = [ln.strip() for ln in open(a.notes, encoding="utf-8") if ln.strip()]
moves = sorted([(n, s) for n, s in stats.items() if s["chg"] is not None and abs(s["chg"]) > 0.03], key=lambda x: -abs(x[1]["chg"]))
auto = [f"<b>{e(short(n))}</b> {'подорожала' if s['chg'] > 0 else 'подешевела'} на {abs(s['chg']) * 100:.1f}% у тех же продавцов." for n, s in moves[:3]]
notes = (auto + notes)[:5]

# --- полный список
stage_ix = {}
for nm, st in stats.items():
    stage_ix.setdefault((st["stage"], st["cat"]), len(stage_ix))
ordered = sorted(stats.items(), key=lambda kv: (kv[1]["stage"].split(".")[0].zfill(3), stage_ix[(kv[1]["stage"], kv[1]["cat"])]))
rows, cur = "", None
for n, s in ordered:
    g = (s["stage"], s["cat"])
    if g != cur:
        rows += f'<tr class="grp"><td colspan="7">{e(g[0])} · {e(g[1])}</td></tr>'
        cur = g
    hi = ' class="hi"' if s["spread"] is not None and s["spread"] > 0.3 else ""
    rng = '<span class="no">1 цена</span>' if s["n"] == 1 else f'<span{hi}>{f(s["mn"][0])} – {f(s["mx"])}</span><span class="sm">{s["n"]} цен</span>'
    dm = s["dmn"]
    dcell = f'<b>{f(dm[0])}</b><span class="sm">{e(dm[1])}</span>' if dm else '<span class="no">—</span>'
    rows += (f'<tr><td class="pos">{e(n)} <span class="unit">{e(s["unit"])}</span></td>'
             f'<td><span class="mid">{f(s["mn"][0])}</span>{who(s["mn"][1])}</td>'
             f'<td class="n">{f(s["avg"])}</td><td class="n">{rng}</td><td class="n dv">{dcell}</td>'
             f'<td class="n">{gap_html(s)}</td><td class="n">{our_html(s)}</td></tr>')

nprice = sum(s["n"] for s in stats.values())
cols = lambda ws: "<colgroup>" + "".join(f'<col style="width:{w}%">' for w in ws) + "</colgroup>"
doc = f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><style>
@page {{ size: A4 landscape; margin: 9mm 11mm; }}
table.key td {{ padding:2px 4px; }} table.key .big {{ font-size:9.6pt; }}
body {{ font-family: 'DejaVu Sans', Arial, sans-serif; color:#1a1a1a; font-size:8.6pt; }}
h1 {{ font-size:15pt; margin:0; color:#1F3864; }} .sub {{ color:#666; margin:2px 0 8px; font-size:8pt; }}
h2 {{ font-size:9.6pt; color:#1F3864; margin:8px 0 3px; }}
.wrap {{ display:grid; grid-template-columns: 58% 40%; gap:2%; }}
table {{ width:100%; border-collapse:collapse; table-layout:fixed; font-size:8.2pt; }}
th {{ background:#1F3864; color:#fff; text-align:left; padding:4px; font-size:7.4pt; vertical-align:bottom; }} th.r {{ text-align:right; }} th.dh {{ background:#2e6b34; }}
td {{ border-bottom:1px solid #e6e6e6; padding:4px; vertical-align:middle; overflow-wrap:anywhere; }}
tbody tr:nth-child(even) td {{ background-color:#fafbfc; }}
.n {{ text-align:right; }} .pos {{ font-weight:bold; }} .unit {{ font-weight:normal; color:#999; font-size:7pt; }}
.big {{ display:block; font-size:11pt; font-weight:bold; color:#1F3864; }} .mid {{ display:block; font-weight:bold; color:#1F3864; }}
.who {{ color:#555; font-size:6.8pt; }} .sm {{ display:block; color:#888; font-size:6.6pt; font-weight:normal; line-height:1.2; }}
.tag {{ font-size:6.1pt; padding:0 4px; border-radius:6px; white-space:nowrap; }} .tz {{ background:#d8f0dc; color:#1e6b2e; }} .tsk {{ background:#dceaf8; color:#1d4f8a; }}
.tm {{ background:#fbe8d3; color:#8a4b0f; }} .tt {{ background:#f8d7da; color:#8a1c25; }} .tn {{ background:#eee; color:#777; }}
tr.grp td {{ background:#1F3864 !important; color:#fff; font-weight:bold; font-size:7.8pt; padding:3px 6px; }}
td.dv {{ background-color:#f3f9f1 !important; }}
.hi {{ color:#b00020; font-weight:bold; }} .no {{ color:#bbb; }} .up {{ color:#b00020; font-weight:bold; }} .down {{ color:#1e7b34; font-weight:bold; }} .best {{ color:#1e7b34; font-weight:bold; }}
ul {{ margin:2px 0 0 14px; padding:0; }} li {{ margin-bottom:2px; font-size:8pt; }}
.note {{ color:#777; font-size:7pt; margin-top:6px; }} tr {{ page-break-inside:avoid; }} .pb {{ page-break-before:always; }}
</style></head><body>
<h1>Сводка цен — ЖК Golden Hills · {D:%d.%m.%Y}</h1>
<div class="sub">Весь рынок Ташкента · {nprice} цен по {len(stats)} позициям · последняя цена каждого продавца за {WINDOW} дней · сум, с НДС (если не указано иное)</div>
<div class="wrap"><div>
<h2 style="margin-top:4px">Главное</h2>
<table class="key">{cols([27, 31, 19, 16, 7])}<thead><tr><th>Позиция</th><th>Лучшая цена · у кого</th><th class="r">Средняя</th><th class="r">Наша КП</th><th class="r">Изм.</th></tr></thead>
<tbody>{key_rows}</tbody></table>
</div><div>
<h2>Что важно сегодня</h2><ul>{"".join(f"<li>{x}</li>" for x in notes)}</ul>
<h2>Где наша КП дороже рынка</h2>
<table>{cols([34, 24, 28, 14])}<thead><tr><th>Позиция</th><th class="r">Наша КП</th><th class="r">Мин. у проверенных</th><th class="r">Перепл.</th></tr></thead>
<tbody>{save_rows}</tbody></table>
</div></div>
<div class="pb"></div>
<h2>Все позиции</h2>
<table>{cols([24, 20, 9, 13, 13, 8, 13])}<thead><tr><th>Позиция <span style="font-weight:normal;opacity:.7">ед.</span></th><th>Лучшая цена · у кого</th><th class="r">Средняя</th><th class="r">Диапазон</th><th class="r dh">Мин. у заводов и складов</th><th class="r">Посредники дороже на</th><th class="r">Наша КП</th></tr></thead>
<tbody>{rows}</tbody></table>
<p class="note"><b>Как читать:</b> метка у продавца — завод / склад / магазин / трейдер / не пров. «Посредники дороже на» — средняя у магазинов и трейдеров к средней у заводов и складов. «Наша КП» — лучшая цена ваших поставщиков: «лучшая» или +% к рыночному минимуму. «Изм.» — изменение у тех же продавцов к их прошлой цене. Красный диапазон — разброс больше 30% (есть смысл торговаться). Цены из объявлений — ориентир; для закупки нужна письменная КП.</p>
</body></html>"""
tmp = os.path.splitext(a.pdf)[0] + ".html"
open(tmp, "w", encoding="utf-8").write(doc)
here = os.path.dirname(os.path.abspath(__file__))
subprocess.run(["node", os.path.join(here, "render_pdf.js"), a.pdf, tmp], check=True)
os.remove(tmp)
print("PDF:", a.pdf)
