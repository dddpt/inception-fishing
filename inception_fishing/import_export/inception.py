from os import path, listdir

import re

from ..Annotation import Annotation
from ..Corpus import Corpus
from ..Document import Document


INCEPTION_DEFAULT_TAGSET_TAG_STR = '<type2:TagsetDescription xmi:id="8999" sofa="1" begin="0" end="0" layer="de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity" name="Named Entity tags" input="false"/>'
inception_being_regex=re.compile(r'begin="(\d+)"')
inception_end_regex=re.compile(r'end="(\d+)"')



def correct_inception_name_encoding_errors(name):
        encoding_errors = {"├д": "ä", "├╝": "ü"}
        for err, corr in encoding_errors.items():
            name = name.replace(err, corr)
        return name

# Annotation
# ==============================================


def annotation_to_tag_string(annotation, xmi_id, tag_name="type3:NamedEntity",
    identifier_attribute_name="identifier",
    grobid_tag_attribute_name="entityfishingtag"
):
    """Returns a valid <type3:NamedEntity/> tag string for inception's UIMA CAS XMI (XML 1.1) format

    Tag & attribute name can be changed
    """
    identifier_attribute = f' {identifier_attribute_name}="{annotation.wikidata_entity_url}" ' if annotation.wikidata_entity_url is not None else ""
    grobid_tag_attribute = f' {grobid_tag_attribute_name}="{annotation.grobid_tag}" ' if annotation.grobid_tag is not None else ""
    return f'<{tag_name} xmi:id="{xmi_id}" sofa="1" begin="{annotation.start}" end="{annotation.end}" {identifier_attribute} {grobid_tag_attribute}/>'


def annotation_from_tag_string(
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
        raise Exception(f"inception.annotation_from_tag_string() missing begin or end attribute in tag: {tag_string}")
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

# Documents
# ==============================================



def document_to_xml_string(document, force_single_sentence=False, annotations_xmi_ids_start = 9000, tagset_tag_str=INCEPTION_DEFAULT_TAGSET_TAG_STR, **named_entity_to_tag_kwargs):
    """Returns a valid inception input file content in UIMA CAS XMI (XML 1.1) format
    
    Note: replaces " characters in text wth ', to simplify handling of XML.
    force_single_sentence=True forces the whole document text to be considered as a single sentence by inception,
    useful when text contains non-sentence-inducing dots (such as abbreviation dots in the DHS)
    """
    annotations_str ="\n            ".join(annotation_to_tag_string(ne, annotations_xmi_ids_start+i, **named_entity_to_tag_kwargs) for i, ne in enumerate(document.annotations))
    force_single_sentence_str = f'\n            <type4:Sentence xmi:id="8998" sofa="1" begin="0" end="{len(document.text)}"/>' if force_single_sentence else ""
    return f'''
    <?xml version="1.1" encoding="UTF-8"?>
    <xmi:XMI xmlns:pos="http:///de/tudarmstadt/ukp/dkpro/core/api/lexmorph/type/pos.ecore" xmlns:tcas="http:///uima/tcas.ecore" xmlns:xmi="http://www.omg.org/XMI" xmlns:cas="http:///uima/cas.ecore" xmlns:tweet="http:///de/tudarmstadt/ukp/dkpro/core/api/lexmorph/type/pos/tweet.ecore" xmlns:morph="http:///de/tudarmstadt/ukp/dkpro/core/api/lexmorph/type/morph.ecore" xmlns:dependency="http:///de/tudarmstadt/ukp/dkpro/core/api/syntax/type/dependency.ecore" xmlns:type5="http:///de/tudarmstadt/ukp/dkpro/core/api/semantics/type.ecore" xmlns:type8="http:///de/tudarmstadt/ukp/dkpro/core/api/transform/type.ecore" xmlns:type7="http:///de/tudarmstadt/ukp/dkpro/core/api/syntax/type.ecore" xmlns:type2="http:///de/tudarmstadt/ukp/dkpro/core/api/metadata/type.ecore" xmlns:type9="http:///org/dkpro/core/api/xml/type.ecore" xmlns:type3="http:///de/tudarmstadt/ukp/dkpro/core/api/ner/type.ecore" xmlns:type4="http:///de/tudarmstadt/ukp/dkpro/core/api/segmentation/type.ecore" xmlns:type="http:///de/tudarmstadt/ukp/dkpro/core/api/coref/type.ecore" xmlns:type6="http:///de/tudarmstadt/ukp/dkpro/core/api/structure/type.ecore" xmlns:constituent="http:///de/tudarmstadt/ukp/dkpro/core/api/syntax/type/constituent.ecore" xmlns:chunk="http:///de/tudarmstadt/ukp/dkpro/core/api/syntax/type/chunk.ecore" xmlns:custom="http:///webanno/custom.ecore" xmi:version="2.0">
        <cas:NULL xmi:id="0"/>
        {annotations_str}{force_single_sentence_str}
        {tagset_tag_str}
        <cas:Sofa xmi:id="1" sofaNum="1" sofaID="_InitialView" mimeType="text" sofaString="{document.text.replace('"', "'")}"/>
        <cas:View sofa="1" members="{("8998 " if force_single_sentence else "")}8999 {" ".join(str(annotations_xmi_ids_start+i) for i, ne in enumerate(document.annotations))}"/>
    </xmi:XMI>
    '''.replace("\n    ","\n").strip()
def document_to_xml_file(document, folder="./", filename=None, **inception_to_xml_string_kwargs):
    if not filename:
        filename=document.name
    with open(path.join(folder,filename), "w") as outfile:
        outfile.write(document_to_xml_string(document, **inception_to_xml_string_kwargs))

def document_from_string(name, document_string, named_entity_tag_name="custom:Entityfishinglayer", text_tag_name="cas:Sofa", **named_entity_parser_kwargs) -> Document:
    named_entity_tag_regex = "<"+named_entity_tag_name+r"\W.+?/>"
    tags = re.findall(named_entity_tag_regex, document_string)
    annotations = [annotation_from_tag_string(t, **named_entity_parser_kwargs) for t in tags if named_entity_tag_name in t]
    text_regex = r'sofaString="(.+?)"'
    text = re.search(text_regex, document_string).group(1)
    return Document(
        correct_inception_name_encoding_errors(name),
        annotations,
        text
    )

def document_from_file(file_path, document_name=None, **inception_from_string_kwargs) -> Document:
    with open(file_path) as file:
        document_string = file.read()
        if document_name is None:
            document_name = file_path
        return document_from_string(document_name, document_string, **inception_from_string_kwargs)

# Corpus
# ==============================================


def corpus_from_directory(
        name,
        dir_path,
        inception_user_name,
        wikipedia_page_titles_and_ids_language = None,
        **document_inception_from_file_kwargs
    ) -> Corpus:

    documents_directories = listdir(dir_path)
    documents = [
        document_from_file(
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
