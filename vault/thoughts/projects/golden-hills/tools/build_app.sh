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
ls "$OUT/svodki"
