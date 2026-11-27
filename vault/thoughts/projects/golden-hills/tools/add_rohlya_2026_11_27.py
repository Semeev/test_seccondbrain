"""Рохля 3 т — на заметку от пользователя 27.11.2026 (новая категория «Инструмент и оборудование»)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from openpyxl import load_workbook
from wbtools import ensure_v2, ensure_v3, add_positions
X = sys.argv[1]
wb = load_workbook(X); ensure_v2(wb); ensure_v3(wb)
print("добавлено позиций:", add_positions(wb, [("Инструмент и оборудование", "Рохля гидравлическая 3 т", "шт",
      "Ручная гидравлическая тележка, грузоподъёмность 3 т", "9. Метизы и расходники", "По потребности")]))
wb.save(X)
