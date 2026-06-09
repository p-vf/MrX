import sqlite3
from pathlib import Path
import random
import copy
import os
from typing import override
# make imports work if this file is run as a standalone script
import sys
sys.path.append(str(Path(__file__).parent.parent))
from server.permission_store import PermissionStore

def create_perm_db(dbpath: Path):
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()

    # Maybe make subject and object reference the usernames in users.db
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS permission (
        subject TEXT,
        object TEXT,
        accuracy INTEGER,
        PRIMARY KEY (subject, object)
    );
    """)

    conn.commit()
    conn.close()

class PermissionDBManager(PermissionStore):
    """this database does NOT manage friendships symmetrically. so to end a
    friendship between bob and alice, one has to call
    update(bob, alice, 0) AND update(alice, bob, 0)"""
    def __init__(self, db: Path):
        self.conn = sqlite3.connect(db)
        self.cur = self.conn.cursor()
        self.load_perms()

    @override
    def update(self, subj_user_id: str, obj_user_id: str, accuracy: int):
        super().update(subj_user_id, obj_user_id, accuracy)
        if accuracy == 0:
            self.cur.execute("DELETE FROM permission WHERE subject = ? AND object = ?", (subj_user_id, obj_user_id))
        else:
            self.cur.execute("INSERT OR REPLACE INTO permission (subject, object, accuracy) VALUES (?, ?, ?);", (subj_user_id, obj_user_id, accuracy))
        self.conn.commit()

    def load_perms(self):
        self.cur.execute("SELECT * FROM permission;")
        self._perms = {}
        perms = self.cur.fetchall()
        for perm in perms:
            super().update(*perm)

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
    create_perm_db(test_db)
    print("running property based test")
    p = PermissionDBManager(test_db )
    namelist = ["chad", "chud", "alice", "bob", "carol", "diogenes", "hrodebert"]
    # check that each change is reflected properly in the database
    for _ in range(500):
        name1 = random.choice(namelist)
        namelist.remove(name1)
        name2 = random.choice(namelist)
        namelist.append(name1)
        accuracy = random.randint(0, 4)
        p.update(name1, name2, accuracy)
        old_perms = copy.deepcopy(p._perms)
        p.load_perms()
        assert old_perms == p._perms, f"\n{old_perms}\n======\n{p._perms}"
    for s in p._perms:
        for o in p._perms[s]:
            if p._perms[s][o] == 0:
                assert False, f"0 stored in entry {s}, {o}"
    print("property based test successful")

def manual_tests():
    if os.path.exists(test_db):
        os.remove(test_db)
    create_perm_db(test_db )
    print("running manual test")
    p = PermissionDBManager(test_db )
    p.update("chud", "chad", 1)
    p.update("chad", "chud", 2)
    p.update("chad", "bob", 3)
    p.update("alice", "chad", 2)
    p.update("chud", "chad", 0)

    assert p._perms == {"chad": {"chud": 2, "bob": 3}, "alice": {"chad": 2}}
    print("manual test successful")

def main():
    property_based_test_consistency()
    manual_tests()

if __name__ == "__main__":
    main()