# Zero W Game

Minimal Flask game starter for a Raspberry Pi Zero W. The homepage has a clickable counter so you can confirm the app is running from a browser.

## Run on Raspberry Pi

```bash
sudo apt update
sudo apt install -y git python3 python3-venv
git clone https://github.com/unixv/zerow.git
cd zerow
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

Visit `http://<PI_IP>:8000` from another device on your network. Check `http://<PI_IP>:8000/health` for JSON `{"status":"ok"}`.

## Run as a service

Create `/etc/systemd/system/zerow.service` (replace `pi` and paths with your Pi username):

```ini
[Unit]
Description=Zero W Flask Game
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/zerow
ExecStart=/home/pi/zerow/.venv/bin/python /home/pi/zerow/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now zerow
sudo systemctl status zerow
```

## Deploy updates manually (until your CI/CD is connected)

```bash
cd ~/zerow
git pull --ff-only origin main
.venv/bin/pip install -r requirements.txt
sudo systemctl restart zerow
```

No deployment workflow or credentials are committed to this repository. You can connect your own CI/CD pipeline later.
