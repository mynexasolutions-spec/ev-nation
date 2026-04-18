# Manual Test Setup

## Quick Start

The default local setup now uses SQLite, so you can usually start the app immediately with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_local.ps1
```

Or directly:

```powershell
uvicorn app.main:app --reload
```

Default admin credentials created by the script:

- email: `admin@evnation.local`
- password: `Admin12345`

## What the Script Does

- creates `.env` from `.env.example` if missing
- generates a random `SECRET_KEY` if the `.env` file is created
- starts the app, whose startup bootstrap creates missing tables
- ensures the default local admin exists during app startup
- starts Uvicorn with reload enabled

## Default Local Database

The default `DATABASE_URL` is:

```env
DATABASE_URL=sqlite:///C:/Users/<your-user>/AppData/Local/EV_Nation/ev_nation.db
```

This keeps the SQLite file out of OneDrive-synced folders, which is more reliable for local testing on Windows.

## PostgreSQL Later

When you want to switch back to PostgreSQL, change `DATABASE_URL` in `.env` to your Postgres connection string.

## Manual Admin Creation

You can also create/update an admin separately:

```powershell
python -B .\scripts\create_admin.py --email admin@evnation.local --password Admin12345 --full-name "Local Admin" --superuser
```
