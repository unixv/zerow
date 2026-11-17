# Zero W Game

A tiny Flask click-counter game for Raspberry Pi Zero W. The app serves on port 8000 and provides a health endpoint at `/health`.

## One-time setup (automatic deployment)

On your Pi, run:

```bash
sudo apt-get update
sudo apt-get install -y git
git clone https://github.com/unixv/zerow.git
cd zerow
sudo bash deploy/install.sh
```

The installer creates a dedicated unprivileged `zerow` user, installs the app into `/opt/zerow`, creates its Python virtual environment, and enables the web service and automatic deployment timer. It does not require any inbound SSH access from GitHub.

Open `http://<PI_IP>:8000` from your LAN. Check `http://<PI_IP>:8000/health` to verify the app.

## How deployment works

Every ~60 seconds, the Pi checks the public GitHub repository for changes to `main`. When new code is merged it fetches the commit, updates dependencies, restarts the app, and checks the health endpoint. If the health check or installation fails, it attempts to roll back to the previous commit. All of this happens outbound from the Pi; no GitHub Actions runners, tokens, or inbound ports are needed.

```bash
# Follow application logs
sudo journalctl -u zerow.service -f

# Inspect deployment attempts
sudo journalctl -u zerow-update.service -n 50 --no-pager

# See next scheduled deployment check
systemctl list-timers zerow-update.timer

# Force an update check
sudo systemctl start zerow-update.service
```

The install script assumes port 8000 is unused. Stop any manually launched copy of the game first. Run `sudo bash deploy/install.sh` again if the systemd unit files themselves change; ordinary application code changes deploy automatically.

## Local development

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```
