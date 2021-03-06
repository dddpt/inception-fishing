
from __future__ import annotations
from copy import deepcopy
import re
from typing import TYPE_CHECKING
from warnings import warn

from .utils import wikidata_entity_base_url, get_attributes_string
if TYPE_CHECKING:
    from .Document import Document



class Annotation:
    def __init__(
            self,
            start,
            end,
            wikidata_entity_id=None,
            wikipedia_page_id=None,
            wikipedia_page_title=None,
            wikidata_entity_url=None,
            mention=None,
            grobid_tag=None,
            extra_fields=None
        ):
        """Creates Annotation, end is non-inclusive"""
        self.start:int = start
        self.end:int = end
        self.wikidata_entity_id:str = wikidata_entity_id if wikidata_entity_id!="null" else None
        if (self.wikidata_entity_id is None) and (wikidata_entity_url is not None):
            self.wikidata_entity_url = wikidata_entity_url
        self.wikipedia_page_id:str = wikipedia_page_id
        self.wikipedia_page_title:str = wikipedia_page_title
        self.grobid_tag:str = grobid_tag
        self.mention:str = mention
        self.extra_fields:dict = extra_fields if extra_fields is not None else dict()
    @property
    def length(self):
        return self.end-self.start
    @length.setter
    def length(self, new_length):
        self.end = self.start+new_length
    @property
    def wikidata_entity_url(self) -> str:
        if self.wikidata_entity_id is None:
            return None
        return wikidata_entity_base_url + self.wikidata_entity_id
    @wikidata_entity_url.setter
    def wikidata_entity_url(self, new_url):
        self.wikidata_entity_id = Annotation.get_wikidata_id_from_url(new_url)
    def set_mention(self, document:Document):
        self.mention = document.text[self.start:self.end]         
    def __hash__(self):
        return hash((self.start, self.end, self.wikidata_entity_id, self.grobid_tag))
    def __eq__(self, other):
        if type(other) is type(self):
            return (other.start==self.start) and (other.end==self.end) and (other.wikidata_entity_id==self.wikidata_entity_id) and (other.grobid_tag==self.grobid_tag)
        return False
    def __repr__(self):
        return get_attributes_string("Annotation",self.__dict__)
    def __copy__(self) -> Annotation:
        return Annotation(
            self.start,
            self.end,
            wikidata_entity_id = self.wikidata_entity_id,
            wikipedia_page_id = self.wikipedia_page_id,
            wikipedia_page_title = self.wikipedia_page_title,
            mention = self.mention,
            grobid_tag = self.grobid_tag,
            extra_fields = deepcopy(self.extra_fields)
        )
    def __deepcopy__(self) -> Annotation:
        return self.__copy__()

    @staticmethod
    def get_wikidata_id_from_url(wikidata_url):
        if (wikidata_url is not None) and wikidata_url!="null":
            return wikidata_url.replace(wikidata_entity_base_url, "") 
        return None
        
# %%