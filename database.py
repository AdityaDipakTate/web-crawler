import sqlite3
import json
from datetime import datetime

DB_PATH = "crawler.db"
 
# ------------------------------------
# Connection
# ------------------------------------
def get_connection():
    return sqlite3.connect(DB_PATH)

# ------------------------------------
# Initialize DB
# ------------------------------------
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        domain TEXT,
        title TEXT,
        description TEXT,
        content TEXT,
        links TEXT,
        depth INTEGER,
        status_code INTEGER,
        content_type TEXT,
        crawled_at TEXT
    )
    """)

    conn.commit()
    conn.close()

# ------------------------------------
# Insert Page
# ------------------------------------
def save_page(url, domain, title, desc, content,
              links, depth, status_code, content_type):

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
        INSERT OR IGNORE INTO pages
        (url, domain, title, description, content,
         links, depth, status_code, content_type, crawled_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            url,
            domain,
            title,
            desc,
            content,
            json.dumps(list(links)),
            depth,
            status_code,
            content_type,
            datetime.utcnow().isoformat()
        ))

        conn.commit()

    except Exception as e:
        print("DB insert error:", e)

    finally:
        conn.close()

# ------------------------------------
# Utility
# ------------------------------------
def page_exists(url):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pages WHERE url = ?", (url,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists
