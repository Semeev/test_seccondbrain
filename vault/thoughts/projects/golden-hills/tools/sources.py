"""Реестр источников цен (данные/источники.json): поиск новых и вывод списка.

    python tools/sources.py check Мониторинг_цен_Ташкент.xlsx [данные/найдено_ДАТА.txt ...]
        Собирает домены из «Журнала цен» (ссылки), «Поставщиков» (сайт) и файлов со ссылками
        из сегодняшнего поиска; печатает те, которых нет в реестре. Их нужно открыть, оценить
        и внести в реестр (в т.ч. со статусом «нет данных»/«блокирует»), а в выводы дня — строку
        «Новые источники: …». Код выхода 0 всегда; последняя строка — «новых: N».
    python tools/sources.py md
        Пишет источники.md (таблица для чтения в Obsidian).
"""
import json, os, re, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "данные", "источники.json")
# Не источники цен: соцсети, поисковики, служебное, чужие страны
IGNORE = re.compile(r"(google|yandex|bing|facebook|instagram|threads|youtube|wikipedia|t\.me|telegram|tgstat|"
                    r"\.ru$|\.kz$|\.kg$|\.ua$|\.md$|\.by$|cdn|fonts|jsdelivr|cloudflare|gstatic|doubleclick|uzum\.uz)")


def dom(url):
    m = re.search(r"https?://([^/\s\"'<>,;)]+)", url or "")
    return m.group(1).lower().removeprefix("www.") if m else None


def known():
    reg = json.load(open(REG, encoding="utf-8"))
    return reg, {s["domain"].split("/")[0].removeprefix("www.") for s in reg["sources"]}


def check(xlsx, extra):
    from openpyxl import load_workbook
    _, have = known()
    found = defaultdict(set)
    wb = load_workbook(xlsx, read_only=True)
    for r in wb["Журнал цен"].iter_rows(min_row=2, values_only=True):
        d = dom(str(r[14] or ""))
        if d: found[d].add(f"журнал: {r[4]}")
    for r in wb["Поставщики"].iter_rows(min_row=2, values_only=True):
        for d in filter(None, (dom(u) for u in re.findall(r"https?://\S+", str(r[5] or "")))):
            found[d].add(f"поставщик: {r[0]}")
    for f in extra:
        for line in open(f, encoding="utf-8"):
            d = dom(line)
            if d: found[d].add("поиск")
    new = {d: v for d, v in found.items() if d not in have and not IGNORE.search(d)}
    for d, why in sorted(new.items()):
        print(f"НОВЫЙ  {d:32} ← {', '.join(sorted(why))[:120]}")
    print(f"новых: {len(new)}")


def md():
    reg, _ = known()
    order = list(reg["types"])
    st_order = {"работает": 0, "только поиск": 1, "нет данных": 2, "блокирует": 3}
    out = ["# Источники цен — Golden Hills", "",
           "Реестр ведётся в `данные/источники.json`, этот файл пересоздаётся `python tools/sources.py md`.",
           "Новые источники ловит `python tools/sources.py check …` в каждом ежедневном прогоне.", ""]
    for t in order:
        ss = sorted([s for s in reg["sources"] if s["type"] == t], key=lambda s: (st_order.get(s["status"], 9), s["name"]))
        if not ss: continue
        out += [f"## {t.capitalize()} — {reg['types'][t]}", "",
                "| Источник | Сайт | Что берём | Частота | Статус | Как | Проверен |", "|---|---|---|---|---|---|---|"]
        for s in ss:
            out.append(f"| {s['name']} | {s['domain']} | {s['categories']} | {s['freq']} | {s['status']} | {s['how'].replace('|', '/')} | {s['checked']} |")
        out.append("")
    open(os.path.join(ROOT, "источники.md"), "w", encoding="utf-8").write("\n".join(out))
    print("источники.md:", len(reg["sources"]), "источников")


if __name__ == "__main__":
    if sys.argv[1] == "check":
        check(sys.argv[2], sys.argv[3:])
    else:
        md()
