# Job Application Email Tracker
Scans @live.com(it is a set up for microsoft email services but it is prtty much the same for all email providers ) inbox + junk, classifies emails (EN/DE), stores in MongoDB Atlas.
Deployed on Proxmox via Docker, accessed privately through Tailscale.

---

## Architecture

```
Phone or browser (Tailscale)
       │  encrypted tunnel, no public internet
       ▼
Proxmox VM/LXC (Tailscale node)
       │
       ▼
Docker Compose
  ├── dashboard   → Streamlit UI on :8501
  └── scheduler   → auto-syncs emails every 6 hours
       │
       ▼
MongoDB Atlas (cloud database)
```

---

## Setup Guide

### Step 1 — Proxmox VM/LXC requirements

```bash
Create LXC if not exist

```
```bash
# Install Docker 
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Tailscale 
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

### Step 2 — Copy project to Proxmox
```bash
# On terminal copy the project to Proxmox
scp -r ./job_tracker user@<lxc-ip>:/opt/job_tracker

# Or use git (create a private repo first, never push .env)
git clone https://github.com/yourname/job_tracker /opt/job_tracker
```

### Step 3 — Fill in `.env` on Proxmox
```bash
cd /opt/job_tracker
nano .env   # fill in all values
```

### Step 4 — First-time Microsoft login (one-time only)
The MS OAuth token must be created interactively on your Mac first,
then copied to Proxmox — Docker can't open a browser.

```bash
# On your Mac (inside the project folder)
python auth.py               # completes browser login, saves token

# Copy the token to Proxmox
scp data/token_cache.json user@<proxmox-ip>:/opt/job_tracker/data/
```

### Step 5 — Start Docker on Proxmox
```bash
cd /opt/job_tracker
docker compose up -d
```

### Step 6 — Access from your phone
1. Make sure Tailscale is running on both your phone and the Proxmox VM
2. Find your VM's Tailscale IP:
   ```bash
   tailscale ip -4
   # example output: 100.xx.xx.xx
   ```
3. Open on a browser on a phone or desktop: `http://100.xx.xx.xx:8501`
4. Enter your `DASHBOARD_PASSWORD`  

---

## Useful Commands

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Live logs
docker compose logs -f

# Scheduler logs only
docker compose logs -f scheduler

# Force manual sync
docker compose exec scheduler python sync.py

# Rebuild after code changes
docker compose up -d --build
```

---

## Security Model

| Layer | Protection |
|---|---|
| Network | Tailscale — zero public exposure, encrypted WireGuard tunnel |
| Dashboard | Password-protected login |
| Database | MongoDB Atlas locked to Proxmox IP only |
| Secrets | `.env` never committed, never in Docker image |
| Token | MS OAuth token stored in Docker volume, not in image |

### Lock MongoDB to your Proxmox Tailscale IP
Atlas → Network Access → delete `0.0.0.0/0` → Add IP → enter your Tailscale IP (`100.xx.xx.xx`)

---

## Project Files

| File | Purpose |
|---|---|
| `Dockerfile` | Container definition |
| `docker-compose.yml` | Dashboard + scheduler services |
| `auth.py` | Microsoft MSAL login |
| `fetch_emails.py` | Pulls emails from inbox + junk (2026+) |
| `classify.py` | Bilingual EN/DE keyword classifier |
| `database.py` | MongoDB Atlas storage |
| `sync.py` | fetch → classify → save pipeline |
| `scheduler.py` | Auto-syncs every 6 hours |
| `dashboard.py` | Mobile-friendly Streamlit UI |