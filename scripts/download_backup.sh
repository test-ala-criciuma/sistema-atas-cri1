#!/usr/bin/env bash
set -euo pipefail

# Download backup from remote app to local file
# Usage: BACKUP_PASSWORD=... ./scripts/download_backup.sh /path/to/save.db

OUTFILE=${1:-./atas.db}
BACKUP_URL=${BACKUP_URL:-"https://to-gather.up.railway.app/configuracoes/backup"}

if [ -z "${BACKUP_PASSWORD:-}" ]; then
  echo "ERROR: BACKUP_PASSWORD environment variable is required to download backup without session."
  echo "Set BACKUP_PASSWORD and try again: export BACKUP_PASSWORD=\"your_pass\""
  exit 1
fi

echo "Downloading backup from $BACKUP_URL to $OUTFILE"

curl -L -X POST -F "password=$BACKUP_PASSWORD" "$BACKUP_URL" -o "$OUTFILE" -D /tmp/backup_headers.txt

echo "Headers saved to /tmp/backup_headers.txt"

# Basic quick validation
python3 - <<PY
b=open('$OUTFILE','rb').read(64)
print('len=', len(b))
print('is SQLite?:', b.startswith(b"SQLite format 3\x00"))
PY

if python3 - <<PY
b=open('$OUTFILE','rb').read(16)
print(b.startswith(b"SQLite format 3\x00"))
PY
then
  echo 'Backup appears to be a valid SQLite file.'
else
  echo 'WARNING: Download does not look like a SQLite DB. Inspect /tmp/backup_headers.txt and the file.'
fi
