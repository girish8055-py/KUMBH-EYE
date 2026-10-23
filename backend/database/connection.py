import sqlite3

from backend.config.settings import DB_PATH


def get_db():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS crowd_history (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id  TEXT,
            count     INTEGER,
            density   REAL,
            avg_conf  REAL,
            level     TEXT,
            timestamp TEXT
        );
        CREATE TABLE IF NOT EXISTS vehicle_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id   TEXT,
            total      INTEGER,
            density    REAL,
            avg_conf   REAL,
            classes    TEXT,
            timestamp  TEXT
        );
        CREATE TABLE IF NOT EXISTS parking_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id   TEXT,
            occupied   INTEGER,
            available  INTEGER,
            total      INTEGER,
            rate       REAL,
            status     TEXT,
            timestamp  TEXT
        );
        CREATE TABLE IF NOT EXISTS alert_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            title     TEXT,
            video_id  TEXT,
            alert_key TEXT,
            timestamp TEXT
        );
        CREATE TABLE IF NOT EXISTS complaint_log (
            id          TEXT PRIMARY KEY,
            name        TEXT,
            phone       TEXT,
            location    TEXT,
            category    TEXT,
            description TEXT,
            status      TEXT DEFAULT 'Open',
            timestamp   TEXT
        );
    """)
    conn.commit()
    conn.close()
