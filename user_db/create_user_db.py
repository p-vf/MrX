import sqlite3

if __name__ == "__main__":
    conn = sqlite3.connect("user.db")
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