#!/usr/bin/env bash
set -euo pipefail

# Wrapper to run the remote backup job inside the service container
# Usage: railway run --service web bash -lc 'bash scripts/backup_job.sh'

# Ensure backup dir exists
mkdir -p /data/backups

# Run the python job (it will use BACKUP_URL and BACKUP_PASSWORD env vars)
python3 scripts/remote_backup.py

# Show latest backups
ls -la /data/backups | tail -n 10
