import sqlite3
from pathlib import Path

def main():
    create_user_db(Path("users.db"))

def create_user_db(dbpath: Path):
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()

    # role: 0 user, 1 admin
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        role INTEGER DEFAULT 0,
        salt TEXT,
        pw_hash TEXT
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()