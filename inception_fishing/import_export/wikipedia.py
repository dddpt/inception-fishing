
from typing import Sequence
from pandas import isnull

from ..Annotation import Annotation
from ..Corpus import Corpus
from ..Document import Document
from ..utils import wikidata_entity_base_url
from .get_wikipedia_page_titles_and_ids_from_wikidata_ids import get_wikipedia_page_titles_and_ids_from_wikidata_ids

# Annotation
# ==============================================


def annotation_set_page_title_and_id(annotation:Annotation, language, wikipedia_titles_and_ids=None):
    if wikipedia_titles_and_ids is None:
        wikipedia_titles_and_ids = get_wikipedia_page_titles_and_ids_from_wikidata_ids([annotation.wikidata_entity_id], [language])
    annotation_row = wikipedia_titles_and_ids.loc[
        (wikipedia_titles_and_ids.wikidata_id==annotation.wikidata_entity_id) &
        (wikipedia_titles_and_ids.language==language)
    ]
    if annotation_row.shape[0]>=1:
        annotation.wikipedia_page_title = annotation_row.wikipedia_title.values[0]
        if annotation.wikipedia_page_title=="null" or isnull(annotation.wikipedia_page_title):
            annotation.wikipedia_page_title = None
        annotation.wikipedia_page_id = annotation_row.wikipedia_id.values[0]
        if annotation.wikipedia_page_id=="null" or isnull(annotation.wikipedia_page_title):
            annotation.wikipedia_page_id = None


def annotations_get_page_titles_and_ids(annotations:Sequence[Annotation], language):
    """Gets annotations wikipedia page title and ids from their wikidata id"""
    wikidata_ids = {
        a.wikidata_entity_id
        for a in annotations
        if a.wikidata_entity_id is not None and a.wikidata_entity_id != "None" and \
            a.wikidata_entity_id != "" and a.wikidata_entity_id != "null"
    }
    return get_wikipedia_page_titles_and_ids_from_wikidata_ids(wikidata_ids, [language])

def annotations_set_page_titles_and_ids(annotations:Sequence[Annotation], language, wikipedia_page_titles_and_ids=None):
    if wikipedia_page_titles_and_ids is None:
        wikipedia_page_titles_and_ids = annotations_get_page_titles_and_ids(annotations, language)
    for a in annotations:
        annotation_set_page_title_and_id(a, language, wikipedia_page_titles_and_ids)
    return wikipedia_page_titles_and_ids

# Documents
# ==============================================


            
def document_get_annotations_page_titles_and_ids(document, language):
    return annotations_get_page_titles_and_ids([a for a in document.annotations], language)
def document_set_annotations_page_titles_and_ids(document, language, wikipedia_page_titles_and_ids=None):
    return annotations_set_page_titles_and_ids([a for a in document.annotations], language, wikipedia_page_titles_and_ids)

# Corpus
# ==============================================


def corpus_get_annotations_page_titles_and_ids(corpus:Corpus, language):
    return annotations_get_page_titles_and_ids(
        [a for d in corpus.documents for a in d.annotations],
        language
    )
def corpus_set_annotations_page_titles_and_ids(corpus:Corpus, language, wikipedia_page_titles_and_ids=None):
    return annotations_set_page_titles_and_ids(
        [a for d in corpus.documents for a in d.annotations],
        language,
        wikipedia_page_titles_and_ids
    )