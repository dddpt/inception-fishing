
from __future__ import annotations
from os import path, listdir
from typing import Sequence

import xml.etree.ElementTree as ET

from .Document import Document
from .utils import get_attributes_string
from .wiki import get_wikipedia_page_titles_and_ids_from_wikidata_ids

# %%

class Corpus:
    def __init__(self, name, documents):
        self.name:str = name
        self.documents:Sequence[Document] = documents
            
    def get_annotations_wikipedia_page_titles_and_ids(self, language):
        """Gets annotations wikipedia page title and ids from their wikidata id"""
        wikidata_ids = {
            a.wikidata_entity_id
            for d in self.documents
            for a in d.annotations
            if a.wikidata_entity_id is not None
        }
        return get_wikipedia_page_titles_and_ids_from_wikidata_ids(wikidata_ids, [language])
    def set_annotations_wikipedia_page_titles_and_ids(self, language):
        wikipedia_page_titles_and_ids = self.get_annotations_wikipedia_page_titles_and_ids(language)
        for d in self.documents:
            for a in d.annotations:
                a.set_wikipedia_title_and_id(language, wikipedia_page_titles_and_ids)

    def __repr__(self):
        return get_attributes_string(
            "Corpus",
            {"name": self.name,
            "documents": [d.name for d in self.documents]}
        )
    def __deepcopy__(self) -> Corpus:
        return Corpus(
            self.name,
            [d.__deepcopy__() for d in self.documents],
        )
# %%