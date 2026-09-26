-- Schema for the Northwind complaints dataset, designed for Tiger Cloud
-- (Postgres + TimescaleDB). Run this once against your Tiger Cloud service
-- before importing the CSV.

CREATE TABLE IF NOT EXISTS complaints (
    complaint_id                    TEXT        NOT NULL,
    date_opened                     DATE        NOT NULL,
    date_closed                     DATE,
    status                          TEXT        NOT NULL,
    channel                         TEXT        NOT NULL,
    category                        TEXT        NOT NULL,
    priority                        TEXT        NOT NULL,
    region                          TEXT        NOT NULL,
    source_system                   TEXT        NOT NULL,
    transferred_between_systems     BOOLEAN     NOT NULL DEFAULT FALSE,
    sla_days                        INTEGER,
    days_to_close                   INTEGER,
    sla_breach                      BOOLEAN     NOT NULL DEFAULT FALSE,
    reopened                        BOOLEAN     NOT NULL DEFAULT FALSE,
    resolution_action               TEXT,
    resolvable_by_information_only  BOOLEAN,
    bill_correction_value           NUMERIC(10, 2),
    account_id                      TEXT        NOT NULL,
    -- Timescale hypertables require the partitioning column to be part of
    -- any primary/unique key, so date_opened joins complaint_id here.
    PRIMARY KEY (complaint_id, date_opened)
);

-- Turn this into a hypertable partitioned by date_opened. This is optional
-- for 25k rows, but it's what Tiger Cloud/TimescaleDB is built for, and it
-- pays off once this table grows into the millions of rows (automatic
-- partitioning, much faster time-range queries, and compression on old
-- chunks). Safe to skip if you just want plain Postgres.
SELECT create_hypertable('complaints', by_range('date_opened'), if_not_exists => TRUE);

-- Helpful indexes for the dashboard's filters and group-bys.
CREATE INDEX IF NOT EXISTS idx_complaints_category ON complaints (category);
CREATE INDEX IF NOT EXISTS idx_complaints_region   ON complaints (region);
CREATE INDEX IF NOT EXISTS idx_complaints_status    ON complaints (status);
CREATE INDEX IF NOT EXISTS idx_complaints_priority  ON complaints (priority);
CREATE INDEX IF NOT EXISTS idx_complaints_channel   ON complaints (channel);
