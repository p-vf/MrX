from pathlib import Path
# make imports work if this file is run as a standalone script
import sys
sys.path.append(str(Path(__file__).parent.parent))
from server.spacial_store import SpacialStore
from typing import override
import sqlite3
import base64
import json
import os
import random
import copy

class SpacialDBManager(SpacialStore):
    def __init__(self, db: Path):
        self.conn = sqlite3.connect(db)
        self.cur = self.conn.cursor()
        self.load_spacial_data()

    @override
    def insert(self, user_id: str, quad_sequence: list[int]):
        super().insert(user_id, quad_sequence)
        self.cur.execute("INSERT OR REPLACE INTO user_area (user, area) VALUES (?, ?);", (user_id, base64.b64encode(json.dumps(quad_sequence).encode())))
        self.conn.commit()

    def load_spacial_data(self):
        self.cur.execute("SELECT * FROM user_area;")
        self._user_path = {}
        areas = self.cur.fetchall()
        for user, area in areas:
            super().insert(user, json.loads(base64.b64decode(area).decode()))

    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def __del__(self):
        self.close()

def create_spacial_db(dbpath: Path):
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()

    # Maybe make user foreign key referencing the usernames in users.db
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_area (
        user TEXT PRIMARY KEY,
        area BLOB
    );
    """)

    conn.commit()
    conn.close()

test_db = Path("test_spacial.db")
def property_based_tests():
    if os.path.exists(test_db):
        os.remove(test_db)
    create_spacial_db(test_db)
    print("running property based test")
    s = SpacialDBManager(test_db)
    namelist = ["chad", "chud", "alice", "bob", "carol", "diogenes", "hrodebert"]
    # check that each change is reflected properly in the database
    for _ in range(500):
        name = random.choice(namelist)
        accuracy = random.randint(1, 8)
        quad_sequence = random.choices(range(4), k=accuracy)
        s.insert(name, quad_sequence)
        old_data = copy.deepcopy(s._user_path)
        s.load_spacial_data()
        assert old_data == s._user_path, f"\n{old_data}\n======\n{s._user_path}"
    print("property based test successful")

def manual_tests():
    if os.path.exists(test_db):
        os.remove(test_db)
    create_spacial_db(test_db)
    print("running manual tests")
    s = SpacialDBManager(test_db)
    s.insert("chad", [1, 2, 3, 0])
    s.insert("chud", [1, 2, 3, 3, 0])
    s.insert("chad", [1, 2, 3, 3, 0, 0])
    expected = {"chad": [1, 2, 3, 3, 0, 0], "chud": [1, 2, 3, 3, 0]}
    assert s._user_path == expected, f"\n{expected}\n======\n{s._user_path}"
    print("manual tests successful")


def main():
    property_based_tests()
    manual_tests()

if __name__ == "__main__":
    main()