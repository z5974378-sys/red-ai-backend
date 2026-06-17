import sqlite3
from contextlib import contextmanager
from config import DB_PATH


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id           TEXT PRIMARY KEY,
            name         TEXT,
            positioning  TEXT NOT NULL DEFAULT '',
            audience     TEXT NOT NULL DEFAULT '',
            saved_titles TEXT NOT NULL DEFAULT '',
            comments     TEXT NOT NULL DEFAULT '',
            competitors  TEXT NOT NULL DEFAULT '',
            note_links   TEXT NOT NULL DEFAULT '',
            note_content TEXT NOT NULL DEFAULT '',
            topic_count  INTEGER NOT NULL DEFAULT 12,
            risk_level   TEXT NOT NULL DEFAULT 'normal',
            title_style  TEXT NOT NULL DEFAULT 'bold',
            created_at   TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS topics (
            id          TEXT PRIMARY KEY,
            session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            position    INTEGER NOT NULL DEFAULT 0,
            topic       TEXT NOT NULL,
            pain        TEXT NOT NULL DEFAULT '',
            angle       TEXT NOT NULL DEFAULT '',
            cover       TEXT NOT NULL DEFAULT '',
            script      TEXT NOT NULL DEFAULT '',
            priority    TEXT NOT NULL DEFAULT '中',
            risk        TEXT NOT NULL DEFAULT '',
            series      INTEGER NOT NULL DEFAULT 0,
            human       INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_topics_session ON topics(session_id, position);

        CREATE TABLE IF NOT EXISTS images (
            id          TEXT PRIMARY KEY,
            session_id  TEXT REFERENCES sessions(id) ON DELETE SET NULL,
            filename    TEXT NOT NULL,
            stored_path TEXT NOT NULL,
            url_path    TEXT NOT NULL,
            size_bytes  INTEGER NOT NULL DEFAULT 0,
            mime_type   TEXT NOT NULL DEFAULT 'image/jpeg',
            ocr_text    TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_images_session ON images(session_id);
    """)
    conn.commit()
    conn.close()


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
