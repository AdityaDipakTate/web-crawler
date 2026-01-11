import sqlite3
import json
from datetime import datetime

DB_PATH = "crawler.db"
 
# Connection
def get_connection():
    return sqlite3.connect(DB_PATH)

# Initialize DB
# def init_db():
#     conn = get_connection()
#     cur = conn.cursor()

#     cur.execute("""
#     CREATE TABLE IF NOT EXISTS pages (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         url TEXT UNIQUE,
#         domain TEXT,
#         title TEXT,
#         description TEXT,
#         content TEXT,
#         links TEXT,
#         depth INTEGER,
#         status_code INTEGER,
#         content_type TEXT,
#         crawled_at TEXT
#     )
#     """)

#     conn.commit()
#     conn.close()

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # pages table (upgraded, minimal)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        domain TEXT,

        title TEXT,
        description TEXT,
        content TEXT,

        content_hash TEXT,
        content_length INTEGER,

        depth INTEGER,
        status_code INTEGER,

        last_crawled TEXT,
        crawl_count INTEGER DEFAULT 1
    )
    """)

    # links table (NEW)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS links (
        from_page INTEGER,
        to_page INTEGER,

        UNIQUE(from_page, to_page),

        FOREIGN KEY(from_page) REFERENCES pages(id),
        FOREIGN KEY(to_page) REFERENCES pages(id)
    )
    """)

    conn.commit()
    conn.close()

# Insert Page
# def save_page(url, domain, title, desc, content,
#               links, depth, status_code, content_type):

#     conn = get_connection()
#     cur = conn.cursor()

#     try:
#         cur.execute("""
#         INSERT OR IGNORE INTO pages
#         (url, domain, title, description, content,
#          links, depth, status_code, content_type, crawled_at)
#         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """, (
#             url,
#             domain,
#             title,
#             desc,
#             content,
#             json.dumps(list(links)),
#             depth,
#             status_code,
#             content_type,
#             datetime.utcnow().isoformat()
#         ))

#         conn.commit()

#     except Exception as e:
#         print("DB insert error:", e)

#     finally:
#         conn.close()

# insert replace with upsert
def upsert_page(
                url, domain, title, desc, content,
                content_hash, content_length,
                depth, status_code, content_type
                ):
    conn = get_connection()
    cur = conn.cursor()

    # Check if page exists
    cur.execute(
        "SELECT id, content_hash FROM pages WHERE url = ?",
        (url,)
    )
    row = cur.fetchone()

    now = datetime.utcnow().isoformat()

    if row is None:
        # INSERT new page
        cur.execute("""
        INSERT INTO pages
        (url, domain, title, description, content,
         content_hash, content_length,
         depth, status_code, content_type,
         crawled_at, crawl_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            url, domain, title, desc, content,
            content_hash, content_length,
            depth, status_code, content_type,
            now
        ))
        page_id = cur.lastrowid

    else:
        page_id, old_hash = row

        if old_hash == content_hash:
            # Content unchanged → metadata update only
            cur.execute("""
            UPDATE pages
            SET crawl_count = crawl_count + 1,
                status_code = ?,
                content_type = ?,
                crawled_at = ?
            WHERE id = ?
            """, (status_code, content_type, now, page_id))

        else:
            # Content changed → full update
            cur.execute("""
            UPDATE pages
            SET title = ?,
                description = ?,
                content = ?,
                content_hash = ?,
                content_length = ?,
                crawl_count = crawl_count + 1,
                status_code = ?,
                content_type = ?,
                crawled_at = ?
            WHERE id = ?
            """, (
                title, desc, content,
                content_hash, content_length,
                status_code, content_type,
                now, page_id
            ))

    conn.commit()
    conn.close()
    return page_id

# Utility
def page_exists(url):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pages WHERE url = ?", (url,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

def insert_link(from_page_id, to_page_id):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
        INSERT OR IGNORE INTO links (from_page, to_page)
        VALUES (?, ?)
        """, (from_page_id, to_page_id))
        conn.commit()
    finally:
        conn.close()

