import requests
from bs4 import BeautifulSoup

STUDENT_FILE_URL = 'https://ent2.utt.fr/uPortal/ExternalURLStats?fname=suivi-etudiants&service=https:' \
                   '//cocktail-wo.utt.fr/cgi-bin/WebObjects/Dossier-Etudiants.woa/1/wa/casLogin'

payload = {
    '_eventId': 'submit',
    'submit': 'LOGIN',
}


def set_cipher():
    requests.packages.urllib3.disable_warnings()
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
    try:
        requests.packages.urllib3.contrib.pyopenssl.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
    except AttributeError:
        # no pyopenssl support used / needed / available
        pass


def __cas_login(session: requests.Session) -> None:
    url = 'https://cas.utt.fr/cas/login?service=https://ent2.utt.fr/uPortal/Login'
    page = session.get(url, data=payload)
    soup = BeautifulSoup(page.text, 'lxml')
    payload['lt'] = soup.find('input', {'name': 'lt'}).get('value')
    cookies = page.cookies
    session.post(url, data=payload, params=cookies, verify=False)
    session.params = cookies


def init_session(session: requests.Session, username: str, password: str) -> None:
    payload['username'] = username
    payload['password'] = password
    session.auth = (username, password)
    session.verify = False
    session.data = payload
    __cas_login(session)


def get_student_file(session: requests.Session):
    return session.get(STUDENT_FILE_URL)

