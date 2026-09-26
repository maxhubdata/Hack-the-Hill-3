

import os

import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")


FILTERABLE_COLUMNS = {
    "category": "category",
    "region": "region",
    "status": "status",
    "priority": "priority",
    "channel": "channel",
}


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def build_filters(args):
    """Turn query-string filters into a WHERE clause + params list."""
    clauses = []
    params = []

    start = args.get("start")
    end = args.get("end")
    if start:
        clauses.append("date_opened >= %s")
        params.append(start)
    if end:
        clauses.append("date_opened <= %s")
        params.append(end)

    for query_key, column in FILTERABLE_COLUMNS.items():
        value = args.get(query_key)
        if value:
            clauses.append(f"{column} = %s")
            params.append(value)

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return where_sql, params


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/filters")
def api_filters():
    """Distinct values to populate the filter dropdowns."""
    conn = get_connection()
    cur = conn.cursor()
    result = {}
    for key, column in FILTERABLE_COLUMNS.items():
        cur.execute(f"SELECT DISTINCT {column} AS value FROM complaints ORDER BY 1")
        result[key] = [row["value"] for row in cur.fetchall()]
    cur.execute("SELECT MIN(date_opened) AS min_date, MAX(date_opened) AS max_date FROM complaints")
    date_range = cur.fetchone()
    result["date_range"] = {
        "min": date_range["min_date"].isoformat() if date_range["min_date"] else None,
        "max": date_range["max_date"].isoformat() if date_range["max_date"] else None,
    }
    cur.close()
    conn.close()
    return jsonify(result)


@app.route("/api/kpis")
def api_kpis():
    where_sql, params = build_filters(request.args)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE status = 'Open') AS open_count,
            COUNT(*) FILTER (WHERE reopened) AS reopened_count,
            ROUND(AVG(days_to_close) FILTER (WHERE days_to_close IS NOT NULL), 1) AS avg_days_to_close,
            ROUND(
                100.0 * COUNT(*) FILTER (WHERE sla_breach) / NULLIF(COUNT(*), 0), 1
            ) AS sla_breach_pct
        FROM complaints
        {where_sql}
        """,
        params,
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return jsonify(row)


@app.route("/api/trend")
def api_trend():
    """Complaints opened per month, plus SLA breach rate per month."""
    where_sql, params = build_filters(request.args)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT
            DATE_TRUNC('month', date_opened)::date AS month,
            COUNT(*) AS opened,
            ROUND(
                100.0 * COUNT(*) FILTER (WHERE sla_breach) / NULLIF(COUNT(*), 0), 1
            ) AS sla_breach_pct
        FROM complaints
        {where_sql}
        GROUP BY 1
        ORDER BY 1
        """,
        params,
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)


def group_count_endpoint(column):
    where_sql, params = build_filters(request.args)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT {column} AS label, COUNT(*) AS count
        FROM complaints
        {where_sql}
        GROUP BY 1
        ORDER BY count DESC
        """,
        params,
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)


@app.route("/api/by-category")
def api_by_category():
    return group_count_endpoint("category")


@app.route("/api/by-region")
def api_by_region():
    return group_count_endpoint("region")


@app.route("/api/by-priority")
def api_by_priority():
    return group_count_endpoint("priority")


@app.route("/api/by-channel")
def api_by_channel():
    return group_count_endpoint("channel")


@app.route("/api/complaints")
def api_complaints():
    """Paginated table of individual complaints."""
    where_sql, params = build_filters(request.args)
    page = max(int(request.args.get("page", 1)), 1)
    per_page = min(int(request.args.get("per_page", 25)), 100)
    offset = (page - 1) * per_page

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) AS total FROM complaints {where_sql}", params)
    total = cur.fetchone()["total"]

    cur.execute(
        f"""
        SELECT complaint_id, date_opened, date_closed, status, channel,
               category, priority, region, days_to_close, sla_breach, reopened
        FROM complaints
        {where_sql}
        ORDER BY date_opened DESC
        LIMIT %s OFFSET %s
        """,
        params + [per_page, offset],
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify({"total": total, "page": page, "per_page": per_page, "rows": rows})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
