# ☁️ Deploy the Python Cloud Game Leaderboard to AWS EC2

This guide takes the [Python Cloud Game](../README.md) from your laptop to an **Amazon EC2 Linux server**. The **Snake game still runs on your computer**; the **Flask API and leaderboard run in AWS**.

> **Learning lab, not a production deployment.** The direct HTTP setup below is suitable only for a short, tightly restricted demo. HTTP does not encrypt the API key or scores. For use beyond a controlled lab, add HTTPS, stronger authentication, rate limiting, and operational safeguards.

## Architecture

```text
Student laptop                               AWS
+----------------------+         +--------------------------------+
| game.py (Pygame)     | --HTTP--> | EC2 (Ubuntu)                    |
| GAME_SERVER_URL      | POST     | Gunicorn -> Flask server.py     |
| GAME_API_KEY         | /score   |             |                  |
+----------------------+          |             v                  |
                                  |       leaderboard.db (SQLite)  |
Browser -- HTTP GET / ----------> | Flask leaderboard dashboard    |
                                  +--------------------------------+
```

**You will learn:** EC2, security groups, SSH, Python virtual environments, environment variables, HTTP APIs, and the difference between local applications and cloud services.

## Before you begin

- An AWS account with permission to launch EC2 instances and configure security groups.
- A terminal with SSH (macOS, Linux, or Windows PowerShell).
- Git and Python installed on the computer where you will play the game.
- The local game working using the [local setup instructions](../README.md).
- A budget: EC2 and associated public IPv4 addresses can incur charges even for small labs. Check pricing and terminate resources afterward.

## Step 1 — Launch an EC2 instance

1. Sign in to the **AWS Management Console** and open **EC2**.
2. Choose **Launch instance**.
3. Name it `python-cloud-game`.
4. Choose an **Ubuntu Server LTS** AMI (for example, Ubuntu 24.04 LTS).
5. Choose a small instance type appropriate for your budget (for example, `t3.micro`; free-tier eligibility depends on your account and AWS's current offer).
6. Create or select an EC2 key pair. Download the `.pem` file and keep it private.
7. Use a VPC and public subnet with a route to an internet gateway. Enable **Auto-assign public IP** if needed.
8. Configure the security group as described below.
9. Launch the instance and wait for its status checks to pass.

### Security group rules

For a **temporary classroom demo**, use these inbound rules:

| Type | Port | Source | Purpose |
| --- | --- | --- | --- |
| SSH | TCP 22 | **Your public IP /32** | Administration |
| Custom TCP | TCP 5000 | **Your public IP /32** (and explicitly approved students' IPs) | Dashboard and game API |

The default outbound rule is sufficient for installing packages.

**Do not set port 5000 to `0.0.0.0/0` for this lab.** Restrict access to known IP addresses. Students on other networks need their own public IPs allowlisted. A public IP can change; update the rule if necessary.

## Step 2 — Connect to EC2

Find the instance's **Public IPv4 address** in the EC2 console. Replace `EC2_PUBLIC_IP` with that value in commands below.

**macOS / Linux**

```bash
chmod 400 ~/Downloads/your-key.pem
ssh -i ~/Downloads/your-key.pem ubuntu@EC2_PUBLIC_IP
```

**Windows PowerShell**

```powershell
ssh -i "$HOME\Downloads\your-key.pem" ubuntu@EC2_PUBLIC_IP
```

The Ubuntu AMI's default SSH user is typically `ubuntu`. If SSH fails, check the instance status, IP address, security group, key file, and subnet routing.

## Step 3 — Install Python and clone the repository

Run these commands **on EC2**:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
git clone https://github.com/pyjoepy06/python-cloud-game.git
cd python-cloud-game
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The requirements include Pygame for local play, even though EC2 only needs Flask and Gunicorn to host the leaderboard.

## Step 4 — Start the Flask API using Gunicorn

Set a **unique, temporary demo key** on EC2. Do not use the literal placeholder in a real deployment:

```bash
export GAME_API_KEY='REPLACE_WITH_A_UNIQUE_DEMO_KEY'
gunicorn --workers 1 --bind 0.0.0.0:5000 server:app
```

Keep this terminal session open during the demo. `0.0.0.0` tells Gunicorn to listen on all EC2 network interfaces; **the security group controls which remote IPs can connect**.

From your **local browser**, visit:

- `http://EC2_PUBLIC_IP:5000/` — Live leaderboard
- `http://EC2_PUBLIC_IP:5000/health` — Health endpoint
- `http://EC2_PUBLIC_IP:5000/leaderboard` — Scores as JSON

The dashboard may initially show no scores. This is expected.

### Optional: Test from the EC2 terminal

In a **second SSH session**, run:

```bash
curl http://127.0.0.1:5000/health
```

You should receive JSON with `"status":"healthy"`.

## Step 5 — Connect the game on your laptop

Keep the EC2 server running. On your **laptop**, open a new terminal, clone the repo if necessary, activate your local virtual environment, and set these environment variables.

**macOS / Linux**

```bash
export GAME_SERVER_URL='http://EC2_PUBLIC_IP:5000'
export GAME_API_KEY='REPLACE_WITH_THE_SAME_DEMO_KEY'
python game.py
```

**Windows PowerShell**

```powershell
$env:GAME_SERVER_URL = 'http://EC2_PUBLIC_IP:5000'
$env:GAME_API_KEY = 'REPLACE_WITH_THE_SAME_DEMO_KEY'
python game.py
```

**Important:** Replace the placeholder IP and use **exactly the same key** as on EC2. In `game.py`, change `PLAYER = "Chantal"` to your name if desired.

Use the arrow keys to play Snake. Once the game ends, `game.py` sends a `POST /score` request to EC2. Open the public dashboard from an allowlisted IP and watch the leaderboard update (it refreshes every five seconds).

> **Security note:** The sample client sends the API key in an HTTP header. Anyone who can observe the unencrypted network traffic could obtain it. Only use disposable demo keys and non-sensitive player names in this temporary exercise. **Do not treat the demo key as secure over HTTP.** For a shared or ongoing deployment, put the API behind HTTPS and implement stronger controls.

## Step 6 — Understand the AWS components

| Component | What it does |
| --- | --- |
| EC2 | Virtual machine running the Python API |
| VPC | Network containing the instance |
| Public subnet / internet gateway | Allow network access to the public instance |
| Security group | Restricts inbound SSH and application traffic |
| Gunicorn | Runs the Flask application as a web server |
| Flask | Serves the dashboard and API endpoints |
| SQLite | Saves scores to `leaderboard.db` on the instance's local disk |
| Pygame | Runs the interactive Snake game on your laptop |

### What happens to scores?

`server.py` creates `leaderboard.db` in the repository folder. It stores each player's **highest** score. The database survives an application restart as long as its file remains on the same instance disk; it is **not** a managed database or multi-instance storage solution.

To reset the leaderboard, stop Gunicorn with **Ctrl+C**, then run on EC2:

```bash
rm -f leaderboard.db
```

Restart Gunicorn. **This permanently deletes the saved scores.**

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Browser cannot reach port 5000 | EC2 public IP, inbound rule for **your** public IP, instance status, subnet route, and running Gunicorn |
| SSH timeout | Port 22 rule, public IP, internet gateway, and source IP |
| `Permission denied (publickey)` | Correct private key, SSH user, and key file permissions |
| `ModuleNotFoundError` | Activate `.venv` and install requirements |
| `Address already in use` | Another process is using port 5000; stop it before restarting |
| `401 Unauthorized` on `POST /score` | Match `GAME_API_KEY` on both machines and restart the game/server after changes |
| Scores do not update | Finish the game; check its terminal output and EC2 Gunicorn logs |
| `/health` works but the game fails | Check `GAME_SERVER_URL`, port 5000 access from the laptop, and API key |

### Stop or restart the server

For this foreground lab, press **Ctrl+C** in the EC2 terminal to stop Gunicorn. Restart it with:

```bash
cd ~/python-cloud-game
source .venv/bin/activate
export GAME_API_KEY='REPLACE_WITH_YOUR_DEMO_KEY'
gunicorn --workers 1 --bind 0.0.0.0:5000 server:app
```

A disconnected SSH session can stop the foreground server. A later guide can introduce `systemd` for service management.

## Step 7 — Clean up to avoid charges

1. Stop the server and close SSH sessions.
2. In EC2, **terminate** the lab instance when finished (do not merely stop it if you no longer need it).
3. Delete any unused volumes, snapshots, or other resources created specifically for the lab.
4. Remove temporary security-group rules, and release any separately allocated Elastic IP address.
5. Review **AWS Billing and Cost Management** for remaining charges.

**Warning:** Terminating the instance can permanently remove its locally stored leaderboard database.

## Next improvements

- HTTPS with a domain name and reverse proxy or load balancer
- `systemd` service so the API survives SSH disconnection and reboot
- IAM role, logging, monitoring, and more robust secret handling
- More reliable storage and backups
- Terraform to deploy the AWS infrastructure
- Better authentication, rate limiting, and request validation

---

**Learning path:** Run locally → Understand APIs → Deploy Flask on EC2 → Connect your laptop to AWS → Secure and automate the deployment.
