# LEO Tickets

Flask ticketing app for Yale/LEO events. Guests sign in with Google OAuth, receive a QR ticket if they are on the guest list, and door staff scan tickets at the event.

## Features

- **Ticket page** (`/`) — Google login, guest-list check, QR code ticket
- **Scanner** (`/scanner`) — scan QR codes, show name/photo from Yale directory, log entries
- **Admin panel** (`/admin`) — guest list, blacklist, ticket title, scanner log, Yalies image toggle
- **REST API** (`/api/v1`) — health, event settings, allowlist, scans, users (API key or session auth)

## Stack

- Python 3.11, Flask, SQLAlchemy, PostgreSQL
- Google OAuth 2.0
- Gunicorn + Docker for production

## Local development

### Prerequisites

- Python 3.11+
- Docker (for PostgreSQL)

### Setup

```powershell
# Clone and install
pip install -r requirements.txt

# Environment
copy .env.example .env
# Edit .env with your Google OAuth credentials and secrets

# Local data (not committed — use your real guest/admin lists)
copy data\emails.example.txt data\emails.txt
copy data\admin.example.txt data\admin.txt
copy data\ticket_info.example.txt data\ticket_info.txt
copy data\status.example.json data\status.json

# Database
docker compose up db -d
$env:FLASK_APP = "app.py"
flask db upgrade
python scripts/seed_database.py --skip-scans   # add --skip-directory to skip Yale directory

# Run
.\start.ps1
# or: python app.py
```

Open http://127.0.0.1:5000

### Google OAuth (local)

In [Google Cloud Console](https://console.cloud.google.com/apis/credentials), add:

- **Redirect URI:** `http://localhost:5000/google/auth`
- **JavaScript origin:** `http://localhost:5000`

## Deploy (Render + Neon)

1. Push this repo to GitHub.
2. Create a **Neon** Postgres project (no Neon Auth needed — only the database).
3. Create a **Render** Web Service from the repo (Docker, free tier).
4. Set environment variables on Render (see `.env.example`).
5. Update Google OAuth redirect URIs to your Render URL.
6. Seed production from your laptop:

```powershell
$env:DATABASE_URL = "postgresql://..."   # Neon connection string
python scripts/seed_database.py
```

Place `yale_directory.txt` in `archive/data/` locally before seeding the Yale directory (~47k rows, takes several minutes).

## Environment variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Flask session signing key (random hex string) |
| `DATABASE_URL` | PostgreSQL connection string |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth |
| `GOOGLE_AUTH_REDIRECT_URI` | e.g. `https://your-app.onrender.com/google/auth` |
| `BASE_URI` | e.g. `https://your-app.onrender.com/` |
| `SUPERADMIN_EMAIL` | Google account that gets superadmin on login |
| `SCANNER_API_KEY` | Auth for scanner kiosk POST requests |
| `ADMIN_API_KEY` | Optional REST API admin key |

Generate secrets:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

## Project layout

```
app/              Flask application (routes, auth, services, API)
data/             Example seed files (*.example.*); real lists stay local
archive/data/     Yale directory and legacy files (local only, gitignored)
migrations/       Alembic database migrations
scripts/          seed_database.py
templates/        HTML templates
```

## Seeding

```powershell
python scripts/seed_database.py                    # full seed
python scripts/seed_database.py --skip-directory   # guest list + admins only (fast)
python scripts/seed_database.py --skip-scans       # skip Excel scan log import
```

## License

Private / event use — Yale/LEO.
