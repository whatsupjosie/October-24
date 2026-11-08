"""Start an authenticated, isolated PubCast instance in an owner-private Codespace.

No browser or optional Node service is installed. Runtime data stays outside git.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    data = Path.home() / '.local' / 'share' / 'pubcast-phone-test'
    data.mkdir(parents=True, exist_ok=True)
    pid_path = data / 'launcher.pid'
    log_path = data / 'server.log'
    if pid_path.exists():
        try:
            pid = int(pid_path.read_text().strip())
            os.kill(pid, 0)
            # Confirm this is our previous launcher before accepting it.
            cmdline = Path(f'/proc/{pid}/cmdline').read_bytes()
            if b'run_reach.py' in cmdline and str(data).encode() in cmdline:
                print(f'PubCast is already running. Logs: {log_path}')
                return 0
        except (ValueError, OSError):
            pass
    with socket.socket() as probe:
        try:
            probe.bind(('127.0.0.1', 8000))
        except OSError:
            print('Port 8000 is occupied by another process; PubCast was not started.', file=sys.stderr)
            return 1
    env = os.environ.copy()
    name = env.get('CODESPACE_NAME')
    domain = env.get('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN', 'app.github.dev')
    if name:
        env['PUBCAST_ALLOWED_ORIGINS'] = f'https://{name}-8000.{domain},http://127.0.0.1:8000'
    env['PUBCAST_ENFORCE_AUTH'] = '1'
    env['PYTHONUNBUFFERED'] = '1'
    with log_path.open('ab') as log:
        child = subprocess.Popen(
            [sys.executable, str(root / 'run_reach.py'), '--port', '8000',
             '--data-dir', str(data), '--no-browser', '--no-legacy-2i'],
            cwd=root, env=env, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
        )
    pid_path.write_text(str(child.pid))
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for _ in range(180):
        if child.poll() is not None:
            print(f'PubCast exited with {child.returncode}; see {log_path}', file=sys.stderr)
            return 1
        try:
            with opener.open('http://127.0.0.1:8000/health', timeout=1) as response:
                if response.status == 200:
                    with opener.open('http://127.0.0.1:8000/api/auth/status', timeout=2) as auth:
                        status = json.load(auth)
                    if status.get('auth_enforced') is not True:
                        child.terminate()
                        print('Authentication is not enforced; stopped the test host.', file=sys.stderr)
                        return 1
                    print('PubCast is healthy with authentication enabled.')
                    print('Open port 8000 from the Ports panel; keep its visibility Private.')
                    print('Open /login to create your test owner on first use.')
                    print(f'Logs and test data: {data}')
                    return 0
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            pass
        time.sleep(0.5)
    child.terminate()
    print(f'Startup timed out; see {log_path}', file=sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
