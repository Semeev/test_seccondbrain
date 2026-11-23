"""Проверенные прямые источники (заводы/склады) на 23.11.2026 + цены с их сайтов."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from openpyxl import load_workbook
from wbtools import ensure_v2, ensure_v3, upsert_supplier

XLSX, OUT = sys.argv[1], sys.argv[2]
Z, SK, PR = "Завод-производитель", "Склад/дистрибьютор", "Перекупщик"
V = [
 ("ARTON", dict(type=Z, cats="Газоблок автоклавный", site="https://arton.uz/price-list", phone="+998 71 200 200 6",
   addr="Ташкентская обл., Ахангаранский р-н, СЭЗ «Ангрен» (ООО EAST MINING INVEST)",
   basis="Сайт arton.uz: собственный завод (фотогалерея, SMART-завод), «поставка без посредников», официальный прайс завода")),
 ("BEAMING UNIVERSE", dict(type=PR, cats="Газоблок", basis="Продаёт газоблок ARTON по 850 000 при цене завода 780 000 — перепродавец")),
 ("Cubix Beton", dict(type=Z, cats="Бетон товарный", site="https://cubixbeton.uz/",
   basis="Сайт cubixbeton.uz: «являемся производителем», собственный завод, экскурсии на завод, прайс без НДС")),
 ("Завод Махсус Полимер", dict(type=Z, cats="Трубы ПЭ/ПНД, ПП, фитинги", site="https://pipe.uz/",
   phone="+998 97 729 70 07; +998 71 295 03 04; +998 71 295 20 36; +998 90 973 19 12", comment="info@pipe.uz",
   basis="Сайт pipe.uz: завод, экструзионные линии Battenfeld/Drossbach, ISO 9001 (SGS); полный прайс по ссылке на Яндекс.Диск")),
 ("Росметсервис (KZMC)", dict(type=SK, cats="Металлопрокат, арматура, трубы ПЭ, кабель", site="https://kzmc.uz/", phone="+998 71 205 59 51",
   basis="Сайт kzmc.uz: продажа «со склада», прайс-лист PDF (цены — на сайте по запросу)")),
 ("Metal City", dict(type=SK, site="https://metalcity.uz/", phone="+998 71 200 10 90",
   basis="Сайт metalcity.uz: 6 собственных складов, 10 000 т постоянного запаса, 18 лет; цены — по запросу (прайс через форму)")),
 ("BSgroup Gazobeton", dict(type=Z, cats="Газоблок автоклавный, клей", site="https://bsgazobeton.uz/",
   basis="Aircrete Europe: собственный завод автоклавного газобетона BS Gazobeton с марта 2023")),
 ("Biржа UZEX (средневзвеш.)".replace("Bi", "Би"), dict(basis="Биржевые торги заводов-производителей (цемент, металл)")),
 ("ПЕНОПЛЭКС (Ангрен / Ташкент)", dict(basis="Официальный производитель «Пеноплэкс»; прямое КП от завода")),
 ("Texnolit (литейное производство)", dict(basis="Литейное производство, адрес производства Сергели")),
 ("LITDORMASH", dict(basis="Адрес производства: Бектемирский р-н, промзона Куйлюк")),
 ("Max Valve (MAX VALVE TRADE BUSINES)", dict(basis="Указан адрес склада: Учтепа, Промзона-5")),
 ("Techno Cable Group", dict(type=Z, basis="Карточка stroyka.uz: кабельный завод в Зангиатинском р-не (проверить на месте)")),
 ("Turon Plast Montaj", dict(type=Z, basis="Карточка stroyka.uz/prom.uz: производит трубы ПЭ-80/ПЭ-100 по ГОСТ РУз (проверить)")),
 ("АО «Узметкомбинат» (Бекабад)", dict(basis="Металлургический завод, Бекабад")),
]
SRC = "Сайт завода/склада"
P = []
for t in (300, 200, 150, 100):
    P.append(dict(position=f"Газоблок автоклавный {t} мм", supplier="ARTON", price=780000, unit="м³", source=SRC,
                  link="https://arton.uz/price-list", comment="Официальный прайс завода, D500, 625×250; «цены актуальны с 15 мая 2025»"))
P.append(dict(position="Газоблок автоклавный D500 (толщина не указана)", supplier="ARTON", price=780000, unit="м³", source=SRC,
              link="https://arton.uz/price-list", comment="Официальный прайс завода; D400 — 830 000"))
for pos, pr, lab in [("Бетон М150 (B12,5)", 390000, "B10 М-150"), ("Бетон М200 (B15)", 410000, "B15 М-200"), ("Бетон М250 (B20)", 430000, "B20 М-250"),
                     ("Бетон М300 (B22,5)", 470000, "B22,5 М-300"), ("Бетон М350 (B25)", 490000, "B27,5 М-350"), ("Бетон М400 (B30)", 525000, "B30 М-400")]:
    P.append(dict(position=pos, supplier="Cubix Beton", price=pr, unit="м³", vat="Нет", source=SRC, link="https://cubixbeton.uz/",
                  comment=f"Прайс завода «{lab}», без НДС; дата прайса на сайте не указана — уточнить актуальность"))
for x in P:
    x["date"] = "2026-11-23"
wb = load_workbook(XLSX)
ensure_v2(wb); ensure_v3(wb)
for n, kw in V:
    upsert_supplier(wb, n, **kw)
wb.save(XLSX)
json.dump(P, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok", len(P))
