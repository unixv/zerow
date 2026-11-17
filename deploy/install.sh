#!/usr/bin/env bash
# One-time install on Raspberry Pi OS (run with sudo).
set -euo pipefail
if [[ "$(id -u)" -ne 0 ]]; then echo "Run with sudo: sudo bash deploy/install.sh" >&2; exit 1; fi
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y git python3 python3-venv curl util-linux

if ! id zerow >/dev/null 2>&1; then
  useradd --system --user-group --home-dir /opt/zerow --shell /usr/sbin/nologin zerow
fi
if [[ ! -d /opt/zerow/.git ]]; then
  if [[ -e /opt/zerow ]]; then echo "/opt/zerow exists but is not a git checkout; move it first" >&2; exit 1; fi
  git clone https://github.com/unixv/zerow.git /opt/zerow
fi
chown -R zerow:zerow /opt/zerow

# First install from the current checkout. Future merges deploy via the timer.
if [[ ! -d /opt/zerow/.venv ]]; then
  runuser -u zerow -- python3 -m venv /opt/zerow/.venv
fi
runuser -u zerow -- /opt/zerow/.venv/bin/python -m pip install -r /opt/zerow/requirements.txt

cp /opt/zerow/deploy/zerow.service /etc/systemd/system/
cp /opt/zerow/deploy/zerow-update.service /etc/systemd/system/
cp /opt/zerow/deploy/zerow-update.timer /etc/systemd/system/\ncp /opt/zerow/deploy/zerow-backup.service /etc/systemd/system/\ncp /opt/zerow/deploy/zerow-backup.timer /etc/systemd/system/

systemctl daemon-reload
systemctl enable --now zerow.service
systemctl enable --now zerow-update.timer\nsystemctl enable --now zerow-backup.timer

echo "Zero W: http://<PI_IP>:8000"
echo "Automatic updates: systemctl list-timers zerow-update.timer"\necho "Daily backups: systemctl list-timers zerow-backup.timer"
