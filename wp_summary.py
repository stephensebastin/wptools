#!/usr/bin/env python
"""
Query MediaWiki API for wiki-text before first heading

INPUT
    Wikipedia article title(s) (or filename)

OUTPUT
    Summary(es) as wiki-text, dict, or json

References
    https://en.wikipedia.org/wiki/Help:Summary
    https://www.mediawiki.org/wiki/API:Main_page
"""

from __future__ import print_function

__author__ = "@siznax"
__version__ = "15 Sep 2015"

import argparse
import json
import os
import re
import sys
import time
import wp_query

from collections import defaultdict

DEFAULT = 'text'
FORMATS = ['dict', 'json', 'text']


def from_api(titles, _format=DEFAULT):
    """returns Summaries from api"""
    return _output(_parse(_articles(titles)), _format)


def from_file(fname, _format=DEFAULT):
    """returns Summaries from input file"""
    with open(fname) as fh:
        return _output(_parse(json.loads(fh.read())), _format)


def _output(summaries, _format):
    """returns Summaries as text, dict, or json"""
    if _format == 'dict':
        return _summaries_to_dict(summaries)
    if _format == 'json':
        return json.dumps(summaries)
    if _format == 'text':
        return _summaries_to_text(summaries)


def _summaries_to_dict(summaries):
    """return list of dicts from list of infosummaries"""
    for i, summary in enumerate(summaries):
        _dict = defaultdict(str)
        for line in summary['wikitext'].split("\n"):
            _dict['title'] = summary['title']
            _dict['wikitext'] = summary['wikitext']
            if '=' in line:
                terms = line.split('=')
                key = terms[0].replace(' ', '').replace('|', '')
                _dict[key] = terms[1].strip()
        summaries[i] = dict(_dict)
    return summaries


def _summaries_to_text(summaries):
    """return wikitext from list of infosummaries"""
    text = ""
    for summary in summaries:
        text += "\n= %s =\n\n" % summary['title']
        text += summary['wikitext'] + "\n"
    return text


def _summary(wikitext):
    output = []
    temple = False
    braces = 0
    mark = " "
    lines = wikitext.split("\n")
    for line in lines:
        if line.startswith("="):
            break

        fence = re.search(r'^{{.*}}$', line)
        fence1 = re.search(r'^\[\[.*\]\]$', line)
        fence2 = re.search(r'^<!--.*-->$', line)

        braces += len(re.findall(r'{{', line))
        braces -= len(re.findall(r'}}', line))

        exited = False
        if braces > 0:
            temple = True
        if temple and braces == 0:
            temple = False
            exited = True

        mark = ">"
        if fence or fence1 or fence2:
            mark = "*"
        elif braces > 0:
            mark = str(braces)
        if exited:
            mark = "0"

        if mark == ">":
            output.append(line.lstrip())

        # print("[%s] %s" % (mark, line.encode('utf-8')))

    return "\n".join(output)


def _parse(api_json):
    """returns [{title, summary}, ...] from JSON"""
    summaries = []
    # print("pages: %d" % len(api_json["query"]['pages']), file=sys.stderr)
    try:
        for page in api_json["query"]["pages"]:
            wikitext = page["revisions"][0]["content"]
            summary = _summary(wikitext)
            if summary:
                summaries.append({'title': page["title"],
                                  'wikitext': summary})
    except:
        print(page)
        raise RuntimeError("Unable to parse result! Check your API query.")
    return summaries


def _articles(titles):
    """returns JSON object from list of titles"""
    if isinstance(titles, str):
        titles = [titles]
    return json.loads(wp_query.data("|".join(titles)))


def _main(titles, _format):
    """emits Summaries from api or local file"""
    if os.path.exists(titles[0]):
        return from_file(titles[0], _format)
    else:
        return from_api(titles, _format)


if __name__ == "__main__":
    argp = argparse.ArgumentParser(
        description="Wikipedia article summaries given titles, format")
    argp.add_argument("titles", nargs='+',
                      help="article titles (optionally, local filename)")
    argp.add_argument("-format", choices={'text', 'json'}, default='text',
                      help="output format (default=text)")
    args = argp.parse_args()

    start = time.time()
    print(_main(args.titles, args.format).encode('utf-8'))
    print("%5.3f seconds" % (time.time() - start), file=sys.stderr)
