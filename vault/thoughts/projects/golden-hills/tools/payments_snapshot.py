"""Снимок вкладки «Оплаты» для просмотра без входа (решение пользователя 26.11.2026: у начальника участка нет аккаунта Claude).

    python tools/payments_snapshot.py <папка с JSON из ArtifactData list out_dir>/payments  [время снимка ISO]

Пишет данные/оплаты_снимок.json; build_app.sh кладёт его рядом с приложением как payments.json.
Приложение берёт живую базу, если зритель вошёл в Claude, иначе — этот снимок (только чтение).
"""
import glob, json, os, sys
from datetime import datetime, timezone, timedelta
src = sys.argv[1]
at = sys.argv[2] if len(sys.argv) > 2 else datetime.now(timezone(timedelta(hours=5))).isoformat(timespec="minutes")
docs = []
for f in sorted(glob.glob(os.path.join(src, "*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    d = d.get("data", d)
    d["id"] = os.path.splitext(os.path.basename(f))[0]
    docs.append(d)
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "данные", "оплаты_снимок.json")
json.dump({"snapshotAt": at, "payments": docs}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("снимок:", len(docs), "документов,", at)
