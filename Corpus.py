
from __future__ import annotations
from os import path, listdir
from typing import Sequence

import xml.etree.ElementTree as ET

from .Document import Document
from .utils import get_attributes_string, clef_hipe_scorer_tsv_columns
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

    def clef_hipe_scorer_to_conllu_tsv(self, filepath, spacy_nlp, **document_kwargs):
        doc_tsv_separator = "\n"+(2*"									\n")
        alphabetic_ordered_docs = sorted(self.documents, key= lambda d: d.name)
        tsv_docs = [d.clef_hipe_scorer_to_conllu_tsv(spacy_nlp, **document_kwargs) for d in alphabetic_ordered_docs]

        tsv_content = "\t".join(clef_hipe_scorer_tsv_columns)+"\n"+doc_tsv_separator.join(tsv_docs)
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(tsv_content)
        return tsv_content

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
    @staticmethod
    def inception_from_directory(
            name,
            dir_path,
            inception_user_name,
            wikipedia_page_titles_and_ids_language = None,
            **document_inception_from_file_kwargs
        ) -> Corpus:

        documents_directories = listdir(dir_path)
        documents = [
            Document.inception_from_file(
                path.join(dir_path,dd,inception_user_name+".xmi"),
                dd,
                **document_inception_from_file_kwargs
            ) for dd in documents_directories
            if path.isdir(path.join(dir_path,dd))
        ]

        corpus = Corpus(name, documents)
        if wikipedia_page_titles_and_ids_language is not None:
            corpus.set_annotations_wikipedia_page_titles_and_ids(wikipedia_page_titles_and_ids_language)

        return corpus

# %%