import sqlite3
from cryptography.fernet import Fernet
from confidential import FERNET_KEY
from website_interact.ent_requests import init_session
from pathlib import Path

DB_PATH = Path().absolute() / "users.sqlite"


class OverwriteError(Exception): pass


class UserNotFoundError(Exception): pass


class User:
    def __init__(self, discord_id: int, username: str = "", password: str = ""):
        self.__username = username
        self.__password = password
        self.discord_id = discord_id

    def save(self):
        if self.__username == "" or self.__password == "":
            raise ValueError()
        db = sqlite3.connect(DB_PATH)
        cur = db.cursor()
        f = Fernet(FERNET_KEY)
        encoded_pass = f.encrypt(self.__password.encode('utf-8'))
        try:
            cur.execute(
                "INSERT INTO users VALUES (?, ?, ?)",
                (self.discord_id, self.__username, encoded_pass)
            )
        except sqlite3.IntegrityError:
            raise OverwriteError()
        finally:
            cur.close()
            db.commit()
            db.close()

    def remove(self):
        db = sqlite3.connect(DB_PATH)
        cur = db.cursor()
        result = cur.execute("DELETE FROM users WHERE discordId=?", (self.discord_id,))
        cur.close()
        db.commit()
        db.close()
        if result.rowcount == 0:
            raise UserNotFoundError()

    def __find_user_in_db(self):
        db = sqlite3.connect(DB_PATH)
        cur = db.cursor()
        f = Fernet(FERNET_KEY)
        result = cur.execute(
            "SELECT entUsername, entPassword FROM users WHERE discordId=?",
            (self.discord_id,)
        ).fetchone()
        if result is None:
            raise UserNotFoundError
        self.__username = result[0]
        self.__password = f.decrypt(result[1]).decode('utf-8')
        print(self.__password)
        cur.close()
        db.close()

    def init_session(self, session):
        if self.__username == "" or self.__password == "":
            try:
                self.__find_user_in_db()
            except UserNotFoundError:
                raise UserNotFoundError()
        init_session(session, self.__username, self.__password)
