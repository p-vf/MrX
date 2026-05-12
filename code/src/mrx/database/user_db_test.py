import sqlite3
from .user_db import UserDBManager
from .create_user_db import main as create_db

NO_OF_TESTS = 7

class UserDBTest:
    def __init__(self):
        create_db()
        self.db = UserDBManager("user.db")
        self.db.nuke_db()

    def test_insert(self):
        username_1 = "chud"
        role_1 = 0
        password_1 = "chopped_1"

        username_2 = "chad"
        role_2 = 1
        password_2 = "mogging-2026"

        self.db.insert_user(username_1, role_1, password_1)
        self.db.insert_user(username_2, role_2, password_2)

    def test_get(self):
        chud = self.db.get_user("chud")
        chad = self.db.get_user("chad")

        assert chud[0] == "chud"
        assert chud[1] == 0

        assert chad[0] == "chad"
        assert chad[1] == 1

    def test_check_login(self):
        assert self.db.is_valid_login("chud", "chopped_1") == True
        assert self.db.is_valid_login("chad", "chopped_1") == False

    def test_change_username(self):
        self.db.change_username("chud", "nothingeverhappens")

        chud = self.db.get_user("chud")
        neh = self.db.get_user("nothingeverhappens")

        assert chud == None
        assert neh != None

    def test_change_password(self):
        old_chad = self.db.get_user("chad")
        self.db.change_password("chad", "based")
        new_chad = self.db.get_user("chad")
        
        assert old_chad[2] != new_chad[2]
        assert old_chad[3] != new_chad[3]

    def test_change_role(self):
        self.db.change_role("chad", 0)
        chad = self.db.get_user("chad")

        assert chad[1] == 0
    
    def test_delete(self):
        self.db.delete_user("chud")
        self.db.delete_user("chad")

        chud = self.db.get_user("chud")
        chad = self.db.get_user("chad")

        assert chud == None
        assert chad == None

def main():
    test = UserDBTest()

    test.test_insert()
    test.test_get()
    test.test_check_login()
    test.test_change_username()
    test.test_change_password()
    test.test_change_role()
    test.test_delete()

    print(f"passed all {NO_OF_TESTS} tests")

if __name__ == "__main__":
    main()