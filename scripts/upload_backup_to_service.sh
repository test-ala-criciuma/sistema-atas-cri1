#!/usr/bin/env bash
set -euo pipefail

# Upload a local backup file to the service /data/atas.db
# Usage: ./scripts/upload_backup_to_service.sh /path/to/your/backup.db

SRC=${1:-}
if [ -z "$SRC" ]; then
  echo "Usage: $0 /path/to/backup.db"
  exit 1
fi

if [ ! -f "$SRC" ]; then
  echo "File not found: $SRC"
  exit 1
fi

echo "Uploading $SRC to service /data/atas.db"
railway run --service web bash -lc 'mkdir -p /data/backups && cp /data/atas.db /data/backups/atas.db.corrupt.$(date +%Y%m%d_%H%M%S) || true; cat > /data/atas.db' < "$SRC"

echo "Upload complete. You may want to run: railway restart --service web"