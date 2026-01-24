#!/usr/bin/env bash
set -euo pipefail

DB_PATH="${DB_PATH:-/data/atas.db}"

echo "Resetting DB at: $DB_PATH"

# Backup current DB if exists
if [ -f "$DB_PATH" ]; then
  BACKUP_DIR="$(dirname "$DB_PATH")/backups"
  mkdir -p "$BACKUP_DIR"
  cp "$DB_PATH" "$BACKUP_DIR/atas.db.bak.$(date +%Y%m%d_%H%M%S)"
  echo "Backup created: $BACKUP_DIR"
  rm -f "$DB_PATH"
  echo "Old DB removed"
else
  echo "No existing DB found - creating new one"
fi

# Run the project's reset script (creates DB from schema)
python reset_db.py

echo "New DB created at:"
ls -lh "$DB_PATH" || true

sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;" || true

echo "Reset complete"