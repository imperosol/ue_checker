import sqlite3
from src.users import DB_PATH
from pathlib import Path
from cryptography.fernet import Fernet
import sys
import pkg_resources
import subprocess


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
    confidential_path = Path().absolute() / 'src' / "confidential.py"
    if confidential_path.exists():
        return
    with open(confidential_path, "w") as f:
        f.write("""
# Write the token of your bot. You must create a discord application and generate the token
# Follow this link to create a discord application : https://discord.com/developers/applications/
BOT_TOKEN = ''\n
""")
        f.write(f"FERNET_KEY = {Fernet.generate_key()}")


def __install_packages():
    required = {'mutagen', 'gTTS'}
    installed = {pkg.key for pkg in pkg_resources.working_set}
    missing = required - installed
    if missing:
        print("Following packages used by the program are missing :\n\t- " +
              "\n\t- ".join(m for m in missing))
        answer = input("Do you want to install those packages ? (y/n)")
        if answer in ('y', 'yes', 'o', 'oui'):
            python = sys.executable
            subprocess.check_call([python, '-m', 'pip', 'install', *missing], stdout=subprocess.DEVNULL)
        else:
            print("Can't process further without the packages. Cancel project initialization.")
            exit(0)
    else:
        print("No missing packages")


if __name__ == '__main__':
    print("Check packages...")
    __install_packages()
    print("Database creation...")
    __create_database()
    print("Confidential data file creation...")
    __create_confidential()
