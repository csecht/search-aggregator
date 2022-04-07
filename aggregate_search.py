#!/usr/bin/env python3
"""
aggregate_search.py is a command-line web search aggregator written in
Python3. It is derived from the Search-Engines-Scraper repository at
https://github.com/tasos-py/Search-Engines-Scraper.

Non-redundant aggregated results from privacy-focused search engines
are returned as URLs, page titles, and page descriptions printed to the
Terminal and to an auto-named text file.

The intent is to provide broad searches and easy comparisons among
search engines, while minimizing or avoiding search silos. User agents
for HTTP requests are randomized for each engine within optimized sets.

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

import argparse
import time
from datetime import datetime
from pathlib import Path
from sys import exit as sys_exit

from aggregate_utils import about, agents, files, reporting, config as cfg
from search_engines import engines as se

FileIt = files.results2file
ReportIt = reporting.report_results


def search_this(search_term: str) -> None:
    """
    Run the input search term through engines specified in dict(engine).
    Report to Terminal and to file non-redundant results of urls and
    page titles and page text details.

    :param search_term: String with valid syntax for all or most engines.
    """

    # Any duplicated url closest to the end of the combined_results list
    #   will be retained in the unique_results list, so engines item
    #   order matters for the number of unique results from each engine.
    # For sensible reporting, item order should match among
    #   dict(agents), config.ENGINE_NAMES, and dict(engines)
    engines = {
        '(DDG)': se.Duckduckgo(agents['(DDG)']),
        '(MG)': se.Metager(agents['(MG)']),
        '(SP)': se.Startpage(agents['(SP)']),
        '(Moj)': se.Mojeek(agents['(Moj)']),
    }
    combined_results = []

    # From each engine, balance the number of initial results so numbers
    #   of unique results retained are more even among engines.
    for tag, engine in engines.items():
        # Depending on UA, DGG returns ~20-60 results/page, MG ~20-40.
        if tag in '(DDG), (MG)':
            results = engine.search(search_term, pages=1)
            links = results.links()[0:30]
            titles = results.titles()[0:30]
            details = results.text()[0:30]
        else:
            # Mojeek and Startpage return 10 results/page.
            results = engine.search(search_term, pages=2)
            links = results.links()
            titles = results.titles()
            details = results.text()

        # Prepend the engine tag to each result title.
        for i, _title in enumerate(titles):
            titles[i] = f'{tag} {_title}'

        # Pack each engine's result into a list of tuples.
        combined_results.extend(list(zip(links, titles, details)))

        e_count_msg = (f'Keeping the first {len(links)} results'
                       f' from {cfg.ENGINE_NAMES[tag]}')
        ReportIt(search_term, e_count_msg)

    # Filter unique urls, saving the last redundant hit from combined_results,
    #   where last is determined by the order of items in {engines}.
    # Note: in combined_results and unique_results, res[0] is the url,
    #   res[1] is the page title, res[2] is the detailed description.
    unique_results = tuple({res[0]: res for res in combined_results}.values())

    result_summary = (f'Kept {len(combined_results)} total results.\n\n'
                      f'There are {len(unique_results)} unique results.')
    ReportIt(search_term, result_summary)

    # Report number of unique results retained from each engine.
    for tag, engine in cfg.ENGINE_NAMES.items():
        num_uniq = sum(tag in res[1] for res in unique_results)
        uniq_msg = f'{num_uniq} unique results retained from {engine} {tag}'
        ReportIt(search_term, uniq_msg)

    # Need a brief delay before Terminal scrolls to last line of results
    #   so user can glimpse the last engine's, and final, unique count.
    time.sleep(2)

    # Finally, report url, page title, and page detail from each result.
    for (_u, _t, _d) in unique_results:
        url = f'\n{cfg.BLUE}{_u}'
        title = f'\n{cfg.YELLOW}{_t}{cfg.NC}'
        detail = f'\n{_d}'
        ReportIt(search_term, url+title+detail)

    print(f'\nResults were written or appended to {FileIt(search_term, "")}')
    ending_msg = f'\n{"=" * 26} END of {len(unique_results)} results {"=" * 26}\n'
    ReportIt(search_term, ending_msg)


def parse_args(assist: str = None) -> None:
    """Allow handling of common command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--about',
                        help='Provides description, version, GNU license.',
                        action='store_true',
                        default=False)
    parser.add_argument('--use',
                        help='Usage, search term syntax examples.',
                        action='store_true',
                        default=False)

    args = parser.parse_args()
    if args.about:
        print(__doc__)
        print(f'{"Author:".ljust(10)}', about.data('author'))
        print(f'{"License:".ljust(10)}', about.data('license'))
        print(f'{"Copyright:".ljust(10)}', about.data('copyright'))
        print(f'{"Program:".ljust(10)}', about.data('program_name'))
        print(f'{"URL:".ljust(10)}', about.data('project_url'))
        print(f'{"Version:".ljust(10)}', about.data('version'))
        print(f'{"Dev Env:".ljust(10)}', about.data('dev_environment'))
        print(f'{"Status:".ljust(10)}', about.data('status'))
        print()
        sys_exit(0)

    if args.use or str(assist) in '-help, --help':
        print(f'USAGE: Run {__file__} without arguments,'
              ' then enter your search term at the prompt.\n')
        _use = Path('aggregate_utils/use_syntax.txt').resolve()
        try:
            syntax = Path(_use).read_text(encoding='utf-8')
            print(syntax)
        except FileNotFoundError:
            print(f'Sorry, but could not find file: {_use}')
        sys_exit(0)


def main() -> None:
    """
    Obtain input search term.
    Print user agents and header information to Terminal and file.
    Run searches if no arguments are given.
    """

    parse_args()

    term = input("\nEnter search term: ").lstrip()
    print()

    # In the unlikely event user seeks assistance at input prompt...
    if term in '-help, --help, -h':
        parse_args(term)

    # Remove spaces in term for better file naming; '+' doesn't affect search.
    term = term.replace(' ', '+')

    file_header = (
        f'SEARCH TERM: {term}    TIME: {datetime.now().strftime("%x %X")}')
    FileIt(term, f'{file_header}\n\n')

    reporting.report_agents(term)

    search_this(term)


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print(' *** Keyboard interrupt: User has quit the program ***\n')
        sys_exit()
