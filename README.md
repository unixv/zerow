# ZeroW — Persistent multiplayer Lobby

A small Atrium-style multiplayer room for Raspberry Pi Zero W, built with Flask and SQLite. **No SQL server is required.**

## Accounts

- Permanent unique usernames (3–18 letters/numbers/underscore/hyphen)
- Passwords hashed using scrypt; plaintext passwords are never stored
- Password change from the Account menu, with current-password verification, session revocation, and failed-attempt throttling
- Login, logout and revocable 30-day sessions (random tokens stored as SHA-256 hashes)
- Persistent avatar positions, messages and account creation timestamps
- Six failed logins per username trigger a 15-minute lockout
- Origin validation for all state-changing API requests
- Legacy guest messages remain in the database, labeled `Guest · name`; the old guest cookie no longer authenticates

**Limitations:** There is no password reset or email verification yet. The login throttle is basic; it is not a substitute for Cloudflare WAF/rate limiting, moderation and abuse prevention. Use HTTPS for internet access. If terminating HTTPS at a local HTTP proxy/tunnel, set `Environment=ZEROW_SECURE_COOKIES=1` in `/etc/systemd/system/zerow.service`, run `sudo systemctl daemon-reload && sudo systemctl restart zerow.service`, then use only the HTTPS hostname. Don't enable Secure cookies when browsing via HTTP LAN address.

## Existing Raspberry Pi: automatic updates

`zerow-update.timer` checks GitHub `main` about once a minute, installs code changes, restarts the service and checks `/health`.

```bash
systemctl list-timers zerow-update.timer
sudo journalctl -u zerow-update.service -n 50 --no-pager
sudo journalctl -u zerow.service -n 50 --no-pager
```

User data lives in `/opt/zerow/data/atrium.sqlite3`, outside Git-tracked files; it survives deployments and device restarts. Avoid removing this directory. A failed deployment attempts a code rollback, **not** a database downgrade.

## Backups

Create a consistent SQLite backup (including data in SQLite WAL):

```bash
sudo -u zerow /opt/zerow/.venv/bin/python /opt/zerow/deploy/backup.py
```

The script makes an atomic, integrity-checked online snapshot (including WAL records), refuses to create an empty database when the source is missing, and retains the seven newest snapshots in `/opt/zerow/data/backups/`. Fresh installations enable `zerow-backup.timer` for daily backups. **Copy backups off the Pi**: an SD card failure could destroy the database and all local snapshots.\n\nFor an existing Pi installation, the updater deploys the script but does not install new systemd units. Run `sudo bash /opt/zerow/deploy/install.sh` once to enable the timer, then check `systemctl list-timers zerow-backup.timer` and `sudo journalctl -u zerow-backup.service -n 30 --no-pager`. Existing database data is not reset by the installer.

## Fresh Pi install

```bash
sudo apt-get update
sudo apt-get install -y git
git clone https://github.com/unixv/zerow.git
cd zerow
sudo bash deploy/install.sh
```

## Local development and tests

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
ZEROW_DB=./data/atrium.sqlite3 .venv/bin/python app.py
python3 -m unittest discover -s tests -v
```

Visit `http://localhost:8000` and `/health`.

## Next milestones

Email-based recovery, moderation and abuse controls, secure HTTPS-only production entry, off-device automated backups, and load/concurrency testing should precede opening registration to the wider internet.
