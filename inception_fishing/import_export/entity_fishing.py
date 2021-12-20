from copy import Error
import json
from os import path
from typing import Dict

import requests as r
import xml.etree.ElementTree as ET

from ..Annotation import Annotation
from ..Corpus import Corpus
from ..Document import Document
from ..utils import wikidata_entity_base_url, ANNOTATION_ORIGIN_ENTITY_FISHING


entity_fishing_default_base_url = "http://localhost:8090"
entity_fishing_disambiguate_path = "/service/disambiguate"

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

def annotation_to_json(annotation:Annotation, as_dict=False):
    """returns None if annotation doesn't have a wikipedia_page_id, the id that entity-fishing needs"""
    if annotation.wikipedia_page_id is None:
        return None
    json_annotation = {
        "rawName": annotation.mention,
        "offsetStart": annotation.start,
        "offsetEnd": annotation.end,
        "wikipediaExternalRef": annotation.wikipedia_page_id,
        "wikidataId": annotation.wikidata_entity_id
    }
    if as_dict:
        return json_annotation
    else:
        return json.dumps(json_annotation)

def annotation_from_json(json_annotation:Dict):
    a = Annotation(
        json_annotation["offsetStart"],
        json_annotation["offsetEnd"],
        json_annotation.get("wikidataId"),
        json_annotation.get("wikipediaExternalRef"),
        grobid_tag = json_annotation.get("type")
        #mention = json_annotation["rawName"] # not sure this corresponds
    )
    used_keys = [
        "offsetStart",
        "offsetEnd",
        "wikidataId",
        "wikipediaExternalRef",
        "type"
        #"rawName"
    ]
    for k, v in json_annotation.items():
        if k not in used_keys:
            a.extra_fields[k]=v
    return a

# Documents
# ==============================================


def document_get_text_from_corpus_folder(document:Document, corpus_folder):
    text_file_path = path.join(corpus_folder, document.name) if corpus_folder else document.name
    with open(text_file_path) as f:
            document.text = f.read()
            return document.text


def document_to_xml_tag(document:Document, **annotation_kwargs):
    document_tag = ET.Element("document")
    document_tag.set("docName", document.name)
    for a in document.annotations:
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

non_query_kwargs = set([
    "as_dict",
    "include_entities",
    "entity_fishing_base_url",
    "annotations_origin"
])
def document_to_json_request(document:Document, language, include_entities=True, as_dict=False, **query_kwargs):
    """Formats the document to a json (dict or str) ready to be sent to the entity-fishing API
    
    Annotations who have a wikipedia_page_id set will be added to the json request so that entity-fishing
    can use this information. Can be disabled with include_entities=False 
    """
    entities = []
    if include_entities:
        entities = [annotation_to_json(a, as_dict=True) for a in  document.annotations]
        #print(f"entities middle len: {len(entities)}")
        entities = [e for e in entities if e is not None]
    #print(f"ef.document_to_json_request() \ninclude_entities: {include_entities}\ndocument.annotations:\n{document.annotations}\nentities:\n{entities}\n------------------------------")
    json_query = {
        "text": document.text,
        #"shortText": "",
        #"termVector": [],
        "language": {
            "lang": language
        },
        "entities": entities,
        #"mentions": [
        #    "ner",
        #    "wikipedia"
        #],
        #"nbest": False,
        #"sentence": False
    }
    for k,v in query_kwargs.items():
        if k not in non_query_kwargs:
            json_query[k] = v
    
    if as_dict:
        return json_query
    else:
        return json.dumps(json_query)


def document_send_request(document:Document, language:str, entity_fishing_base_url = entity_fishing_default_base_url, include_entities=True, **query_kwargs):
    """Sends the document text to a running entity-fishing service for NE linking and returns the response json.
    
    """
    entity_fishing_disambiguate_url = entity_fishing_base_url+entity_fishing_disambiguate_path
    json_query = document_to_json_request(document, language, include_entities, True, **query_kwargs)
    entity_fishing_resp = r.post(entity_fishing_disambiguate_url, json = json_query)

    if entity_fishing_resp.status_code!=200:
        raise Error(
            f"inception_fishing.entity_fishing.document_send_request() Non 200 response code. "+
            f"Unable to connect to entity-fishing at url '{entity_fishing_disambiguate_url}'.\n"+
            f"Response code: {entity_fishing_resp.status_code}\nResponse content:\n{entity_fishing_resp.content}"+
            f"Sent JSON query:\n{json_query}"
        )
    return json.loads(entity_fishing_resp.content)

def document_augment_from_json_response(document:Document, json_response:Dict, annotations_origin = ANNOTATION_ORIGIN_ENTITY_FISHING, **kwargs):
    """Augments a document with the annotation obtained from the entity-fishing API

    Adds an "entity_fishing_response" extra field to document, containing the json_response excluding its "entities" field (which is added to annotations)
    Adds an "origin" extra field to annotations, with value "entity_fishing" by default
    """
    entity_fishing_response = dict()
    for k,v in json_response.items():
        if k!="entities":
            entity_fishing_response[k] = v
    document.extra_fields["entity_fishing_response"] = entity_fishing_response

    entities = json_response.get("entities")
    if entities is not None:
        new_annotations = [annotation_from_json(j) for j in entities]
        for a in new_annotations:
            a.extra_fields["origin"] = annotations_origin
        document.annotations = document.annotations+new_annotations

    return document
    
def document_named_entity_linking(document, language:str, include_entities=True, **kwargs):
    """Augments document with entity-fishing named entities annotations

    calls both document_send_request() and document_augment_from_json_response()
    """
    entity_fishing_json_resp = document_send_request(document, language, include_entities = include_entities, **kwargs)
    return document_augment_from_json_response(document, entity_fishing_json_resp, **kwargs)
    

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