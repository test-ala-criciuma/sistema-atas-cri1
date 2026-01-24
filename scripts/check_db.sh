#!/usr/bin/env bash
set -euo pipefail

DB_PATH="${DB_PATH:-/data/atas.db}"

echo "Checking DB at: $DB_PATH"

if [ ! -f "$DB_PATH" ]; then
  echo "No DB found at $DB_PATH"
  exit 1
fi

echo "Size:"
ls -lh "$DB_PATH"

echo "Tables:"
sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"

echo "OK"