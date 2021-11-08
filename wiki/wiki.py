# %%

from typing import Sequence
from warnings import warn

import requests as r

"""
Two step solution to get wikipedia page id from wikidata entity id (from maxlath answer to https://stackoverflow.com/questions/43746798/how-to-get-wikipedia-pageid-from-wikidata-id):
1) find wikipedia page title (in any language) using wikidata API: `
https://www.wikidata.org/w/api.php?format=json&action=wbgetentities&ids=Q78|Q3044&props=aliases|sitelinks&languages=en
`
2) find wikipedia pageid from page title: `
https://en.wikipedia.org/w/api.php?action=query&titles=Fribourg&format=json
"""

# %%

wikipedia_page_titles_by_lng_and_wikidata_ids = dict()

# %%

def _get_wikipedia_page_titles_from_wikidata_ids_max50(wikidata_ids:Sequence[str], languages:Sequence[str]=None):
    """Returns wikipedia page titles from wikidata ids, max 50 items at a time

    languages should be an array of two-letter abbreviations for desired languages
    
    note: this function returns an accumulator that accumulates endlessly over a program run.
    always iterate over your own wikidata_ids, not this function result. consider further optimization if long runs.
    """
    wikidata_ids = list(i for i in wikidata_ids if i !="null")
    if len(wikidata_ids)>50:
        raise(Exception(f"wiki._get_wikipedia_page_titles_from_wikidata_ids_max50() more than 50 wikidata_ids given:\n{wikidata_ids}"))

    for lng in languages:
        if lng not in wikipedia_page_titles_by_lng_and_wikidata_ids:
            wikipedia_page_titles_by_lng_and_wikidata_ids[lng]=dict()

    already_covered_ids = set(
        wd_id for wd_id in wikidata_ids
        if all(wd_id in wikipedia_page_titles_by_lng_and_wikidata_ids[lng] for lng in languages)
    )
    ids_to_query = [wd_id for wd_id in wikidata_ids if wd_id not in already_covered_ids]

    if len(ids_to_query)>0:
        url = "https://www.wikidata.org/w/api.php"
        params = {
            "format":  "json",
            "action":  "wbgetentities",
            "ids":  "|".join(ids_to_query),
            "props":  "sitelinks"
        }


        resp = r.get(url=url, params=params)
        data = resp.json()
        #print(f"\n-----\nwiki._get_wikipedia_page_titles_from_wikidata_ids_max50(ids, {languages})\n ids_to_query:\n{ids_to_query}\ndata:\n{data}\n-----\n")
        entities = data["entities"]
        for lng in languages:
            for wd_id in ids_to_query:
                if (lng+"wiki") in entities[wd_id]["sitelinks"]:
                    wikipedia_page_titles_by_lng_and_wikidata_ids[lng][wd_id] = entities[wd_id]["sitelinks"][lng+"wiki"]["title"] 
                else:
                    wikipedia_page_titles_by_lng_and_wikidata_ids[lng][wd_id] = None
        # wikipedia_titles_by_language = {
        #     lng: {
        #         # only consider wikidata id with a wikipedia page in given language
        #         wd_id: entities[wd_id]["sitelinks"][lng+"wiki"]["title"] if (lng+"wiki") in entities[wd_id]["sitelinks"] else None
        #         for wd_id in wikidata_ids
        #     }
        #     for lng in languages
        # }
    return wikipedia_page_titles_by_lng_and_wikidata_ids

# %%

def get_wikipedia_page_titles_from_wikidata_ids(wikidata_ids:Sequence[str], languages:Sequence[str]=None):
    """Returns wikipedia page titles from wikidata ids

    languages should be an array of two-letter abbreviations for desired languages

    note: this function returns an accumulator that accumulates endlessly over a program run.
    always iterate over your own wikidata_ids, not this function result. consider further optimization if long runs.
    """
    rest = list(wikidata_ids)
    while len(rest)>0:
        current = rest[:50]
        rest = rest[50:]
        _get_wikipedia_page_titles_from_wikidata_ids_max50(current, languages)
    return wikipedia_page_titles_by_lng_and_wikidata_ids

# %%

wikipedia_page_ids_by_lng_and_title = dict()

# %%


def _get_wikipedia_pages_ids_from_titles_max50(wikipedia_titles:Sequence[str], language:str):
    """Returns wikipedia page ids from their title, max 50 items at a time
    
    language should be the two-letter abbreviation for desired language"""
    # get_wikipedia_pages_ids_from_titles(wikipedia_titles:str, language:str):
    wikipedia_titles = [t for t in wikipedia_titles if t is not None]
    if len(wikipedia_titles)>50:
        raise(Exception(f"wiki._get_wikipedia_pages_ids_from_titles_max50() more than 50 wikipedia_titles given:\n{wikipedia_titles}"))

    if language not in wikipedia_page_ids_by_lng_and_title:
        wikipedia_page_ids_by_lng_and_title[language]=dict()

    already_covered_titles = set(
        t for t in wikipedia_titles
        if t in wikipedia_page_ids_by_lng_and_title[language]
    )
    titles_to_query = [t for t in wikipedia_titles if t not in already_covered_titles]

    if len(titles_to_query)>0:
        url = f"https://{language}.wikipedia.org/w/api.php"
        params = {
            "action":  "query",
            "titles":  "|".join(titles_to_query),
            "format":  "json"
        }
        resp = r.get(url=url, params=params)
        data = resp.json()
        
        #print(f"\n-----\nwiki.get_wikipedia_pages_ids_from_titles(titles, {language})\ntitles_to_query:\n{titles_to_query}\ndata:\n{data}\n-----\n")
    
        pages = data["query"]["pages"]
        if "-1" in pages:
            warn(f"get_wikipedia_pages_ids_from_titles(): missing page for wikipedia page: {pages['-1']}")
            del pages["-1"]

        for pageid,page_info in pages.items():
            wikipedia_page_ids_by_lng_and_title[language][page_info["title"]] = pageid
    return wikipedia_page_ids_by_lng_and_title[language]

# %%

def get_wikipedia_pages_ids_from_titles(wikipedia_titles:Sequence[str], language:str):
    """Returns wikipedia page ids from their title, max 50 items at a time
    
    language should be the two-letter abbreviation for desired language"""
    rest = list(wikipedia_titles)
    while len(rest)>0:
        current = rest[:50]
        rest = rest[50:]
        _get_wikipedia_pages_ids_from_titles_max50(current, language)
    return wikipedia_page_ids_by_lng_and_title[language]
# %%


def get_wikipedia_page_titles_and_ids_from_wikidata_ids(wikidata_ids:str, languages:str):
    """Returns wikipedia page titles and ids from wikidata ids, max 50 items at a time
    
    languages should be a list of two-letter abbreviations for desired languages
    returns dict of the form:
    ```
    {
        <language>: {
            <wikidata_id>: (<wikipedia_page_title>, <wikipedia_page_id>),
            ...
            }
        ...
    }
    ```
    <wikipedia_page_title> or <wikipedia_page_id> are None if not found on wikipedia api
    """
    wikipedia_titles_by_language = get_wikipedia_page_titles_from_wikidata_ids(wikidata_ids, languages)
    wikipedia_ids_by_language_and_title = {
        lng: get_wikipedia_pages_ids_from_titles(titles.values(), lng)
        for lng, titles in wikipedia_titles_by_language.items()
    }
    print(f"get_wikipedia_page_titles_and_ids_from_wikidata_ids() wikipedia_ids_by_language_and_title: {wikipedia_ids_by_language_and_title}")
    wikipedia_ids_by_language_and_wikidata_id = {
        lng: {
            wd_id: (wp_title, wikipedia_ids_by_language_and_title[lng][wp_title])
            for wd_id, wp_title in wikipedia_titles.items()
            if wp_title in wikipedia_ids_by_language_and_title[lng]
        }
        for lng, wikipedia_titles in wikipedia_titles_by_language.items()
    }
    return wikipedia_ids_by_language_and_wikidata_id

# %%

if __name__=="__main__":

    wikidata_ids = ["Q12771","Q3102325","Q78", "Q3044" ]
    languages=["fr", "de", "en"]

    wikipedia_titles_by_language = get_wikipedia_page_titles_from_wikidata_ids(wikidata_ids, languages)



    # %%

    language="de"
    wikipedia_titles = wikipedia_titles_by_language[language]

    # %%

    page_titles_ids = get_wikipedia_page_titles_and_ids_from_wikidata_ids(wikidata_ids, languages)
    # %%
