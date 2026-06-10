from pathlib import Path
import sqlite3
from typing import override
import os
import random
import copy
import sys
sys.path.append(str(Path(__file__).parent.parent))
from server.pending_request_store import PendingRequestStore

def create_pending_request_db(dbpath: Path):
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()

    # Maybe make user reference the usernames in users.db
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pending_request (
        user TEXT PRIMARY KEY
    );
    """)

    conn.commit()
    conn.close()

class PendingRequestDBManager(PendingRequestStore):
    def __init__(self, db: Path):
        self.conn = sqlite3.connect(db)
        self.cur = self.conn.cursor()
        self.load_pending_requests()

    @override
    def add_pending(self, user_id: str):
        super().add_pending(user_id)
        self.cur.execute("INSERT OR REPLACE INTO pending_request (user) VALUES (?);", (user_id,))
        self.conn.commit()

    @override
    def remove_pending(self, user_id: str):
        super().remove_pending(user_id)
        self.cur.execute("DELETE FROM pending_request WHERE user = ?", (user_id,))

    def load_pending_requests(self):
        self.cur.execute("SELECT * FROM pending_request;")
        self._pending = set()
        pending_requests = self.cur.fetchall()
        for pending in pending_requests:
            super().add_pending(*pending)

    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def __del__(self):
        self.close()

test_db = Path("test_permission.db")
def property_based_test_consistency():
    if os.path.exists(test_db):
        os.remove(test_db)
    create_pending_request_db(test_db )
    print("running property based test")
    p = PendingRequestDBManager(test_db )
    namelist = ["chad", "chud", "alice", "bob", "carol", "diogenes", "hrodebert"]
    # check that each change is reflected properly in the database
    for _ in range(500):
        remove = random.choice([True, False])
        name = random.choice(namelist)
        if remove:
            p.remove_pending(name)
        else:
            p.add_pending(name)
        old_perms = copy.deepcopy(p._pending)
        p.load_pending_requests()
        assert old_perms == p._pending, f"\n{old_perms}\n======\n{p._pending}"
    print("property based test successful")

def manual_tests():
    if os.path.exists(test_db):
        os.remove(test_db)
    create_pending_request_db(test_db )
    print("running manual test")
    p = PendingRequestDBManager(test_db )
    # TODO
    p.add_pending("chud")
    p.remove_pending("chad")
    p.add_pending("chad")
    p.remove_pending("chud")

    assert p._pending == {"chad"}
    print("manual test successful")

def main():
    property_based_test_consistency()
    manual_tests()

if __name__ == "__main__":
    main()