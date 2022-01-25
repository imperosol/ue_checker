from confidential import *
import requests
from bs4 import BeautifulSoup

STUDENT_FILE_URL = 'https://ent2.utt.fr/uPortal/ExternalURLStats?fname=suivi-etudiants&service=https:' \
                   '//cocktail-wo.utt.fr/cgi-bin/WebObjects/Dossier-Etudiants.woa/1/wa/casLogin'

payload = {
    '_eventId': 'submit',
    'submit': 'LOGIN',
    'username': USERNAME,
    'password': PASSWORD,
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
    page = session.get('https://cas.utt.fr/cas/login?service=https://ent2.utt.fr/uPortal/Login', data=payload)
    soup = BeautifulSoup(page.text, 'lxml')
    payload['lt'] = soup.find('input', {'name': 'lt'}).get('value')
    cookies = page.cookies
    url = 'https://cas.utt.fr/cas/login?service=https://ent2.utt.fr/uPortal/Login'
    session.post(url, data=payload, params=cookies, verify=False)
    session.params = cookies
    print('connected')


async def init_session(session: requests.Session, username: str = None, password: str = None) -> None:
    if username is not None:
        payload['username'] = username
    if password is not None:
        payload['password'] = password
    session.auth = (payload['username'], payload['password'])
    session.verify = False
    session.data = payload
    __cas_login(session)


def ent_ddos(session: requests.Session):
    url = 'https://ent2.utt.fr/uPortal/ExternalURLStats?fname=suivi-etudiants&service=https://cocktail-wo.utt.fr/cgi' \
          '-bin/WebObjects/Dossier-Etudiants.woa/1/wa/casLogin'
    while True:
        try:
            page = session.get(url, verify=False, data=payload)
            print(f'{page.status_code} {page.reason}')
        except:
            print('error')
            pass


def get_student_file(session: requests.Session):
    return session.get(STUDENT_FILE_URL)
