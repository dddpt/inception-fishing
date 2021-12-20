from __future__ import annotations
from csv import DictReader
from os import path
from warnings import warn



script_folder = path.dirname(__file__)

DEFAULT_WIKIDATA_LINKS_FILE = path.join(script_folder, "wikidata_dhs_wikipedia_articles_gndid_instanceof.csv")
WIKIDATA_QUERY_FILE = path.join(script_folder, "wikidata_dhs_wikipedia_articles_gndid.sparql")

LOADED_WIKIDATA_LINKS_CSVS = set()
WIKIDATA_LINKS = dict()
WIKIDATA_DUPLICATE_LINKS = dict()

WIKIDATA_URL_KEY = "item"
def get_wikidata_short_id(wikidata_url):
    if wikidata_url:
        return wikidata_url.replace("http://www.wikidata.org/entity/", "")
    return None

SPARQL_DOWNLOAD_DISCLAIMER = \
    f"A prerequisite is to have manually downloaded the result of the sparql query in file '{WIKIDATA_QUERY_FILE}' at 'https://query.wikidata.org/' " + \
    f"as a csv at this location '{DEFAULT_WIKIDATA_LINKS_FILE}' (or provide to this function the location of your csv file as function argument)."

def load_wikidata_links(wikidata_links_file = DEFAULT_WIKIDATA_LINKS_FILE):
    """Loads the csv links in a dictionary of the form wikidata_id->list(linked wikidata_wikipedia entities)\n\n""" + SPARQL_DOWNLOAD_DISCLAIMER
    if wikidata_links_file not in LOADED_WIKIDATA_LINKS_CSVS:
        if not path.exists(wikidata_links_file):
            raise Exception(
                f"inception_fishing.import_export.get_dhs_id_from_wikidata_id() wikidata_links_file at location '{wikidata_links_file}' not found.\n"+
                SPARQL_DOWNLOAD_DISCLAIMER
            )
        with open(wikidata_links_file) as f:
            reader = DictReader(f)
            for r in reader:
                wd_id = get_wikidata_short_id(r[WIKIDATA_URL_KEY])
                r["wikidata_id"] = wd_id
                if wd_id in WIKIDATA_LINKS and r["dhsid"]!=WIKIDATA_LINKS[wd_id]['dhsid']:
                    #warn(f"inception_fishing.import_export.get_dhs_id_from_wikidata_id(): wikidata id {wd_id} pointing to multiple DHS ids: {[WIKIDATA_LINKS[wd_id]['dhsid'], r['dhsid']]}") 
                    if wd_id not in WIKIDATA_DUPLICATE_LINKS:
                        WIKIDATA_DUPLICATE_LINKS[wd_id] = [WIKIDATA_LINKS[wd_id]]
                    WIKIDATA_DUPLICATE_LINKS[wd_id].append(r)
                WIKIDATA_LINKS[wd_id] = r
        LOADED_WIKIDATA_LINKS_CSVS.add(wikidata_links_file)
    return WIKIDATA_LINKS

def get_infos_from_wikidata_id(wikidata_id):
    load_wikidata_links()
    wikidata_id = get_wikidata_short_id(wikidata_id)
    return WIKIDATA_LINKS.get(wikidata_id)

def get_dhs_id_from_wikidata_id(wikidata_id):
    row = get_infos_from_wikidata_id(wikidata_id)
    if row is not None:
        return row["dhsid"]
    return None 
