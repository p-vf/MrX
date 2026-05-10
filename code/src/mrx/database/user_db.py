import sqlite3
import hashlib
import secrets

class UserDBManager:

    def __init__(self, database):
        self.conn = sqlite3.connect(database)
        self.cur = self.conn.cursor()

    def close_connection(self):
        self.conn.close()

    def gen_salt_and_pw(self, password):
        salt = secrets.token_bytes(4)

        pw_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )

        salt_hex = salt.hex()
        pw_hash_hex = pw_hash.hex()

        return salt_hex, pw_hash_hex
    
    def insert_user(self, username, role, password):

        salt_hex, pw_hash_hex = self.gen_salt_and_pw(password)

        insert = 'INSERT INTO users (username, role, salt, pw_hash) VALUES (?, ?, ?, ?)'
        data = (username, role, salt_hex, pw_hash_hex)

        try:
            self.cur.execute(insert, data)
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def get_user(self, username):
        get = "SELECT * FROM users Where username = ?"

        try:
            result = self.cur.execute(get, (username,))
            return result.fetchone()
        except  sqlite3.Error as e:
            print(e)
    
    def delete_user(self, username):
        delete = "DELETE FROM users WHERE username = ?"
        
        try:
            self.cur.execute(delete, (username,))
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def change_username(self, old, new):
        change = "UPDATE users SET username = ? WHERE username = ?"
        
        try:
            self.cur.execute(change, (new, old,))
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def change_password(self, username, new):
        change = "UPDATE users SET salt = ?, pw_hash = ? WHERE username = ?"

        salt_hex, pw_hash_hex = self.gen_salt_and_pw(new)
        
        try:
            self.cur.execute(change, (salt_hex, pw_hash_hex, username))
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def change_role(self, username, role):
        change = "UPDATE users SET role = ? WHERE username = ?"

        try:
            self.cur.execute(change, (role, username,))
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def nuke_db(self):
        nuke = "DELETE FROM users"

        try:
            self.cur.execute(nuke)
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)