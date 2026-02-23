#!/bin/bash
# Deploy finance-bot to VPS
# Run: bash finance-bot/deploy.sh

set -e
VPS="root@YOUR_VPS_IP"
REMOTE_DIR="/home/dbrain/finance-bot"

echo "==> Copying files..."
ssh "$VPS" "mkdir -p $REMOTE_DIR/src $REMOTE_DIR/data"
rsync -av --exclude='.env' --exclude='__pycache__' --exclude='*.pyc' \
    finance-bot/ "$VPS:$REMOTE_DIR/"

echo "==> Installing dependencies..."
ssh "$VPS" "cd $REMOTE_DIR && sudo -u dbrain /home/dbrain/.local/bin/uv pip install -e . --python /usr/bin/python3"

echo "==> Restarting service..."
ssh "$VPS" "systemctl restart finance-bot"

echo "==> Done! Check: journalctl -u finance-bot -n 20"
