#!/usr/bin/env python3
"""

"""

from pathlib import Path


def results2file(search_txt: str, data: str) -> str:
    """
    Write a text file of search results.

    :param search_txt: The search string to use in the file name.
    :param data: The URL or info strings to save to file.
    :return: Name of file created/appended.
    """

    filename = f'Results_{search_txt}.txt'
    filepath = Path(filename)
    with open(filepath, 'a', encoding='utf-8') as hits:
        hits.write(data)

    return filename


def remove_file(search_txt: str) -> None:

    Path(results2file(search_txt, '')).unlink()