# 🐍 Python Cloud Game

A beginner-friendly Python Snake game with a Flask web server and a live leaderboard. Built for a classroom Python-to-the-cloud demonstration.

**Start locally first!** Cloud deployment instructions (including AWS EC2) will be added in a future update.

## What you'll build

- **`game.py`** — Play Snake on your computer using Pygame.
- **`server.py`** — Run a Flask web server that accepts scores and displays a leaderboard.
- **SQLite** — Stores each player's highest score locally in `leaderboard.db`.

## Prerequisites

- Python 3.10 or newer (with `pip`)
- Git
- A terminal (macOS Terminal or Windows PowerShell)
- A desktop environment capable of opening a Pygame window

## 1. Download the project

Open a terminal and run:

```bash
git clone https://github.com/pyjoepy06/python-cloud-game.git
cd python-cloud-game
```

Alternatively, use GitHub's **Code → Download ZIP** and extract it.

## 2. Create a virtual environment

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can run the virtual environment's Python directly, for example `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.

## 3. Install dependencies

With the virtual environment active:

```bash
python -m pip install -r requirements.txt
```

This installs Flask, Pygame Community Edition, Requests, and Gunicorn. **Windows users should use the Flask development server below**, since Gunicorn is not supported natively on Windows.

## 4. Start the leaderboard server

Choose a demo API key. **Use the same key for the server and game.** This example is for local learning only; don't commit real credentials.

**macOS / Linux**

```bash
export GAME_API_KEY="local-demo-key"
python server.py
```

**Windows (PowerShell)**

```powershell
$env:GAME_API_KEY = "local-demo-key"
python server.py
```

Keep this terminal open. The server runs at **http://127.0.0.1:5000**.

Open these pages in a browser:

- **http://127.0.0.1:5000/** — Live leaderboard dashboard
- **http://127.0.0.1:5000/health** — Server health information (JSON)
- **http://127.0.0.1:5000/leaderboard** — Player scores (JSON)

The leaderboard may initially be empty. That's normal!

## 5. Play Snake

Open a **second terminal** in the same project folder and activate the virtual environment again (step 2). Set the same API key.

**macOS / Linux**

```bash
export GAME_API_KEY="local-demo-key"
python game.py
```

**Windows (PowerShell)**

```powershell
$env:GAME_API_KEY = "local-demo-key"
python game.py
```

Use the **arrow keys** to move. Eat the red food to gain points, and avoid hitting the walls or your own snake. When the game ends, it sends your score to the local server. Refresh the leaderboard page to see your score (the dashboard also refreshes automatically).

**Change your player name:** Open `game.py` and change `PLAYER = "Chantal"` to your own name before starting the game.

## 6. Optional: Run with Gunicorn (macOS / Linux)

After setting `GAME_API_KEY`, you can run the Flask application using Gunicorn instead of `python server.py`:

```bash
gunicorn --workers 1 --bind 127.0.0.1:5000 server:app
```

Use **one worker** for this classroom demo. Keep the server bound to `127.0.0.1` for local-only use. Stop either server with **Ctrl+C**.

## How it works

```text
Your computer
 ├── game.py (Pygame Snake)
 │      |
 │      | POST /score with X-API-Key
 │      v
 ├── server.py (Flask API)
 │      |
 │      v
 ├── leaderboard.db (SQLite)
 │
 └── Web browser
        |
        | GET / and /leaderboard
        v
     Flask leaderboard
```

The game sends a score only when the game ends. The server stores each player's **highest** score.

## Troubleshooting

| Problem | What to try |
| --- | --- |
| `python` not found | Install Python and check your PATH; on macOS try `python3`, on Windows try `py`. |
| `ModuleNotFoundError` | Activate your virtual environment and rerun `python -m pip install -r requirements.txt`. |
| Port 5000 already in use | Stop the other server using port 5000 (often with Ctrl+C). |
| Score submission returns 401 | Make sure `GAME_API_KEY` is set to the **same value in both terminals**, then restart the processes. |
| Score cannot reach the server | Start `server.py` first; confirm `http://127.0.0.1:5000/health` works. |
| Scores don't appear | Finish a game, check the second terminal for errors, then refresh the leaderboard. |

### Reset scores for a fresh classroom game

Stop the server, then delete the local `leaderboard.db` file in the project folder. Restart the server; it will create a fresh empty database. **This permanently removes local scores.**

## ☁️ Coming Soon: Run in the Cloud

Future instructions will cover:

- Launching an AWS EC2 instance
- Installing Python and the project on the instance
- Running the Flask leaderboard with Gunicorn
- Connecting a local Snake game to the cloud-hosted server
- Configuring networking and security safely

**For now, run everything on your own computer.** Never expose the classroom demo server or its demo API key to the public internet without additional security controls.

---

Created as a hands-on introduction to **Python, APIs, web servers, and cloud computing**.
