#!/usr/bin/env bash
set -euo pipefail

# Run inside the service container (railway ssh) or via
# railway run --service web bash -lc 'bash scripts/restore_from_latest.sh'

BACKUP_DIR="/data/backups"
DB_PATH="/data/atas.db"

if [ ! -d "$BACKUP_DIR" ]; then
  echo "No backups directory found at $BACKUP_DIR"
  exit 1
fi

LATEST_FILE=$(ls -1t "$BACKUP_DIR" | head -n1)
if [ -z "$LATEST_FILE" ]; then
  echo "No backups found in $BACKUP_DIR"
  exit 1
fi

LATEST="$BACKUP_DIR/$LATEST_FILE"

echo "Latest backup candidate: $LATEST"

# Quick validation: check SQLite signature
python3 - <<PY
b=open('$LATEST','rb').read(64)
print('len=', len(b))
print('is SQLite?:', b.startswith(b'SQLite format 3\x00'))
print('preview:', repr(b[:64]))
PY

read -p "Proceed to restore $LATEST into $DB_PATH? [y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "Aborted by user"
  exit 0
fi

# Backup current DB (if exists)
mkdir -p "$BACKUP_DIR"
if [ -f "$DB_PATH" ]; then
  cp "$DB_PATH" "$BACKUP_DIR/atas.db.corrupt.$(date +%Y%m%d_%H%M%S)" || true
  echo "Saved current DB as corrupt backup"
fi

# Copy the valid backup into place
cp "$LATEST" "$DB_PATH"
ls -l "$DB_PATH"

# Validate tables
python3 - <<PY
import sqlite3
try:
  c=sqlite3.connect('$DB_PATH')
  print([r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")])
  c.close()
except Exception as e:
  print('Error opening DB:', e)
  raise
PY

echo "Restore completed. Consider restarting the service (railway restart --service web)"