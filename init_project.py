import sqlite3
from users import DB_PATH
from pathlib import Path
from cryptography.fernet import Fernet


def __create_database():
    if DB_PATH.exists():
        return
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    query = """create table users (
        discordId   integer
            constraint users_pk
                primary key,
        entUsername text not null,
        entPassword text not null
    );
    create unique index users_entPassword_uindex on users(entPassword);
    create unique index users_entUsername_uindex on users(entUsername);"""
    cur.executescript(query)
    db.commit()
    cur.close()
    db.close()


def __create_confidential():
    confidential_path = Path().absolute() / "confidential.py"
    if confidential_path.exists():
        return
    with open(confidential_path, "w") as f:
        f.write("""
# Write the token of your bot. You must create a discord application and generate the token
# Follow this link to create a discord application : https://discord.com/developers/applications/
BOT_TOKEN = ''\n
""")
        f.write(f"FERNET_KEY = {Fernet.generate_key()}")


if __name__ == '__main__':
    __create_database()
    __create_confidential()
