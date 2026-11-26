"""Сохраняет все присланные пользователем файлы для приложения «300 снабженцев» в проект (правило пользователя 26.11.2026).

    python tools/save_uploads.py <папка загрузок сессии> [--name "<sha256-префикс>=<имя>" ...]

- Файл, чьё содержимое (sha256) уже лежит где-либо в проекте, не копируется — только отмечается в журнале.
- Новый файл копируется в исходники/входящие/ДАТА_<имя> (имя — из --name, иначе из имени загрузки).
- Журнал всех входящих: данные/входящие_файлы.json (sha256, имя загрузки, где лежит в проекте, дата).
"""
import hashlib, json, os, re, shutil, sys
from datetime import date
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = sys.argv[1]
names = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a and not a.startswith("--"))
names.update(dict(a.split("=", 1) for a in [x for i, x in enumerate(sys.argv) if i and sys.argv[i - 1] == "--name"]))
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
have = {}
for d, _, fs in os.walk(ROOT):
    if "/.git" in d: continue
    for f in fs:
        p = os.path.join(d, f)
        try: have.setdefault(sha(p), os.path.relpath(p, ROOT))
        except OSError: pass
logp = os.path.join(ROOT, "данные", "входящие_файлы.json")
log = json.load(open(logp, encoding="utf-8")) if os.path.exists(logp) else {"comment": "Журнал всех файлов, присланных для приложения «300 снабженцев» (Снабжение Golden Hills).", "files": []}
logged = {x["sha256"] for x in log["files"]}
new = 0
for f in sorted(os.listdir(src)):
    p = os.path.join(src, f)
    if not os.path.isfile(p) or not re.match(r'^[0-9a-f]{8}-', f): continue  # only user uploads (<uuid>-<name>), not service files like uploads.jsonl
    h = sha(p)
    if h in logged: continue
    if h in have:
        where = have[h]
    else:
        nm = next((v for k, v in names.items() if h.startswith(k)), f.split("-", 1)[-1])
        os.makedirs(os.path.join(ROOT, "исходники", "входящие"), exist_ok=True)
        where = os.path.join("исходники", "входящие", f"{date.today():%Y-%m-%d}_{nm}")
        shutil.copy(p, os.path.join(ROOT, where)); have[h] = where; new += 1
    log["files"].append({"sha256": h, "upload": f, "saved": where, "date": f"{date.today():%Y-%m-%d}"})
    logged.add(h)
json.dump(log, open(logp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"новых файлов скопировано: {new}; всего в журнале: {len(log['files'])}")
