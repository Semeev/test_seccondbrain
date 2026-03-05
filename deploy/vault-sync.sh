#!/bin/bash
REPO="/home/dbrain/agent-second-brain"
LOG="/home/dbrain/vault-sync.log"
chown -R dbrain:dbrain "$REPO/.git/objects" 2>/dev/null
cd "$REPO" || exit 1
if sudo -u dbrain git status --porcelain vault/ | grep -q .; then
    sudo -u dbrain git add vault/
    sudo -u dbrain git commit -m "auto-sync: vault $(date '+%Y-%m-%d %H:%M')"
    sudo -u dbrain git push origin main >> "$LOG" 2>&1
    echo "$(date): pushed vault changes" >> "$LOG"
fi
