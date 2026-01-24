#!/usr/bin/env bash
set -euo pipefail

echo "[start] backup worker starting: $(date -u)"

# Ensure backup dir exists and is writable
if ! mkdir -p /data/backups 2>/dev/null; then
  echo "[error] Cannot create /data/backups. Check volume mount and permissions." >&2
  exit 1
fi

# If running as root, try to set reasonable owner (no-op if not permitted)
if [ "$(id -u)" = "0" ]; then
  chown -R 1000:1000 /data || true
fi

# Find Python 3
PY=""
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "[error] No python interpreter found (need Python 3)" >&2
  exit 127
fi

# Verify Python 3
if ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info[0] >= 3 else 1)'; then
  echo "[error] Selected interpreter ($PY) is not Python 3" >&2
  exit 127
fi

# Warn if BACKUP_PASSWORD missing (won't abort so startup still works)
if [ -z "${BACKUP_PASSWORD:-}" ]; then
  echo "[warn] BACKUP_PASSWORD not set. Backups will fail until set."
fi

# Run one initial backup
echo "[run] Initial backup attempt: $(date -u)"
"$PY" scripts/remote_backup.py || echo "[warn] initial backup failed"

# Periodic loop (set BACKUP_INTERVAL_SECONDS to change frequency)
BACKUP_INTERVAL=${BACKUP_INTERVAL_SECONDS:-86400}
echo "[info] Entering periodic loop (every $BACKUP_INTERVAL seconds)."

while true; do
  sleep "$BACKUP_INTERVAL"
  echo "[run] Scheduled backup: $(date -u)"
  "$PY" scripts/remote_backup.py || echo "[warn] scheduled backup failed"
done