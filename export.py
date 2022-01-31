import openpyxl.styles.fonts
from openpyxl import Workbook
from custom_types import ue_set
import json


def __get_max_sub_elem(content: ue_set) -> dict[str, int]:
    """
    take in argument a nested dictionary
    and return a dictionary which associates each key of inner
    dictionary with the max number of elements in field.
    Example : ::
        {
            'TC1': {'CS': [1, 1], 'TM': [1],       'ME': [1]},
            'TC2': {'CS': [1, 1], 'TM': [1, 1, 1], 'ME': [1, 1]}
        }

    as an input will make the function
    return : ::
            {'CS': 2, 'TM': 3, 'ME': 2}
    """
    max_sizes = dict()
    for elem in content.values():
        for sub_title, sub_elem in elem.items():
            nb_rows = len(sub_elem)
            if sub_title in max_sizes:
                max_sizes[sub_title] = max(max_sizes[sub_title], nb_rows)
            else:
                max_sizes[sub_title] = nb_rows
    return max_sizes


def to_xls(content: ue_set) -> str:
    """ Function to create an Excel file with the datas of the student file.
    :return: the name of the file created
    :rtype: str
    """
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "ues"
    font = openpyxl.styles.Font(bold=True)
    align = openpyxl.styles.Alignment(horizontal='center', vertical='center')
    row_per_category = __get_max_sub_elem(content)
    col = 2
    for title, elem in content.items():
        worksheet.merge_cells(start_row=1, start_column=col, end_row=1, end_column=col + 2)
        worksheet.cell(1, col).value = title
        worksheet.cell(1, col).font = font
        worksheet.cell(1, col).alignment = align
        row = 2
        for sub_title, sub_elem in elem.items():
            size = 0
            add_row = row_per_category[sub_title]
            if add_row > 0:
                worksheet.merge_cells(start_row=row, start_column=1, end_row=row + add_row - 1, end_column=1)
            worksheet.cell(row, 1).value = sub_title
            worksheet.cell(row, 1).alignment = align
            if len(sub_elem) > 0:
                for ue in sub_elem:
                    if len(ue) == 0:
                        continue
                    for i, ue_info in enumerate(ue):
                        if ue_info.isdigit():
                            ue_info = int(ue_info)
                        worksheet.cell(row + size, col + i).value = ue_info
                    size += 1
            row += add_row
        col += 3
    workbook.save('ues.xlsx')
    return 'ues.xlsx'


def to_json(ues: ue_set) -> str:
    """ Function to create a json file with the datas of the student file.
    :return: the name of the file created
    :rtype: str
    """
    with open('ues.json', "w", encoding='utf-8') as f:
        json.dump(ues, f, ensure_ascii=False, indent=2)
    return 'ues.json'
