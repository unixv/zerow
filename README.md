# ZeroW — Multiplayer Lobby

A small Atrium-style multiplayer room for Raspberry Pi Zero W, powered by Flask and SQLite.

## First iteration
- Join the **Lobby** with a unique nickname (2–18 letters, numbers, spaces, underscores, hyphens)
- Click a tile to move your avatar anywhere in the 16×11 room
- See other active players and their positions (refreshed every 1.5 seconds)
- Send messages to everyone in the Lobby; chat appears as speech bubbles above avatars
- Retain the latest 500 messages in SQLite, with the latest 60 shown in the UI
- Server-side validation, simple per-player chat cooldown, and HTTP-only session cookies

There are no passwords or account recovery in this prototype; names are claimed by the browser's cookie. Do not use this as an authenticated or moderated public chat until those features exist.

## Already configured Pi — automatic deployment

The Pi's `zerow-update.timer` checks `main` approximately once per minute and deploys new commits automatically.

```bash
systemctl list-timers zerow-update.timer
sudo journalctl -u zerow-update.service -n 40 --no-pager
sudo journalctl -u zerow.service -n 40 --no-pager
```

Open `http://<PI_IP>:8000` from the local network or use your existing reverse proxy/tunnel. Database is stored at `/opt/zerow/data/atrium.sqlite3` and is not committed to Git. Existing data survives updates.

## Fresh Raspberry Pi setup

```bash
sudo apt-get update
sudo apt-get install -y git
git clone https://github.com/unixv/zerow.git
cd zerow
sudo bash deploy/install.sh
```

The installer sets up a dedicated `zerow` user, `/opt/zerow`, a Python virtual environment, a systemd web service, and an update timer. This needs to be done only once, unless the service/timer configurations are changed.

## Development on another machine

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
ZEROW_DB=./data/atrium.sqlite3 .venv/bin/python app.py
```

Visit `http://localhost:8000`. Visit `/health` for a database-aware health check.

## Future iterations

Rooms and furniture, avatar customization, account recovery, server-side moderation and rate limits, and real-time WebSockets can be added separately once the first shared room is verified on the Pi.
