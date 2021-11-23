
from __future__ import annotations
import re
from typing import TYPE_CHECKING

from pandas import isnull
import xml.etree.ElementTree as ET

from .utils import wikidata_entity_base_url, get_attributes_string, inception_being_regex, inception_end_regex
from .wiki import get_wikipedia_page_titles_and_ids_from_wikidata_ids
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
            grobid_tag=None
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
    def set_wikipedia_title_and_id(self, language, wikipedia_titles_and_ids=None):
        if wikipedia_titles_and_ids is None:
            wikipedia_titles_and_ids = get_wikipedia_page_titles_and_ids_from_wikidata_ids([self.wikidata_entity_id], [language])
        annotation_row = wikipedia_titles_and_ids.loc[
            (wikipedia_titles_and_ids.wikidata_id==self.wikidata_entity_id) &
            (wikipedia_titles_and_ids.language==language)
        ]
        if annotation_row.shape[0]>=1:
            self.wikipedia_page_title = annotation_row.wikipedia_title.values[0]
            if self.wikipedia_page_title=="null" or isnull(self.wikipedia_page_title):
                self.wikipedia_page_title = None
            self.wikipedia_page_id = annotation_row.wikipedia_id.values[0]
            if self.wikipedia_page_id=="null" or isnull(self.wikipedia_page_title):
                self.wikipedia_page_id = None            
    def __hash__(self):
        return hash((self.start, self.end, self.wikidata_entity_id, self.grobid_tag))
    def __eq__(self, other):
        if type(other) is type(self):
            return (other.start==self.start) and (other.end==self.end) and (other.wikidata_entity_id==self.wikidata_entity_id) and (other.end==self.grobid_tag)
        return False
    def inception_to_tag_string(self, xmi_id, tag_name="type3:NamedEntity", identifier_attribute_name="identifier"):
        """Returns a valid <type3:NamedEntity/> tag string for inception's UIMA CAS XMI (XML 1.1) format

        Tag & attribute name can be changed
        """
        return f'<{tag_name} xmi:id="{xmi_id}" sofa="1" begin="{self.start}" end="{self.end}" {identifier_attribute_name}="{self.wikidata_entity_url}"/>'
    def __repr__(self):
        return get_attributes_string("Annotation",self.__dict__)
    def entity_fishing_to_xml_tag(self, include_grobid_tag=False):
        annotation_tag = ET.Element("annotation")
        offset_tag = ET.SubElement(annotation_tag, "offset")
        offset_tag.text = str(self.start)
        length_tag = ET.SubElement(annotation_tag, "length")
        length_tag.text = str(self.length) 
        if self.wikidata_entity_id is not None:
            wikidata_id_tag = ET.SubElement(annotation_tag, "wikidataId") 
            wikidata_id_tag.text = wikidata_entity_base_url+str(self.wikidata_entity_id)
        if self.wikipedia_page_title is not None:
            wikipedia_title_tag = ET.SubElement(annotation_tag, "wikiName") 
            wikipedia_title_tag.text = str(self.wikipedia_page_title)
        if self.wikipedia_page_id is not None:
            wikipedia_id_tag = ET.SubElement(annotation_tag, "wikipediaId")
            wikipedia_id_tag.text = str(self.wikipedia_page_id)
        if self.mention is not None:
            mention_tag = ET.SubElement(annotation_tag, "mention")
            mention_tag.text = self.mention
        if include_grobid_tag and self.grobid_tag is not None:
            grobid_tag_tag = ET.SubElement(annotation_tag, "grobidTag")
            grobid_tag_tag.text = self.grobid_tag
        return annotation_tag
    
    @staticmethod
    def get_wikidata_id_from_url(wikidata_url):
        if (wikidata_url is not None) and wikidata_url!="null":
            return wikidata_url.replace(wikidata_entity_base_url, "") 
        return None

    @staticmethod
    def entity_fishing_from_tag(ef_xml_annotation_tag) -> Annotation:
        """Parses an annotation from an lxml.etree.parse(...) tag
        
        <annotation>
			<mention>14.1</mention>
			<wikiName>14 und 1 endlos</wikiName>
			<wikidataId>Q7468888</wikidataId>
			<wikipediaId>3677337</wikipediaId>
			<offset>0</offset>
			<length>4</length>
		</annotation>
        """
        offset = int(ef_xml_annotation_tag.find("offset").text)
        length = int(ef_xml_annotation_tag.find("length").text)
        wikidata_id = ef_xml_annotation_tag.find("wikidataId").text
        wikidata_id = ef_xml_annotation_tag.find("wikidataId").text
        wikipedia_page_id = ef_xml_annotation_tag.find("wikipediaId").text
        wikipedia_page_title = ef_xml_annotation_tag.find("wikiName").text
        mention = ef_xml_annotation_tag.find("mention").text
        return Annotation(offset, offset+length, wikidata_id, wikipedia_page_id, wikipedia_page_title, mention)
    @staticmethod
    def inception_from_tag_string(
            tag_string,
            identifier_attribute_name="identifier",
            grobid_tag_attribute_name="entityfishingtag",
            wikipedia_titles_and_ids=dict()
        ) -> Annotation:
        """
    
        <custom:Entityfishinglayer xmi:id="3726" sofa="1" begin="224" end="244" entityfishingtag="INSTALLATION" wikidataidentifier="http://www.wikidata.org/entity/Q2971666"/>
        """
        offset_match = inception_being_regex.search(tag_string)
        end_match = inception_end_regex.search(tag_string)
        if (not offset_match) or (not end_match):
            raise Exception(f"Annotation.inception_from_tag_string() missing begin or end attribute in tag: {tag_string}")
        offset = int(offset_match.group(1))
        end = int(end_match.group(1))

        grobid_tag_match = re.search(grobid_tag_attribute_name+r'="(.+?)"', tag_string)
        grobid_tag = grobid_tag_match.group(1) if grobid_tag_match else None

        identifier_match = re.search(identifier_attribute_name+r'="(.+?)"', tag_string)
        identifier_url = identifier_match.group(1) if identifier_match else None
        wikidata_id = None
        wikipedia_id = None
        wikipedia_title = None
        if identifier_url is not None:
            wikidata_id = Annotation.get_wikidata_id_from_url(identifier_url)
            if wikidata_id in wikipedia_titles_and_ids:
                wikipedia_title = wikipedia_titles_and_ids[wikidata_id][0]
                wikipedia_id = wikipedia_titles_and_ids[wikidata_id][1]
            
        return Annotation(offset, end, wikidata_id,
            wikipedia_page_id = wikipedia_id,
            wikipedia_page_title = wikipedia_title,
            grobid_tag=grobid_tag
        )
        
# %%