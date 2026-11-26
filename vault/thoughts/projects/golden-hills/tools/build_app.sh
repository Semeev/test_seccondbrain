#!/usr/bin/env bash
# Builds the app bundle (app/index.html + data.json + PDF digests) into an output folder for publishing.
# Usage: bash tools/build_app.sh <out_dir>     (run from the golden-hills folder)
set -euo pipefail
OUT=${1:?out dir}
mkdir -p "$OUT/svodki"
cp app/index.html "$OUT/index.html"
python3 tools/export_app.py Мониторинг_цен_Ташкент.xlsx "$OUT/data.json"
for f in сводки/Сводка_цен_*.pdf; do
  d=$(basename "$f" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')
  cp "$f" "$OUT/svodki/$d.pdf"
done
# contract/invoice files for the «Оплаты» tab (данные/документы_оплат.json: payment id → source file)
mkdir -p "$OUT/docs"
python3 - "$OUT" <<'PY'
import json, shutil, sys
m = json.load(open("данные/документы_оплат.json", encoding="utf-8"))["files"]
for k, src in m.items():
    shutil.copy(src, f"{sys.argv[1]}/docs/{k}.pdf")
print("docs:", len(m))
PY
ls "$OUT/svodki"
