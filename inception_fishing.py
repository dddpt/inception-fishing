# %%

from __future__ import annotations
from os import path, listdir
import re
from typing import Sequence

from pandas import isnull
import xml.etree.ElementTree as ET

from .wiki import get_wikipedia_page_titles_and_ids_from_wikidata_ids

# %%
INCEPTION_DEFAULT_TAGSET_TAG_STR = '<type2:TagsetDescription xmi:id="8999" sofa="1" begin="0" end="0" layer="de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity" name="Named Entity tags" input="false"/>'
inception_being_regex=re.compile(r'begin="(\d+)"')
inception_end_regex=re.compile(r'end="(\d+)"')

def get_attributes_string(class_name, object_dict):
    """Unimportant utility function to format __str__() and __repr()"""
    return f"""{class_name}({', '.join([
        f"{str(k)}: {str(v)}"
        for k, v in object_dict.items()
    ])})"""

# %%

wikidata_entity_base_url = "http://www.wikidata.org/entity/"


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

class Corpus:
    def __init__(self, name, documents):
        self.name:str = name
        self.documents:Sequence[Document] = documents
            
    def get_annotations_wikipedia_page_titles_and_ids(self, language):
        """Only works for corpus with <=50 unique entities in annotations"""
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

    def entity_fishing_to_xml_tag(self, **document_kwargs):
        corpus_tag = ET.Element(self.name+".entityAnnotation")
        for d in self.documents:
            corpus_tag.append(d.entity_fishing_to_xml_tag(**document_kwargs))
        return corpus_tag

    def entity_fishing_to_xml_file(self, filepath, **document_kwargs):
        intro_str = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'
        corpus_tag = self.entity_fishing_to_xml_tag(**document_kwargs)

        ET.ElementTree(corpus_tag).write(filepath, encoding="utf-8")
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(intro_str+"\n"+content)

    @staticmethod
    def entity_fishing_from_tag_and_corpus(ef_xml_root_tag, corpus_folder = None) -> Corpus:
        """Returns a Corpus object from a lxml.etree tag (the root of an EF evaluation XML output) and the EF corpus folder"""
        name = ef_xml_root_tag.tag.replace(".entityAnnotation", "")
        document_tags = ef_xml_root_tag.findall("document")
        return Corpus(name, [Document.entity_fishing_from_tag(t, corpus_folder) for t in document_tags])
    def __repr__(self):
        return get_attributes_string(
            "Corpus",
            {"name": self.name,
            "documents": [d.name for d in self.documents]}
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