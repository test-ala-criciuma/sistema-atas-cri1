#!/usr/bin/env python3
"""Remote backup job.
Sends a POST to BACKUP_URL with BACKUP_PASSWORD and saves the DB into /data/backups.
"""
import os
import sys
from datetime import datetime

BACKUP_PASSWORD = os.environ.get('BACKUP_PASSWORD')
BACKUP_URL = os.environ.get('BACKUP_URL', 'https://to-gather.up.railway.app/configuracoes/backup')
BACKUP_DIR = os.environ.get('BACKUP_DIR', '/data/backups')
RETENTION = int(os.environ.get('BACKUP_RETENTION', '7'))  # number of backups to keep

os.makedirs(BACKUP_DIR, exist_ok=True)
# Use a temporary file inside the backup directory to ensure renames are on the same filesystem
TMP_PATH = os.path.join(BACKUP_DIR, '.backup.tmp')

if not BACKUP_PASSWORD:
    print('ERROR: BACKUP_PASSWORD environment variable not set', file=sys.stderr)
    sys.exit(2)


# Try to use requests if available for simplicity
try:
    import requests
    use_requests = True
except Exception:
    use_requests = False


def download_with_requests():
    print('Using requests to download backup...')
    try:
        r = requests.post(BACKUP_URL, files={'password': (None, BACKUP_PASSWORD)}, stream=True, timeout=60)
        if r.status_code != 200:
            print(f'Bad response: {r.status_code} {r.text[:200]}', file=sys.stderr)
            return False
        with open(TMP_PATH, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print('Error downloading (requests):', e, file=sys.stderr)
        return False


def download_with_urllib():
    print('Using urllib to download backup...')
    import uuid
    import http.client
    from urllib.parse import urlparse

    boundary = '--------------' + uuid.uuid4().hex
    data = []
    data.append(f'--{boundary}')
    data.append('Content-Disposition: form-data; name="password"')
    data.append('')
    data.append(BACKUP_PASSWORD)
    data.append(f'--{boundary}--')
    body = '\r\n'.join(data).encode('utf-8')

    url = urlparse(BACKUP_URL)
    conn = None
    try:
        if url.scheme == 'https':
            conn = http.client.HTTPSConnection(url.netloc, timeout=60)
        else:
            conn = http.client.HTTPConnection(url.netloc, timeout=60)
        path = url.path or '/'
        if url.query:
            path += '?' + url.query
        headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Content-Length': str(len(body))
        }
        conn.request('POST', path, body, headers)
        res = conn.getresponse()
        if res.status != 200:
            print(f'Bad response: {res.status} {res.reason}', file=sys.stderr)
            return False
        with open(TMP_PATH, 'wb') as f:
            while True:
                chunk = res.read(8192)
                if not chunk:
                    break
                f.write(chunk)
        return True
    except Exception as e:
        print('Error downloading (urllib):', e, file=sys.stderr)
        return False
    finally:
        if conn:
            conn.close()


def validate_sqlite(path):
    try:
        with open(path, 'rb') as f:
            sig = f.read(16)
        return sig.startswith(b'SQLite format 3\x00')
    except Exception as e:
        print('Error reading file for validation:', e, file=sys.stderr)
        return False


def rotate_backups():
    files = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith('atas_backup_')])
    if len(files) <= RETENTION:
        return
    to_remove = files[:-RETENTION]
    for f in to_remove:
        path = os.path.join(BACKUP_DIR, f)
        try:
            os.remove(path)
            print('Removed old backup:', path)
        except Exception as e:
            print('Failed to remove old backup', path, e, file=sys.stderr)


def main():
    ok = download_with_requests() if use_requests else download_with_urllib()
    if not ok:
        print('Download failed', file=sys.stderr)
        sys.exit(3)

    if not validate_sqlite(TMP_PATH):
        print(f'Downloaded file is NOT a valid SQLite DB. Inspect {TMP_PATH} and aborting.', file=sys.stderr)
        try:
            os.remove(TMP_PATH)
        except Exception:
            pass
        sys.exit(4)

    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    dest = os.path.join(BACKUP_DIR, f'atas_backup_{ts}.db')
    try:
        os.replace(TMP_PATH, dest)
    except OSError:
        import shutil
        shutil.move(TMP_PATH, dest)
    print('Backup saved to', dest)

    rotate_backups()

if __name__ == '__main__':
    main()
