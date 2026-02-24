#!/bin/bash
# Двусторонняя синхронизация vault с GitHub

REPO="/Users/zake/Documents/test_seccondbrain"
LOG="/Users/zake/Documents/test_seccondbrain/scripts/vault-sync.log"

cd "$REPO" || exit 1

# Если есть изменения в vault — коммитим и пушим ТОЛЬКО vault
if [ -n "$(git status --porcelain vault/)" ]; then
    echo "$(date): Vault changes detected, pushing..." >> "$LOG"
    git add vault/
    git commit -m "sync: obsidian vault changes $(date '+%Y-%m-%d %H:%M')" >> "$LOG" 2>&1
    git push origin main >> "$LOG" 2>&1
else
    echo "$(date): No vault changes" >> "$LOG"
fi

# Тянем с сервера
git pull -X theirs origin main >> "$LOG" 2>&1
echo "$(date): Sync complete" >> "$LOG"
