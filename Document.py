

from __future__ import annotations
from csv import DictReader
from os import path, listdir, replace
import re
from typing import Dict, Sequence
from warnings import warn

from spacy.tokens import Doc, Token
import xml.etree.ElementTree as ET

from .Annotation import Annotation
from .utils import get_attributes_string

# %%


# %%


class Document:
    def __init__(self, name:str, annotations, text = ""):
        self.name:str = name
        self.annotations:Sequence[Annotation] = annotations
        self.text:str = text
    
    def replace_span(self, start, end, replacement):
        """Replaces given span in Document text
        
        Throws an exception if span intersects with an existing annotation

        returns an incremental match, a tuple consisting of:
        0) start
        1) span original content
        2) replacement
        3) annotation_indexation_shift
        """
        replaced_length = end-start
        replacement_length=len(replacement)
        annotation_indexation_shift = replacement_length - replaced_length
        old_span_content = self.text[start:end]
        new_text = self.text[:start] + replacement + self.text[end:]
        annotations_to_remove = set()
        for a in self.annotations:
            #a_starts_in_replacement = (a.start >= start) and (a.start <end) 
            #a_ends_in_replacement = (a.end > start) and (a.end > end)
            replacement_starts_in_a = (start >= a.start) and (start < a.end) 
            replacement_ends_in_a = (end > a.start) and (end <= a.end)
            replacement_is_around_a = (start <= a.start and end>a.end) or (start < a.start and end>=a.end)
            # print(f"start_between: {start_between}, end_between: {end_between}")
            if replacement_is_around_a:
                warn(f"Document.replace_span({start}, {end}, {replacement}) for doc {self.name} englobes annotation {a}. This annotation is removed from document.")
                annotations_to_remove.add(a)
            elif replacement_starts_in_a != replacement_ends_in_a and start!=end:
                raise Exception(f"Document.replace_span({start}, {end}, {replacement}) for doc {self.name} intersects with {a}. Text:\n{self.text}")
            else:
                if a.start >= end:
                    a.start += annotation_indexation_shift
                if a.end >= end:
                    a.end += annotation_indexation_shift
        self.annotations = [
            a for a in self.annotations
            if a not in annotations_to_remove
        ]
        self.text=new_text
        return (start, old_span_content, replacement, annotation_indexation_shift)

    def replace_regex(self, to_replace_regex, replacement):
        """Replaces the given regex in the text

        returns the list of incremental matches tuples from replace_span(), see replace_span() doc

        Not that incremental matches' starts are incrementally computed and do not directly correspond to the new Document text.
        If you want to re-modify the replacements, you have to do so in reverse order for starts to match.
        """
        match = re.search(to_replace_regex, self.text)
        incremental_matches = []
        while match is not None:
            start, end = match.span()
            incremental_matches.append((start, self.text[start:end]))
            incremental_matches.append(self.replace_span(start, end, replacement))
            match = re.search(to_replace_regex, self.text)
        return incremental_matches
    def reverse_replace_span(self, incremental_match):
        """Reverse a single replace_span() call from its incremental_match return
        
        see replace_span() doc
        """
        start, original_content, replacement, shift = incremental_match
        self.replace_span(start, start+len(replacement), original_content)
    def reverse_consecutive_replace_span(self, incremental_matches):
        """Reverse a consecutive list of replace_span() call from their incremental_matches list
        
        typically used to reverse a replace_regex() call
        """
        return [
            self.reverse_replace_span(incremental_match)
            for incremental_match in incremental_matches.reverse()
        ]
    def update_mentions(self):
        for a in self.annotations:
            a.set_mention(self)
    def get_annotations_nesting_level(self):
        nesting_levels = {
            a: 0
            for a in self.annotations
        }
        if len(self.annotations) <= 1:
            return nesting_levels
        self.annotations.sort(key=lambda a: a.start)
        for i,a in enumerate(self.annotations[:-1]):
            for a2 in self.annotations[i+1:]:
                if a2.start<a.end:
                    #print(f"NESTING: {a2}\ninsid\n{a}\n")
                    nesting_levels[a2] = nesting_levels[a2]+1
                else:
                    break
        return nesting_levels
    def remove_nested_annotations(self):
        nesting_levels = self.get_annotations_nesting_level()
        self.annotations = [a for a in self.annotations if nesting_levels[a]==0]
    def filter_annotations(self, filter):
        self.annotations = [a for a in self.annotations if filter(a)]
    def __repr__(self):
        return get_attributes_string("Document",self.__dict__)
    def __deepcopy__(self) -> Document:
        return Document(
            self.name,
            [a.__deepcopy__() for a in self.annotations],
            self.text
        )
    
    def spacy_to_doc(self, spacy_nlp) -> Doc:
        """Transforms the Document into a spacy doc, adds annotations to tokens."""
        spacy_doc:Doc = spacy_nlp(self.text)
        #print(f"Doc.spacy_to_doc() for {self.name}")
        for t in spacy_doc:
            if not t.has_extension("wikidata_entity_id"):
                t.set_extension("wikidata_entity_id", default="")
            if not t.has_extension("wikipedia_page_id"):
                t.set_extension("wikipedia_page_id", default="")
        for a in self.annotations:
            tokens = a.spacy_get_tokens(spacy_doc)
            for t in tokens:
                t._.wikidata_entity_id = a.wikidata_entity_id
                t._.wikipedia_page_id = a.wikipedia_page_id
        return spacy_doc
    @staticmethod
    def from_dhs_article(
        dhs_article,
        dhs_wikidata_wikipedia_links_dict:Dict[str,Dict]|None = None,
        wikipedia_page_name_language = "fr",
        p_text_blocks_separator = "\n",
        non_p_text_blocks_separator = "\n",
    ):
        """Creates a document from a dhs_article annotating text blocks and text_links 
        
        dhs_wikidata_wikipedia_links should be a dict of dict with structure:
        {dhs-id: dict(
            - item (wikidata id)
            - itemLabel 
            - dhsid
            - namefr (wikipedia name fr)
            - articlefr (wikipedia url fr)
            - namede
            - articlede
            - nameit
            - articleit
            - nameen
            - articleen
            - instanceof
            - instanceofLabel
            - gndid
        )}

        Creates to two types of annotations:
        - annotations for text blocks with extra_fields "dhs_type"->"text_block" and "dhs_html_tag"->html tag name
        - annotations for text links with extra_fields "dhs_type"->"text_link", "dhs_id"->dhs_id and "dhs_href"->internal dhs link
        """
        if dhs_wikidata_wikipedia_links_dict is None:
            dhs_wikidata_wikipedia_links_dict=dict()
        
        annotations:Sequence[Annotation] = []
        dhs_article_id_from_url_regex = re.compile(r"(fr|de|it)/articles/(\d+)/")

        # assembling text blocks as annotations
        text_blocks = dhs_article.parse_text_blocks()
        whole_text = ""
        for tag, text in text_blocks:
            new_whole_text = whole_text+text
            annotations.append(Annotation(
                len(whole_text),
                len(new_whole_text),
                extra_fields = {"dhs_type": "text_block", "dhs_html_tag": tag}
            ))
            if tag =="p":
                whole_text = new_whole_text+p_text_blocks_separator
            else:
                whole_text = new_whole_text+non_p_text_blocks_separator

        # assembling text links as annotations with wikidata ids
        text_links_per_blocks = dhs_article.parse_text_links()
        for i, text_links in enumerate(text_links_per_blocks):
            text_block_start = annotations[i].start
            for text_link in text_links:
                start, end, mention, href = text_link.values()
                # get text link correspondance in wikidata & wikipedia (if present)
                wikidata_entity_url = None
                wikipedia_page_title = None
                dhs_id_match = dhs_article_id_from_url_regex.search(href)
                if dhs_id_match:
                    dhs_id = dhs_id_match.group(2)
                    wikidata_entry = dhs_wikidata_wikipedia_links_dict.get(dhs_id)
                    if wikidata_entry:
                        wikidata_entity_url = wikidata_entry["item"]
                        wikidata_entity_url = wikidata_entity_url if wikidata_entity_url!="" else None
                        wikipedia_page_title = wikidata_entry["name"+wikipedia_page_name_language]
                        wikipedia_page_title = wikipedia_page_title if wikipedia_page_title!="" else None
                annotations.append(Annotation(
                    text_block_start+start,
                    text_block_start+end,
                    wikidata_entity_url = wikidata_entity_url,
                    wikipedia_page_title = wikipedia_page_title,
                    mention = mention,
                    extra_fields={"dhs_type": "text_link", "dhs_href": href, "dhs_id": dhs_id}
                ))
                
        return Document(dhs_article.title, annotations, whole_text)



# %%