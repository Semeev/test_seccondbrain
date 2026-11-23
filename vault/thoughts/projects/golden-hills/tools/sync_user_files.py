"""Повторная загрузка файлов пользователя: берёт только новое и изменённое.

    python tools/sync_user_files.py <файл.xlsx> [<файл2.xlsx> ...] [--apply] [--date 2026-11-25]

Без --apply — только показывает, что изменилось и что не удалось сопоставить.
С --apply — дописывает цены в журнал (через add_prices), обновляет контакты поставщиков, сохраняет снимок
и копию файла в исходники/. Затем нужно пересчитать книгу (recalc.py).

Сопоставление названий — данные/сопоставление.json. Снимки прошлых версий — данные/снимок_*.json.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from parse_user_files import detect, parse_kp, parse_suppliers, norm  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("files", nargs="+")
ap.add_argument("--apply", action="store_true")
ap.add_argument("--date", default=date.today().isoformat())
a = ap.parse_args()

XLSX = os.path.join(ROOT, "Мониторинг_цен_Ташкент.xlsx")
MAP = os.path.join(ROOT, "данные", "сопоставление.json")
M = json.load(open(MAP, encoding="utf-8"))
JUNK = {"№", "наименование товара", "фио", "отправить"}


def low(s):
    return norm(s).lower().replace("ё", "е")


def sup_key(rec):
    if rec["supplier_raw"]:
        return rec["supplier_raw"]
    c = [x for x in rec["contacts"] if low(x) not in JUNK]
    return " ".join(c[:2])


def map_supplier(sheet, raw):
    for k in (f"{sheet}|{raw}", f"*|{raw}"):
        if k in M["suppliers"]:
            return M["suppliers"][k]
    return None


def match(table, sheet, item):
    best, blen = None, 0
    for k, v in table.items() if isinstance(table, dict) else ((x, True) for x in table):
        sh, txt = k.split("|", 1)
        if sh not in ("*", sheet):
            continue
        if low(txt) in low(item) and len(txt) > blen:
            best, blen = v, len(txt)
    return best


def map_item(sheet, item):
    if match(M.get("skip_items", []), sheet, item):
        return "skip"
    m = re.match(r"\s*А\s*(500\s*С|400|2400|240)\s*-?\s*(\d+)\s*мм", item, re.I)
    if m and "арматур" in sheet.lower():
        cls = m.group(1).upper().replace(" ", "")
        cls = {"500С": "А500С", "400": "А400", "2400": "А400", "240": "А240"}[cls.replace("C", "С")]
        com = "В КП «А2400» — опечатка, считается А400" if "2400" in m.group(1) else ("В КП «А1» — уточнить класс" if "А1" in item else "")
        return {"position": f"Арматура {cls} d{m.group(2)}", "comment": com}
    return match(M["items"], sheet, item)


def snap_path(kind):
    return os.path.join(ROOT, "данные", f"снимок_{kind}.json")


report = []
for path in a.files:
    kind = detect(path)
    if kind is None:
        report.append(f"⚠ {os.path.basename(path)}: не похож ни на файл КП, ни на файл поставщиков — пропущен")
        continue
    snap = json.load(open(snap_path(kind), encoding="utf-8")) if os.path.exists(snap_path(kind)) else {}
    new_snap = dict(snap)
    if kind == "kp":
        recs = parse_kp(path)
        prices, unmapped_s, unmapped_i, changed = [], set(), set(), []
        contacts = {}
        for r in recs:
            if r["block"] in M.get("skip_blocks", []):
                continue
            raw = sup_key(r)
            sup = map_supplier(r["sheet"], raw)
            it = map_item(r["sheet"], r["item"])
            if isinstance(it, dict) and sup in M.get("supplier_class_override", {}) and it["position"].startswith("Арматура А400"):
                it = dict(it, position=it["position"].replace("А400", "А500С"), comment="класс уточнён по официальной КП поставщика")
            key = f'{r["sheet"]}|{raw}|{r["item"]}'
            old = snap.get(key)
            new_snap[key] = r["price"]
            if old == r["price"]:
                continue
            if it == "skip":
                continue
            if sup is None:
                unmapped_s.add(f'{r["sheet"]} | {raw}')
                new_snap.pop(key, None)
                continue
            if it is None:
                unmapped_i.add(f'{r["sheet"]} | {r["item"]} | {sup} | {r["price"]:,.0f}')
                new_snap.pop(key, None)
                continue
            d = (r["sheet_date"].isoformat() if r["sheet_date"] else a.date)
            qty = r["qty"] if isinstance(r["qty"], (int, float)) else None
            com = "; ".join(x for x in [it.get("comment", ""), f"кол-во в запросе: {qty:g}" if qty else "",
                                        f"было {old:,.0f}".replace(",", " ") if old else ""] if x)
            prices.append(dict(date=d, position=it["position"], supplier=sup, price=r["price"], unit=r["unit"] or "",
                               coef=it.get("coef"), source="КП (письменное)", link=f'файл КП, лист «{r["sheet"]}»', comment=com))
            changed.append(f'{"изменилась" if old else "новая"}: {it["position"]} — {sup}: {r["price"]:,.0f}'.replace(",", " ")
                           + (f' (было {old:,.0f})'.replace(",", " ") if old else ""))
            contacts.setdefault(sup, set()).update(x for x in r["contacts"] if low(x) not in JUNK)
        report.append(f"📄 {os.path.basename(path)} — файл КП: строк с ценой {len(recs)}, новых/изменённых {len(prices)}")
        report += ["   " + c for c in changed]
        report += [f"   ❓ поставщик не сопоставлен: {x}" for x in sorted(unmapped_s)]
        report += [f"   ❓ позиция не сопоставлена: {x}" for x in sorted(unmapped_i)]
        if a.apply and prices:
            tmp = os.path.join(ROOT, "данные", f"кп_{a.date}.json")
            prev = json.load(open(tmp, encoding="utf-8")) if os.path.exists(tmp) else []
            json.dump(prev + prices, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            only_new = os.path.join(ROOT, "данные", f".tmp_{os.getpid()}.json")
            json.dump(prices, open(only_new, "w", encoding="utf-8"), ensure_ascii=False)
            subprocess.run([sys.executable, os.path.join(HERE, "add_prices.py"), XLSX, only_new], check=True)
            os.remove(only_new)
    else:
        from openpyxl import load_workbook
        from wbtools import upsert_supplier
        recs = parse_suppliers(path)
        wb = load_workbook(XLSX) if a.apply else None
        n = 0
        for r in recs:
            raw = r["name"] or r["contacts"]
            key = f'{r["sheet"]}|{raw}'
            val = [r["items"], r["contacts"], r["comment"], r["site"]]
            if snap.get(key) == val:
                continue
            new_snap[key] = val
            name = M["suppliers"].get(f"sup|{raw}") or (r["name"] or f'{r["sheet"]} — {r["contacts"]}')
            n += 1
            report.append(f'   {"изменён" if key in snap else "новый"}: {name} | {r["items"]} | {r["contacts"]} | {r["comment"]}')
            if wb is not None:
                upsert_supplier(wb, name, cats=r["items"] or r["sheet"], phone=r["contacts"], comment=r["comment"],
                                site=r["site"], works="Да", checked="Нет", type="Не проверено" if wb is not None else None)
        report.insert(len(report) - n, f"📄 {os.path.basename(path)} — файл поставщиков: записей {len(recs)}, новых/изменённых {n}")
        if wb is not None and n:
            wb.save(XLSX)
    if a.apply:
        json.dump(new_snap, open(snap_path(kind), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        dst = os.path.join(ROOT, "исходники", f'{"Запрошенные_цены" if kind == "kp" else "Поставщики_пользователя"}_{a.date}.xlsx')
        if os.path.abspath(path) != os.path.abspath(dst):
            shutil.copy(path, dst)

print("\n".join(report))
if not a.apply:
    print("\n(пробный прогон — ничего не записано; добавьте --apply)")
