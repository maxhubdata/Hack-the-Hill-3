# Hack the Hill 3 — Northwind Complaints Dashboard

A Flask dashboard for exploring and submitting utility complaints, backed by
Tiger Cloud (Postgres + TimescaleDB).

## Stack

- **Database**: Tiger Cloud (Postgres, with `complaints` set up as a TimescaleDB hypertable)
- **Backend**: Flask serves the dashboard page, the submission form, and a JSON API
- **Frontend**: plain HTML/CSS/JS, charts drawn with Chart.js via `fetch()` calls to the API (hosted on render)

## Project structure

```
complaints_dashboard/
├── app.py                   Flask app: routes + JSON API endpoints
├── schema.sql                Table + hypertable + index definitions
├── requirements.txt           Python dependencies
├── templates/
│   ├── index.html             Dashboard page
│   └── submit.html            "Submit a complaint" form
└── static/
    ├── css/style.css           Styling
    └── js/dashboard.js         Fetches from the API and renders charts/table
```

## Setup

### 1. Create a Tiger Cloud database

Sign up at [tigerdata.com](https://www.tigerdata.com) and create a service.
Copy its connection string from the Tiger Console. It looks like:

```
postgres://user:password@host:port/dbname?sslmode=require
```

### 2. Install dependencies

```bash
cd complaints_dashboard
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Create the table

Paste the contents of `schema.sql` into the SQL editor in the Tiger Console
and run it (or use `psql "$DATABASE_URL" -f schema.sql` if you have `psql`
installed locally).

### 4. Load your complaints data

The easiest way in is Tiger Console's built-in CSV importer: **Actions →
Import data → Upload CSV file**, ingesting into the existing `complaints`
table. From there on, new complaints can also be added straight through the
dashboard's own submission form (see below). No re-import needed.

### 5. Run the app

```bash
export DATABASE_URL="postgres://user:password@host:port/dbname?sslmode=require"
python app.py
```

Open **http://localhost:5000**.

## What's in the dashboard

- **KPI cards**: total complaints, currently open, avg. days to close, SLA breach rate, reopened count
- **Trend chart**: complaints opened per month, with SLA breach % overlaid
- **Breakdown charts**: by category, region, priority, channel
- **Filters**: date range, category, region, status, priority, channel; everything on the page responds to the active filters
- **Complaints table**: paginated list of the underlying rows
- **Submit form** (`/submit`): lets anyone log a new complaint directly into the database. It's saved as `Open` and shows up on the dashboard immediately

## Deploying

This deploys to Render (or Fly.io/Railway) as-is. A couple of Render-specific
notes learned the hard way:

- **Root Directory**: set to `complaints_dashboard`, that's where `requirements.txt` and `app.py` actually live.
- **Build command**: `pip install -r requirements.txt`
- **Start command**: `gunicorn app:app` (not the Django-style `your_application.wsgi` Render fills in by default)
- **Python version**: pin it explicitly. Add a `PYTHON_VERSION` environment variable set to `3.11.11` in Render's Environment tab, Render's newer default Python versions can ship without a compatible prebuilt wheel for `psycopg2-binary`, which crashes the app on startup.
- **`DATABASE_URL`**: add it under Render's Environment tab, same as locally.
- Don't run with `debug=True` in production.

## Extending it

- Split the table into open complaints and closed complaints, the closed complaints table would act as a document archive (replacing the old DocVault).
- Once obtained the data for the regulatory reporting (we did not have it), create an autofill form with the information extracted straight from the TigerData database in order to streamline the process and save on time and cost.
