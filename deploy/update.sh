#!/usr/bin/env bash
# Run by systemd as root. The repository is public; no inbound SSH or GitHub secrets needed.
set -euo pipefail
APP=/opt/zerow
USER_NAME=$(stat -c '%U' "$APP")
STATE_DIR=/var/lib/zerow-deploy
mkdir -p "$STATE_DIR"
exec 9>"$STATE_DIR/lock"
flock -n 9 || exit 0

# Git and pip always run as the unprivileged app owner.
as_user() { runuser -u "$USER_NAME" -- "$@"; }

as_user git -C "$APP" fetch --quiet origin main
latest=$(as_user git -C "$APP" rev-parse refs/remotes/origin/main)
previous=$(as_user git -C "$APP" rev-parse HEAD)

if [[ "$latest" == "$previous" ]] && systemctl is-active --quiet zerow.service; then
  exit 0
fi

echo "Deploying Zero W: $previous -> $latest"
as_user git -C "$APP" reset --hard "$latest"

if ! as_user "$APP/.venv/bin/python" -m pip install -q -r "$APP/requirements.txt"; then
  echo "Dependency installation failed; rolling back" >&2
  as_user git -C "$APP" reset --hard "$previous"
  as_user "$APP/.venv/bin/python" -m pip install -q -r "$APP/requirements.txt" || true
  exit 1
fi

systemctl restart zerow.service
healthy=false
for _ in 1 2 3 4 5; do
  if systemctl is-active --quiet zerow.service && curl --fail --silent --max-time 3 -o /dev/null http://127.0.0.1:8000/health; then
    healthy=true
    break
  fi
  sleep 2
done

if [[ "$healthy" == true ]]; then
  echo "Deployed $latest successfully"
  exit 0
fi

echo "Health check failed; rolling back to $previous" >&2
as_user git -C "$APP" reset --hard "$previous"
as_user "$APP/.venv/bin/python" -m pip install -q -r "$APP/requirements.txt" || true
systemctl restart zerow.service || true
exit 1
