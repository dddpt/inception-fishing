

from __future__ import annotations
from os import path, listdir
import re
from typing import Sequence

import xml.etree.ElementTree as ET

from .Annotation import Annotation
from .utils import wikidata_entity_base_url, get_attributes_string, inception_being_regex, inception_end_regex, INCEPTION_DEFAULT_TAGSET_TAG_STR
from .wiki import get_wikipedia_page_titles_and_ids_from_wikidata_ids

# %%

class Document:
    def __init__(self, name:str, annotations, text = ""):
        self.name:str = name
        self.annotations:Sequence[Annotation] = annotations
        self.text:str = text
    
    def replace_span(self, start, end, replacement):
        """Replaces given span
        
        Throws an exception if both 
        """
        replaced_length = end-start
        replacement_length=len(replacement)
        annotation_indexation_shift = replacement_length - replaced_length
        new_text = self.text[:start] + replacement + self.text[end:]
        for a in self.annotations:
            start_between = (a.start >= start) and (a.start <end) 
            end_between = (a.end >= start) and (a.end <end)
            print(f"start_between: {start_between}, end_between: {end_between}")
            if start_between != end_between:
                raise Exception(f"Document.replace_span({start}, {end}, {replacement}) for doc {self.name} intersects with {a}. Text:\n{self.text}")
            if a.start >= end:
                a.start += annotation_indexation_shift
            if a.end >= end:
                a.end += annotation_indexation_shift
        self.text=new_text
        return annotation_indexation_shift

    def replace_regex(self, to_replace_regex, replacement):
        total_shift = 0
        for match in re.finditer(to_replace_regex, self.text):
            start, end = match.span()
            total_shift += self.replace_span(start, end, replacement)
        return total_shift    
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
    def entity_fishing_get_text_from_corpus_folder(self, corpus_folder):
        text_file_path = path.join(corpus_folder, self.name) if corpus_folder else self.name
        with open(text_file_path) as f:
                self.text = f.read()
                return self.text
    def __repr__(self):
        return get_attributes_string("Document",self.__dict__)
    def entity_fishing_to_xml_tag(self, **annotation_kwargs):
        document_tag = ET.Element("document")
        document_tag.set("docName", self.name)
        for a in self.annotations:
            document_tag.append(a.entity_fishing_to_xml_tag(**annotation_kwargs))
        return document_tag
    
    def spacy_to_doc(self, spacy_nlp):
        """Transforms the Document into a spacy doc, adds annotations to tokens."""
        spacy_doc = spacy_nlp(self.text)
        return spacy_doc

    def inception_to_xml_string(self, force_single_sentence=False, annotations_xmi_ids_start = 9000, tagset_tag_str=INCEPTION_DEFAULT_TAGSET_TAG_STR, **named_entity_to_tag_kwargs):
        """Returns a valid inception input file content in UIMA CAS XMI (XML 1.1) format
        
        Note: replaces " characters in text wth ', to simplify handling of XML.
        force_single_sentence=True forces the whole document text to be considered as a single sentence by inception,
        useful when text contains non-sentence-inducing dots (such as abbreviation dots in the DHS)
        """
        annotations_str ="\n            ".join(ne.inception_to_tag_string(annotations_xmi_ids_start+i, **named_entity_to_tag_kwargs) for i, ne in enumerate(self.annotations))
        force_single_sentence_str = f'\n            <type4:Sentence xmi:id="8998" sofa="1" begin="0" end="{len(self.text)}"/>' if force_single_sentence else ""
        return f'''
        <?xml version="1.1" encoding="UTF-8"?>
        <xmi:XMI xmlns:pos="http:///de/tudarmstadt/ukp/dkpro/core/api/lexmorph/type/pos.ecore" xmlns:tcas="http:///uima/tcas.ecore" xmlns:xmi="http://www.omg.org/XMI" xmlns:cas="http:///uima/cas.ecore" xmlns:tweet="http:///de/tudarmstadt/ukp/dkpro/core/api/lexmorph/type/pos/tweet.ecore" xmlns:morph="http:///de/tudarmstadt/ukp/dkpro/core/api/lexmorph/type/morph.ecore" xmlns:dependency="http:///de/tudarmstadt/ukp/dkpro/core/api/syntax/type/dependency.ecore" xmlns:type5="http:///de/tudarmstadt/ukp/dkpro/core/api/semantics/type.ecore" xmlns:type8="http:///de/tudarmstadt/ukp/dkpro/core/api/transform/type.ecore" xmlns:type7="http:///de/tudarmstadt/ukp/dkpro/core/api/syntax/type.ecore" xmlns:type2="http:///de/tudarmstadt/ukp/dkpro/core/api/metadata/type.ecore" xmlns:type9="http:///org/dkpro/core/api/xml/type.ecore" xmlns:type3="http:///de/tudarmstadt/ukp/dkpro/core/api/ner/type.ecore" xmlns:type4="http:///de/tudarmstadt/ukp/dkpro/core/api/segmentation/type.ecore" xmlns:type="http:///de/tudarmstadt/ukp/dkpro/core/api/coref/type.ecore" xmlns:type6="http:///de/tudarmstadt/ukp/dkpro/core/api/structure/type.ecore" xmlns:constituent="http:///de/tudarmstadt/ukp/dkpro/core/api/syntax/type/constituent.ecore" xmlns:chunk="http:///de/tudarmstadt/ukp/dkpro/core/api/syntax/type/chunk.ecore" xmlns:custom="http:///webanno/custom.ecore" xmi:version="2.0">
            <cas:NULL xmi:id="0"/>
            {annotations_str}{force_single_sentence_str}
            {tagset_tag_str}
            <cas:Sofa xmi:id="1" sofaNum="1" sofaID="_InitialView" mimeType="text" sofaString="{self.text.replace('"', "'")}"/>
            <cas:View sofa="1" members="{("8998 " if force_single_sentence else "")}8999 {" ".join(str(annotations_xmi_ids_start+i) for i, ne in enumerate(self.annotations))}"/>
        </xmi:XMI>
        '''.replace("\n    ","\n").strip()
    def inception_to_xml_file(self, folder="./", filename=None, **inception_to_xml_string_kwargs):
        if not filename:
            filename=self.name
        with open(path.join(folder,filename), "w") as outfile:
            outfile.write(self.inception_to_xml_string(**inception_to_xml_string_kwargs))
    @staticmethod
    def inception_correct_name_encoding_errors(name):
        encoding_errors = {"├д": "ä", "├╝": "ü"}
        for err, corr in encoding_errors.items():
            name = name.replace(err, corr)
        return name
    @staticmethod
    def entity_fishing_from_tag(ef_xml_document_tag, corpus_folder = None) -> Document:
        """Returns a Document from a lxml etree entity-fishing document tag"""
        annotations_tags = ef_xml_document_tag.findall("annotation")
        doc = Document(
            ef_xml_document_tag.attrib["docName"],
            [Annotation.entity_fishing_from_tag(t) for t in annotations_tags]
        )
        if corpus_folder:
            doc.entity_fishing_get_text_from_corpus_folder(corpus_folder)
        return doc
    @staticmethod
    def inception_from_string(name, document_string, named_entity_tag_name="custom:Entityfishinglayer", text_tag_name="cas:Sofa", **named_entity_parser_kwargs) -> Document:
        named_entity_tag_regex = "<"+named_entity_tag_name+r"\W.+?/>"
        tags = re.findall(named_entity_tag_regex, document_string)
        annotations = [Annotation.inception_from_tag_string(t, **named_entity_parser_kwargs) for t in tags if named_entity_tag_name in t]
        text_regex = r'sofaString="(.+?)"'
        text = re.search(text_regex, document_string).group(1)
        return Document(
            Document.inception_correct_name_encoding_errors(name),
            annotations,
            text
        )
    @staticmethod
    def inception_from_file(file_path, document_name=None, **inception_from_string_kwargs) -> Document:
        with open(file_path) as file:
            document_string = file.read()
            if document_name is None:
                document_name = file_path
            return Document.inception_from_string(document_name, document_string, **inception_from_string_kwargs)


# %%