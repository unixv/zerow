#!/bin/bash
# Invoked by zerow-deploy.service as root once per minute.
set -euo pipefail
APP=/home/pi/zerow
STATE=/var/lib/zerow-deploy
mkdir -p "$STATE"
exec 9>"$STATE/lock"
flock -n 9 || exit 0
runuser -u pi -- git -C "$APP" fetch --quiet origin main
latest=$(runuser -u pi -- git -C "$APP" rev-parse origin/main)
previous=$(runuser -u pi -- git -C "$APP" rev-parse HEAD)
deployed=$(cat "$STATE/deployed" 2>/dev/null || true)
if [[ "$latest" == "$deployed" ]] && systemctl is-active --quiet zerow-game.service; then exit 0; fi
echo "Deploying Zero W game: $latest"
runuser -u pi -- git -C "$APP" reset --hard "$latest"
if systemctl restart zerow-game.service && systemctl is-active --quiet zerow-game.service; then
  sleep 2
  if curl --fail --silent --output /dev/null http://127.0.0.1:8080/; then
    echo "$latest" > "$STATE/deployed"
    echo "Deployment succeeded: $latest"
    exit 0
  fi
fi
echo "Deployment failed; rolling back to $previous" >&2
runuser -u pi -- git -C "$APP" reset --hard "$previous"
systemctl restart zerow-game.service || true
exit 1
