import re
from collections import Counter
from database import get_connection


STOPWORDS = {
    "the", "is", "a", "an", "of", "to", "in", "on",
    "for", "and", "or", "with", "as", "by", "at",
    "from", "that", "this", "it", "be", "are"
}

def preprocess_text(title, description, content):
    """
    Returns a Counter: {term: frequency}
    Applies simple weighting:
      title x3, description x2, content x1
    """

    parts = []

    if title:
        parts.append((title + " ") * 3)
    if description:
        parts.append((description + " ") * 2)
    if content:
        parts.append(content)

    full_text = " ".join(parts).lower()

    # remove punctuation & numbers
    full_text = re.sub(r"[^a-z\s]", " ", full_text)

    tokens = full_text.split()

    filtered = [
        t for t in tokens
        if len(t) >= 2 and t not in STOPWORDS
    ]

    return Counter(filtered)
# helper functions for indexer
def get_or_create_term(conn, term):
    # testing
    print(f"[INDEXER] inserting/fetching term: {term}")

    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM terms WHERE term = ?",
        (term,)
    )
    row = cur.fetchone()

    if row:
        return row[0]

    cur.execute(
        "INSERT INTO terms (term) VALUES (?)",
        (term,)
    )
    conn.commit()
    return cur.lastrowid

def upsert_posting(conn, term_id, page_id, freq):
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO postings (term_id, page_id, frequency)
        VALUES (?, ?, ?)
        ON CONFLICT(term_id, page_id)
        DO UPDATE SET frequency = excluded.frequency
    """, (term_id, page_id, freq))

    conn.commit()

# main function to index a page
def index_page( page_id, title, description, content):
    # testing
    print(f"[INDEXER] index_page called for page_id={page_id}")

    """
    Incrementally index a single page.
    Safe to call after upsert_page().
    """
    conn = get_connection()
    try:
        term_freqs = preprocess_text(title, description, content)
    # testing
        print(f"[INDEXER] tokens count = {len(term_freqs)}")

        for term, freq in term_freqs.items():
            term_id = get_or_create_term(conn, term)
            upsert_posting(conn, term_id, page_id, freq)
        conn.commit()
    finally:
        conn.close()
