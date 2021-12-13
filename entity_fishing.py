from os import path

import xml.etree.ElementTree as ET

from .Annotation import Annotation
from .Corpus import Corpus
from .Document import Document
from .utils import wikidata_entity_base_url

# Annotation
# ==============================================
def annotation_to_xml_tag(annotation:Annotation, include_grobid_tag=False):
    annotation_tag = ET.Element("annotation")
    offset_tag = ET.SubElement(annotation_tag, "offset")
    offset_tag.text = str(annotation.start)
    length_tag = ET.SubElement(annotation_tag, "length")
    length_tag.text = str(annotation.length) 
    if annotation.wikidata_entity_id is not None:
        wikidata_id_tag = ET.SubElement(annotation_tag, "wikidataId") 
        wikidata_id_tag.text = wikidata_entity_base_url+str(annotation.wikidata_entity_id)
    if annotation.wikipedia_page_title is not None:
        wikipedia_title_tag = ET.SubElement(annotation_tag, "wikiName") 
        wikipedia_title_tag.text = str(annotation.wikipedia_page_title)
    if annotation.wikipedia_page_id is not None:
        wikipedia_id_tag = ET.SubElement(annotation_tag, "wikipediaId")
        wikipedia_id_tag.text = str(annotation.wikipedia_page_id)
    if annotation.mention is not None:
        mention_tag = ET.SubElement(annotation_tag, "mention")
        mention_tag.text = annotation.mention
    if include_grobid_tag and annotation.grobid_tag is not None:
        grobid_tag_tag = ET.SubElement(annotation_tag, "grobidTag")
        grobid_tag_tag.text = annotation.grobid_tag
    return annotation_tag



def annotation_from_tag(ef_xml_annotation_tag) -> Annotation:
    """Parses an annotation from an lxml.etree.parse(...) tag
    
    <annotation>
        <mention>14.1</mention>
        <wikiName>14 und 1 endlos</wikiName>
        <wikidataId>http://www.wikidata.org/entity/Q7468888</wikidataId>
        <wikipediaId>3677337</wikipediaId>
        <offset>0</offset>
        <length>4</length>
    </annotation>
    """
    offset = int(ef_xml_annotation_tag.find("offset").text)
    length = int(ef_xml_annotation_tag.find("length").text)
    mention = ef_xml_annotation_tag.find("mention").text
    wikidata_url = ef_xml_annotation_tag.find("wikidataId")
    wikidata_url = wikidata_url.text if wikidata_url is not None else None
    wikipedia_page_id = ef_xml_annotation_tag.find("wikipediaId")
    wikipedia_page_id = wikipedia_page_id.text if wikipedia_page_id is not None else None
    wikipedia_page_title = ef_xml_annotation_tag.find("wikiName")
    wikipedia_page_title = wikipedia_page_title.text if wikipedia_page_title is not None else None
    return Annotation(offset, offset+length, None, wikipedia_page_id, wikipedia_page_title, wikidata_url, mention)

# Documents
# ==============================================


def document_get_text_from_corpus_folder(document:Document, corpus_folder):
    text_file_path = path.join(corpus_folder, document.name) if corpus_folder else document.name
    with open(text_file_path) as f:
            document.text = f.read()
            return document.text


def document_to_xml_tag(self, **annotation_kwargs):
    document_tag = ET.Element("document")
    document_tag.set("docName", self.name)
    for a in self.annotations:
        document_tag.append(annotation_to_xml_tag(a, **annotation_kwargs))
    return document_tag


def document_from_tag(ef_xml_document_tag, corpus_folder = None) -> Document:
    """Returns a Document from a lxml etree entity-fishing document tag"""
    annotations_tags = ef_xml_document_tag.findall("annotation")
    doc = Document(
        ef_xml_document_tag.attrib["docName"],
        [annotation_from_tag(t) for t in annotations_tags]
    )
    if corpus_folder:
        document_get_text_from_corpus_folder(doc, corpus_folder)
    return doc


# Corpus
# ==============================================



def corpus_to_xml_tag(corpus:Corpus, **document_kwargs):
    corpus_tag = ET.Element(corpus.name+".entityAnnotation")
    for d in corpus.documents:
        corpus_tag.append(document_to_xml_tag(d, **document_kwargs))
    return corpus_tag

def corpus_to_xml_file(corpus:Corpus, filepath, **document_kwargs):
    intro_str = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'
    corpus_tag = corpus_to_xml_tag(corpus, **document_kwargs)
    
    ET.ElementTree(corpus_tag).write(filepath, encoding="utf-8")
    with open(filepath, "r", encoding="utf-8") as file:
        content = file.read()
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(intro_str+"\n"+content)


def corpus_from_tag_and_corpus(ef_xml_root_tag, corpus_folder = None) -> Corpus:
    """Returns a Corpus object from a lxml.etree tag (the root of an EF evaluation XML output) and the EF corpus folder"""
    name = ef_xml_root_tag.tag.replace(".entityAnnotation", "")
    document_tags = ef_xml_root_tag.findall("document")
    return Corpus(name, [document_from_tag(t, corpus_folder) for t in document_tags])