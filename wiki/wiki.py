# %%

from typing import Sequence
from warnings import warn

import pandas as pd
import requests as r

"""
Two step solution to get wikipedia page id from wikidata entity id (from maxlath answer to https://stackoverflow.com/questions/43746798/how-to-get-wikipedia-pageid-from-wikidata-id):
1) find wikipedia page title (in any language) using wikidata API: `
https://www.wikidata.org/w/api.php?format=json&action=wbgetentities&ids=Q78|Q3044&props=aliases|sitelinks&languages=en
`
2) find wikipedia pageid from page title: `
https://en.wikipedia.org/w/api.php?action=query&titles=Fribourg&format=json
"""

"""

Change proposition
- using pandas:
    1 dtf for lng, wikidata_id, wikipedia_title
    1 dtf for lng, wikidata_id, wikipedia_title, wikipedia_id
- writing to csv at end of each exec
"""

# %%

DTF_LANG_WDID_WPTITLE_COLUMNS=["language", "wikidata_id", "wikipedia_title"]
DTF_LANG_WDID_WPTITLE = pd.DataFrame(columns=DTF_LANG_WDID_WPTITLE_COLUMNS,
    data=[("fr","Q12771", None),("de", "Q12771","ha")])

DTF_LANG_WDID_WPTITLE_WPID_COLUMNS=["language", "wikidata_id", "wikipedia_title"]
DTF_LANG_WDID_WPTITLE_WPID = pd.DataFrame(columns=DTF_LANG_WDID_WPTITLE_WPID_COLUMNS)

# %%

def dataframe_from_cartesian_product(columns:Sequence[str], col0:Sequence, col1:Sequence):
    return pd.DataFrame({columns[0]: col0}).merge(pd.DataFrame({columns[1]: col1}), how="cross")

def dataframe_only_rows_not_in_dtf2(dtf1, dtf2, columns):
    dtf1["XXcombinedXX"] = ""
    dtf2["XXcombinedXX"] = ""
    for c in columns:
        dtf1["XXcombinedXX"] = dtf1["XXcombinedXX"] +"-XYX-"+dtf1[c]
        dtf2["XXcombinedXX"] = dtf2["XXcombinedXX"] +"-XYX-"+dtf2[c]
    dtf1_kept = dtf1.loc[~dtf1["XXcombinedXX"].isin(dtf2["XXcombinedXX"])].copy()
    del dtf1_kept["XXcombinedXX"]
    del dtf2["XXcombinedXX"]
    return dtf1_kept

# %%

wikipedia_page_titles_by_lng_and_wikidata_ids = dict()

# %%


def _get_wikipedia_page_titles_from_wikidata_ids_max50(dtf_lang_wdid):#wikidata_ids:Sequence[str], languages:Sequence[str]=None):
    """Returns wikipedia page titles from wikidata ids, max 50 items at a time"""
    #dtf_lang_wdid:pd.DataFrame = dataframe_from_ids_and_lngs(wikidata_ids, languages)

    if dtf_lang_wdid.shape[0]>50:
        raise(Exception(f"wiki._get_wikipedia_page_titles_from_wikidata_ids_max50() more than 50 wikidata_ids given:\n{wikidata_ids}"))
    if dtf_lang_wdid.shape[0]>0:
        url = "https://www.wikidata.org/w/api.php"
        params = {
            "format":  "json",
            "action":  "wbgetentities",
            "ids":  "|".join(dtf_lang_wdid.wikidata_id),
            "props":  "sitelinks"
        }
        print(f'"|".join(dtf_lang_wdid.wikidata_id)= {"|".join(dtf_lang_wdid.wikidata_id)}')

        resp = r.get(url=url, params=params)
        data = resp.json()
        
        #print(f"\n-----\nwiki._get_wikipedia_page_titles_from_wikidata_ids_max50(ids, {languages})\n dtf_lang_wdid:\n{dtf_lang_wdid}\ndata:\n{data}\n-----\n")
        entities = data["entities"]
        new_lng_wd_id_title = pd.DataFrame(columns=['language', 'wikidata_id', "wikipedia_title"], data=[
            (
                lng,
                wd_id,
                entities[wd_id]["sitelinks"][lng+"wiki"]["title"]
                if (lng+"wiki") in entities[wd_id]["sitelinks"]
                else None
            )
            for i,(lng, wd_id) in dtf_lang_wdid.iterrows()
        ])
        # wikipedia_titles_by_language = {
        #     lng: {
        #         # only consider wikidata id with a wikipedia page in given language
        #         wd_id: entities[wd_id]["sitelinks"][lng+"wiki"]["title"] if (lng+"wiki") in entities[wd_id]["sitelinks"] else None
        #         for wd_id in wikidata_ids
        #     }
        #     for lng in languages
        # }
        print(f"new_lng_wd_id_title:\n{new_lng_wd_id_title}")
        return new_lng_wd_id_title

# %%

def get_wikipedia_page_titles_from_wikidata_ids(wikidata_ids:Sequence[str], languages:Sequence[str]=None):
    """Returns wikipedia page titles from wikidata ids

    languages should be an array of two-letter abbreviations for desired languages

    note: this function returns an accumulator that accumulates endlessly over a program run.
    always iterate over your own wikidata_ids, not this function result. consider further optimization if long runs.
    """
    global DTF_LANG_WDID_WPTITLE

    dtf_lang_wdid:pd.DataFrame = dataframe_from_cartesian_product(["language", "wikidata_id"], languages,wikidata_ids)
    dtf_lang_wdid = dtf_lang_wdid.loc[dtf_lang_wdid.wikidata_id!="null"].copy()

    print(f"dtf_lang_wdid:\n{dtf_lang_wdid}")

    dtf_wdid_lang_to_query = dataframe_only_rows_not_in_dtf2(dtf_lang_wdid, DTF_LANG_WDID_WPTITLE, ["wikidata_id", "language"])

    print(f"dtf_wdid_lang_to_query:\n{dtf_wdid_lang_to_query}")

    accumulator = pd.DataFrame(columns=DTF_LANG_WDID_WPTITLE_COLUMNS)
    rest = dtf_wdid_lang_to_query
    while rest.shape[0]>0:
        current = rest[:50]
        rest = rest[50:]
        new_dtf_wdid_lang_title = _get_wikipedia_page_titles_from_wikidata_ids_max50(current)
        accumulator = accumulator.append(new_dtf_wdid_lang_title)
    accumulator = dataframe_only_rows_not_in_dtf2(accumulator, DTF_LANG_WDID_WPTITLE, ["wikidata_id", "language"])
    DTF_LANG_WDID_WPTITLE = DTF_LANG_WDID_WPTITLE.append(accumulator)
    return DTF_LANG_WDID_WPTITLE


# %%

wikipedia_page_ids_by_lng_and_title = dict()

# %%


def _get_wikipedia_pages_ids_from_titles_max50( wikipedia_titles:Sequence[str], language:str):
    """Returns wikipedia page ids from their title, max 50 items at a time"""
    #dtf_lang_wptitle = dataframe_from_cartesian_product(["wikipedia_title", "language"],wikidata_ids, [language])

    # get_wikipedia_pages_ids_from_titles(wikipedia_titles:str, language:str):
    if len(wikipedia_titles)>50:
        raise(Exception(f"wiki._get_wikipedia_pages_ids_from_titles_max50() more than 50 wikipedia_titles given:\n{wikipedia_titles}"))
    if len(wikipedia_titles)>0:
        url = f"https://{language}.wikipedia.org/w/api.php"
        params = {
            "action":  "query",
            "titles":  "|".join(wikipedia_titles),
            "format":  "json"
        }
        resp = r.get(url=url, params=params)
        data = resp.json()
        
        #print(f"\n-----\nwiki.get_wikipedia_pages_ids_from_titles(titles, {language})\ntitles_to_query:\n{titles_to_query}\ndata:\n{data}\n-----\n")
    
        pages = data["query"]["pages"]


        new_dtf_lng_title_wpid = pd.DataFrame(columns=['language', "wikipedia_title", 'wikipedia_id'], data=[
            (
                language,
                page_info["title"],
                pageid
            )
            for pageid,page_info in pages.items()
        ])
        return new_dtf_lng_title_wpid

# %%

def get_wikipedia_pages_ids_from_titles(dtf_lang_wptitle:pd.DataFrame):#wikipedia_titles:Sequence[str], language:str):
    """Returns wikipedia page ids from their title, max 50 items at a time"""
    global DTF_LANG_WDID_WPTITLE_WPID

    #dtf_lang_wptitle:pd.DataFrame = dataframe_from_cartesian_product(["wikipedia_title", "language"],wikipedia_titles, [language])
    
    dtf_lang_wptitle = dtf_lang_wptitle.loc[~dtf_lang_wptitle.wikipedia_title.isnull()].copy()

    dtf_lang_wptitle_to_query = dataframe_only_rows_not_in_dtf2(dtf_lang_wptitle, DTF_LANG_WDID_WPTITLE_WPID, ["wikipedia_title", "language"])

    accumulator = pd.DataFrame(columns=DTF_LANG_WDID_WPTITLE_WPID_COLUMNS)
    for lng in dtf_lang_wptitle_to_query.language.unique():
        rest = dtf_lang_wptitle_to_query
        while rest.shape[0]>0:
            current = rest[:50]
            rest = rest[50:]
            new_dtf_dtf_lang_wptitle_wpid = _get_wikipedia_pages_ids_from_titles_max50(current.wikipedia_title, lng)
            accumulator = accumulator.append(new_dtf_dtf_lang_wptitle_wpid)
    accumulator = dataframe_only_rows_not_in_dtf2(accumulator, DTF_LANG_WDID_WPTITLE_WPID, ["wikipedia_title", "language"])
    DTF_LANG_WDID_WPTITLE_WPID = DTF_LANG_WDID_WPTITLE_WPID.append(accumulator)
    return DTF_LANG_WDID_WPTITLE_WPID
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
    dtf_lang_wdid:pd.DataFrame = dataframe_from_cartesian_product(["wikidata_id", "language"],wikidata_ids, languages)

    wikidata_ids2 = ["Q1","Q78", "Q3044" ]
    languages2=[ "de"]
    dtf_lang_wdid2:pd.DataFrame = dataframe_from_cartesian_product(["wikidata_id", "language"],wikidata_ids2, languages2)
    
    #dtf_lang_wdid3 = dtf_lang_wdid2[dtf_lang_wdid2.wikidata.isin(dtf_lang_wdid.wikidata) ]

    dtf_lang_wdid_wptitle = get_wikipedia_page_titles_from_wikidata_ids(wikidata_ids, languages)

    dtf_lang_wptitle_wpid = get_wikipedia_pages_ids_from_titles(dtf_lang_wdid_wptitle)

    if False:
    # %%

        language="de"
        wikipedia_titles = wikipedia_titles_by_language[language]

        # %%

        page_titles_ids = get_wikipedia_page_titles_and_ids_from_wikidata_ids(wikidata_ids, languages)
        # %%
