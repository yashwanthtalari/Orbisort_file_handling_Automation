import sqlite3

DB_PATH = "orbisort.db"


def initialize_db():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_path TEXT,
        new_path TEXT,
        file_hash TEXT,
        size INTEGER,
        created_at TEXT,
        processed_at TEXT,
        status TEXT
    )
    """
    )

    conn.commit()
    conn.close()
