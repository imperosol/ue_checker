import sqlite3
from pathlib import Path
from threading import Thread
import sys
import pkg_resources
import subprocess


def __create_database():
    db_path = Path().absolute() / "users.sqlite"
    if db_path.exists():  # don't overwrite if there is already an existing database
        return
    db = sqlite3.connect(db_path)
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
    from cryptography.fernet import Fernet
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


def __get_outdated(libs):
    reqs = subprocess.check_output([sys.executable, '-m', 'pip', 'list', '--outdated'])
    outdated = {r.split()[0] for r in reqs.decode().split('\n')[2:] if len(r) > 1}
    # remove up-to-date packages
    up_to_date = libs - outdated.intersection(libs)
    for u in up_to_date:
        libs.remove(u)


def __install_missing_packages(missing):
    if missing:
        print("Following packages used by the program are missing :\n\t- " +
              "\n\t- ".join(m for m in missing))
        answer = input("Do you want to install those packages ? (y/n) ")
        if answer.lower() in ('y', 'yes', 'o', 'oui'):
            print("Install packages...")
            python = sys.executable
            subprocess.check_call([python, '-m', 'pip', 'install', *missing])
        else:
            print("Can't process further without the packages. Cancel project initialization.")
            exit(0)
    else:
        print("No missing packages")


def __update_outdated_packages(outdated):
    if outdated:
        print("Following packages should be updated :\n\t- " +
              "\n\t- ".join(o for o in outdated))
        answer = input("Do you want to update those packages ? (y/n) ")
        if answer.lower() in ('y', 'yes', 'o', 'oui'):
            print("Update packages...")
            python = sys.executable
            subprocess.check_call([python, '-m', 'pip', 'install', *outdated, '--upgrade'])
        else:
            print("Packages not updated. Beware that this may cause error in the future")
    else:
        print("All packages are up-to-date")


def __install_packages():
    required = {'discord', 'cryptography', 'bs4', 'requests', 'openpyxl'}
    installed = {pkg.key for pkg in pkg_resources.working_set}
    missing = required - installed
    outdated = required - missing
    # checking for missing packages can be a really long task, so we use a different thread
    # to make it while performing other actions.
    get_outdated_thread = Thread(target=__get_outdated, args=(outdated,))
    get_outdated_thread.start()
    __install_missing_packages(missing)
    print("Check outdated packages...")
    get_outdated_thread.join()
    __update_outdated_packages(outdated)


def __check_python_version():
    version = sys.version_info
    if version.major < 3:
        print("Dude, you're not using Python3, how can you be this stupid ?\n"
              "Just install Python 3.10 or higher and come back then.", file=sys.stderr)
        exit(0)
    if version.minor < 10:
        print("Python 3.10 or higher is required to run this program, while you are using"
              f"{version.major}.{version.minor}.{version.micro}.\n"
              "Please update your version of Python.", file=sys.stderr)
        exit(0)


if __name__ == '__main__':
    __check_python_version()
    print("Check packages...")
    __install_packages()
    print("Database creation...")
    __create_database()
    print("Confidential data file creation...")
    __create_confidential()
    print("Project initialization complete !")
    exit(0)
