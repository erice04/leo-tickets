Legacy files kept locally — not tracked in git.

  data/               Yale directory dumps, scanner Excel log, scraped HTML
  yalies/             Old directory scraper scripts (set YALIES_TOKEN locally)
  client_secret.json  Old Google OAuth JSON (use .env instead)

To seed Postgres from a local Yale directory:
  python scripts/seed_database.py

Place yale_directory.txt in archive/data/ or data/ (see seed script).
