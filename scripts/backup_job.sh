#!/usr/bin/env bash
set -euo pipefail

# Wrapper to run the remote backup job inside the service container
# Usage: railway run --service web bash -lc 'bash scripts/backup_job.sh'

# Ensure backup dir exists
mkdir -p /data/backups

# Run the python job (it will use BACKUP_URL and BACKUP_PASSWORD env vars)
PY=""
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "No python executable found (need python3 or python)" >&2
  exit 127
fi

# Ensure interpreter is Python 3
if ! "$PY" -c 'import sys\nsys.exit(0 if sys.version_info[0] >= 3 else 1)'; then
  echo "Selected Python interpreter ($PY) is not Python 3" >&2
  exit 127
fi

"$PY" scripts/remote_backup.py

# Show latest backups
ls -la /data/backups | tail -n 10
