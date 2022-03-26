#!/usr/bin/env python3
"""
Multi_search is a command-line web search aggregator in Python,
derived from the Search-Engine-Scraper package from
https://github.com/tasos-py/Search-Engines-Scraper.

Non-redundant aggregate results from privacy-oriented search engines
are returned as URLs and their page titles to Terminal output and
an auto-named text file. User agents for requests are randomized.

The intent is to provide easy comparisons among search engines, avoid
unintended search filtering, and automatically store results to file.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see https://www.gnu.org/licenses/.

See LICENCE file for additional licenses of repository components.
"""
__author__ = 'Craig Echt'
__copyright__ = 'Copyright (C) 2022 C.S. Echt'
__license__ = 'GNU General Public License'
__program_name__ = 'multi_search.py'
__project_url__ = 'https://github.com/csecht/Search-Engines-Scraper'
__version__ = '0.3.8'
__credits__ = 'Tasos M Adamopoulos (tasos-py) and Mario Vilas'
__dev_environment__ = 'Python 3.8'
__status__ = 'Development Status :: 1 - Alpha'


import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import search_engines as se
from multi_search_utils import files, get_user_agent as ua

FileIt = files.results2file

# Assign user agent to engines here.
# Bots are generally banned by SP; tua may be blocked by Moj.
dgg_UA = ua.rando_function(('bua', 'fua', 'tua', 'eua'))
sp_UA = ua.rando_function(('fua', 'wua'))
moj_UA = ua.rando_function(('bua', 'fua', 'eua', 'rua', 'rua'))
mg_UA = ua.rando_function(('bua', 'fua', 'pua', 'tua', 'eua', 'rua'))

# The duplicated result closest to end of the results list is the one
#   retained in the unique_results list, so engine order here matters
#   for engine-specific reporting of unique results metrics.
# Use only engines committed to privacy.
engines = {
    'DDG': se.Duckduckgo(dgg_UA),
    'Moj': se.Mojeek(moj_UA),
    'SP': se.Startpage(sp_UA),
    'MG': se.Metager(mg_UA),
    }

engine_names = {
    'DDG': 'DuckDuckGo',
    'Moj': 'Mojeek',
    'SP': 'Startpage',
    'MG': 'MetaGer'
    }


def parse_args() -> None:
    """Allow handling of common command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--about',
                        help='Provides description, version, GNU license.',
                        action='store_true',
                        default=False)
    parser.add_argument('--use',
                        help='Program execution and search term examples.',
                        action='store_true',
                        default=False)

    args = parser.parse_args()
    # args, unknown = parser.parse_known_args()  # Bypass arg errors.
    if args.about:
        print(__doc__)
        print(f'{"Author:".ljust(13)}', __author__)
        print(f'{"License:".ljust(13)}', __license__)
        print(f'{"Copyright:".ljust(13)}', __copyright__)
        print(f'{"Program:".ljust(13)}', __program_name__)
        print(f'{"url:".ljust(13)}', __project_url__)
        print(f'{"Version:".ljust(13)}', __version__)
        print(f'{"Credits:".ljust(13)}', __credits__)
        print(f'{"Dev Env:".ljust(13)}', __dev_environment__)
        print(f'{"Status:".ljust(13)}', __status__)
        print()
        sys.exit(0)

    if args.use:
        print(f'USAGE: Run {__file__} without arguments,'
              ' then enter your search term at the prompt.\n')
        try:
            syntax = Path('multi_search_utils', 'use_syntax.txt').read_text(encoding='utf-8')
            print(syntax)
        except FileNotFoundError:
            print('Sorry, but the use_syntax.txt file is not in the multi_search_utils folder.')
        sys.exit(0)


def search_this(search_term: str) -> None:
    """
    Run the input search term through engines specified in Dict(engines).
    Print and write non-redundant results of urls and page titles.

    :param search_term: String with valid syntax on all or most engines.
    """

    combined_results = []
    for e_key, _engine in engines.items():
        # Limit each engine to ~20 max results.
        # MG returns 20-50 results/page depending on UA; DDG ~36.
        if e_key in 'DDG, MG':
            results = _engine.search(search_term, pages=1)
            links = results.links()[0:20]
            titles = results.titles()[0:20]
        else:
            # Mojeek and Startpage return 10 results/page.
            results = _engine.search(search_term, pages=2)
            links = results.links()
            titles = results.titles()

        # Prepend the engine tag to each result title.
        for i, _title in enumerate(titles):
            titles[i] = f'({e_key}) {_title}'

        # Pack the link and its title into a list of tuples.
        e_result = list(zip(links, titles))
        combined_results.extend(e_result)

        e_count_msg = f'Keeping the first {len(links)} results from {engine_names[e_key]} ({e_key})'
        print(e_count_msg)
        FileIt(search_term, f'{e_count_msg}\n')

    # Filter unique urls, saving the last redundant hit from combined_results,
    #   where last is determined by the engines (dict) items' order.
    unique_results = list({tup[:1]: tup for tup in combined_results}.values())

    result_summary = (f'Found {len(combined_results)} total results.\n\n'
                      f'There are {len(unique_results)} unique results.')
    print(result_summary)
    FileIt(search_term, f'{result_summary}\n')

    # Report number of unique hits retained from each engine.
    for tag in engine_names:
        tag = f'({tag})'
        num_uniq_hit = len([hit for hit in unique_results if tag in hit[1]])
        tag_msg = f'{num_uniq_hit} unique results retained from {tag}'
        print(tag_msg)
        FileIt(search_term, f'{tag_msg}\n')

    # Need a brief delay before Terminal scrolls to last line of results
    #   so user can glimpse the last engine's, and final, unique count.
    time.sleep(2)

    # Finally, report url and page title from each hit in results list.
    for _r in unique_results:
        result_msg = f'\n{_r[0]}\n{_r[1]}'
        print(result_msg)
        FileIt(search_term, f'{result_msg}\n')

    print(f'\nResults were written or appended to {FileIt(search_term, "")}')
    print(f'=============== END of {len(unique_results)} results ==================')
    FileIt(search_term,
           f'\n{"=" * 26} END of {len(unique_results)} results {"=" * 26}\n')


def main() -> None:
    """
    Print parameters and header information to Terminal and file.
    Run the search if no arguments are given.
    """
    parse_args()
    term = input("\nEnter search term: ")

    # Remove spaces in term for better file naming; '+' doesn't affect search.
    term = term.replace(' ', '+')

    user_agents_used = (
        '\nUser agent for each engine of this search:\n'
        f'{"DuckDuckGo:".ljust(11)}{dgg_UA}\n'
        f'{"Mojeek:".ljust(11)}{moj_UA}\n'
        f'{"Startpage:".ljust(11)}{sp_UA}\n'
        f'{"MetaGer:".ljust(11)}{mg_UA}\n')
    print(user_agents_used)

    file_header = (
        f'SEARCH TERM: {term}    TIME: {datetime.now().strftime("%x %X")}')
    FileIt(term, f'{file_header}\n\n')
    FileIt(term, f'{user_agents_used}\n')

    search_this(term)


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        # Note: Ctrl-c may not work with PyCharm Terminal interpreter when
        #   waiting for Terminal input; Ctrl-d does work.
        print(' *** Keyboard interrupt: User has quit the program ***\n')
        sys.exit()
