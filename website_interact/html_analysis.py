from typing import Tuple, List, Any

import bs4
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

ue_set = dict[str, dict[str, list[str, str, str]]]
response = requests.Response


def get_ue_table_html(page: response) -> bs4.element.Tag:
    return BeautifulSoup(page.text, 'lxml').find('div', class_='show').find('table')


def get_ue_td_html(page: response = None) -> list[bs4.element.Tag]:
    return get_ue_table_html(page).findChildren('tr', recursive=False)


def __prepare_extraction(page, semesters) -> tuple[list[str], list[Tag]]:
    content = get_ue_td_html(page)
    categories = content[0].find_all('th', class_='entete-haut ent-categ')
    categories = [c.string for c in categories]
    ues = content[1::2]
    if not semesters:
        ues = [ues[-1]]
    return categories, ues


def extract_letters_category(page: response, semesters_list: list[str], categories_list: list[str]) -> ue_set:
    categories, ues = __prepare_extraction(page, semesters_list)
    dossier_dict = dict()
    for category in categories_list:
        cat_index = categories.index(category)
        dossier_dict[category] = dict()
        for semester in ues:
            semester_name = semester.find('td', class_="entete-haut sem").find('span').get_text().replace(' ', '')
            if semesters_list and semester_name not in semesters_list:
                continue
            # select ues which are in the column of the current category
            results = [c.find_all('td', {"class": ""}) for c in semester.find_all('table')][cat_index]
            results = [item.get_text().split() for item in results]
            if semester_name not in dossier_dict[category]:
                dossier_dict[category][semester_name] = results
            else:
                dossier_dict[category][semester_name] += results
    return dossier_dict


def extract_letters_semester(page: requests.Response, semesters_list, categories_list) -> ue_set:
    """
    extract from the page a dict with all UEs.
    The keys are the semesters and each element is a dict associating UEs to their category
    For example this can return: ::
        {'TC1': {
            'CS': 'MATH01',
            'TM': 'TNEV'},
        'TC2': {
            'CS': 'MATH02',
            'TM': 'EN01'}
        }
    """
    categories, ues = __prepare_extraction(page, semesters_list)
    dossier_dict = dict()
    for semester in ues:
        name: str = semester.find('td', class_="entete-haut sem").find('span').get_text().strip().replace(' ', '')
        if semesters_list is not None and name not in semesters_list:
            continue
        results = [c.find_all('td', {"class": ""}) for c in semester.find_all('table')]  # ues names have no class
        results = [[item.get_text().split() for item in sublist] for sublist in results]  # flatten and clean list
        semester_dict = dict()
        for category, ue in zip(categories, results):
            if not categories_list or category in categories_list:
                semester_dict[category] = ue
        if name in dossier_dict:  # already existing semester, meaning there must have been an annulation
            for category in dossier_dict[name]:
                dossier_dict[name][category] += semester_dict[category]
        else:
            dossier_dict[name] = semester_dict
    return dossier_dict


def extract_decisions(page: requests.Response, index: int = None) -> dict[str, str]:
    if index is None:
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
