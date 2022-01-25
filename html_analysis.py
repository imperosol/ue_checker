import bs4
import requests
from bs4 import BeautifulSoup


def get_ue_table_html(page: requests.Response) -> bs4.element.Tag:
    return BeautifulSoup(page.text, 'lxml').find('div', class_='show').find('table')


def get_ue_td_html(page: requests.Response = None) -> list[bs4.element.Tag]:
    return get_ue_table_html(page).findChildren('tr', recursive=False)


def get_letters(page: requests.Response) -> dict[str, list[str, str, str]]:
    content = get_ue_td_html(page)[1::2]
    dossier_dict = dict()
    for semester in content:
        name: str = semester.find('td', class_="entete-haut sem").find('span').get_text().replace(' ', '')
        results = [c.find_all('td', {"class": ""}) for c in semester.find_all('table')]  # ues names have no class
        results = [c for c in results if len(c) > 0]  # remove categories without ues
        results = [item.get_text().split() for sublist in results for item in sublist]  # flatten and clean list
        if name in dossier_dict:  # already existing semester, meaning there must have been an annulation
            dossier_dict[name] += results
        else:
            dossier_dict[name] = results
    # print('UEs tombées :\n' + "\n".join([f"- {ue[0]} : {ue[1]} ({ue[2]} crédits)" for ue in content if len(ue) > 1]))
    # print('UEs en attente : \n' + "\n".join([ue[0] for ue in content if len(ue) == 1]))
    return dossier_dict


def extract_decisions(page: requests.Response, last = False) -> dict[str, str]:
    if not last:
        content = get_ue_td_html(page)[1::2]
    else:
        content = [get_ue_td_html(page)[-2]]
    dossier_dict = dict()
    for semester in content:
        name: str = semester.find('td', class_="entete-haut sem").find('span').get_text().replace(' ', '')
        results = semester.find('td', class_="observation").find_all('div')
        results = [c.string.strip() for c in results if c.string is not None]  # remove empty div
        results = [c for c in results if c != '']  # remove empty div
        results = '\n'.join(results)
        if name in dossier_dict:  # already existing semester, meaning there must have been an annulation
            name += "(1)"
        dossier_dict[name] = results
    return dossier_dict
