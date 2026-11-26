"""Резервная копия базы приложения (задачи + оплаты) в репозиторий.

    python tools/backup_app_db.py <out_dir из ArtifactData list>     # out_dir содержит tasks/ и payments/

Пишет данные/резервная_копия_приложения.json: {"savedAt", "tasks": [...], "payments": [...]}, у каждого документа поле id.
Восстановление — см. восстановление.md (ArtifactData batch set по каждому документу).
"""
import glob, json, os, sys
from datetime import datetime, timezone, timedelta
src = sys.argv[1]
out = {"savedAt": datetime.now(timezone(timedelta(hours=5))).isoformat(timespec="minutes")}
for col in ("tasks", "payments"):
    docs = []
    for f in sorted(glob.glob(os.path.join(src, col, "*.json"))):
        d = json.load(open(f, encoding="utf-8")); d = d.get("data", d)
        d["id"] = os.path.splitext(os.path.basename(f))[0]; docs.append(d)
    out[col] = docs
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "данные", "резервная_копия_приложения.json")
json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("копия:", len(out["tasks"]), "задач,", len(out["payments"]), "документов оплат,", out["savedAt"])
