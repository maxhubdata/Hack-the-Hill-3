# Complaints dashboard

A Flask + Tiger Cloud (Postgres/TimescaleDB) dashboard for the Northwind
complaints dataset (25,416 rows, Oct 2024–Sep 2026).

## Stack

- **Database**: Tiger Cloud (Postgres, optionally a TimescaleDB hypertable)
- **Backend**: Flask, serving both the page and JSON API endpoints
- **Frontend**: plain HTML/CSS/JS with Chart.js, calling the Flask API with `fetch()`

## Setup

### 1. Create your Tiger Cloud database

Sign up at [tigerdata.com](https://www.tigerdata.com), create a service, and
copy its connection string from the Tiger Console. It looks like:

```
postgres://user:password@host:port/dbname?sslmode=require
```

### 2. Install dependencies

```bash
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Create the table

```bash
export DATABASE_URL="postgres://user:password@host:port/dbname?sslmode=require"
psql "$DATABASE_URL" -f schema.sql
```

(If you don't have `psql` installed locally, you can also paste the contents
of `schema.sql` into the SQL editor in the Tiger Console.)

### 4. Import your CSV

```bash
python import_csv.py /path/to/northwind_complaints.csv
```

This loads all rows in batches of 1,000 and skips duplicates on re-run.

### 5. Run the dashboard

```bash
export DATABASE_URL="postgres://user:password@host:port/dbname?sslmode=require"
python app.py
```

Open **http://localhost:5000** in your browser.

## What's in the dashboard

- KPI cards: total complaints, currently open, avg. days to close, SLA breach rate, reopened count
- Trend chart: complaints opened per month, with SLA breach % overlaid
- Breakdown charts: by category, region, priority, channel
- Filters: date range, category, region, status, priority, channel — all charts and the table respond to the active filters
- A paginated table of the underlying complaints

## Project structure

```
app.py                  Flask app: page route + JSON API endpoints
schema.sql               Table + hypertable + index definitions
import_csv.py             One-off script to load the CSV into Tiger Cloud
requirements.txt          Python dependencies
templates/index.html      Dashboard page
static/css/style.css      Styling
static/js/dashboard.js    Fetches from the API and renders charts/table
```

## Deploying

Once it works locally, this Flask app deploys as-is to Render, Fly.io, or
Railway — just set the `DATABASE_URL` environment variable on the host to
your Tiger Cloud connection string, and don't run with `debug=True` in
production (remove that flag or set `debug=False` in `app.run(...)`).

## Extending it

- Add more filters (e.g. `account_id` search, SLA breach only)
- Add a chart for `bill_correction_value` totals by category
- Add authentication if this will be exposed outside your team
- Add caching (e.g. Flask-Caching) on the aggregate endpoints if the table grows large
