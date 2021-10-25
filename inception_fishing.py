# %%

from os import listdir, path

# %%
INCEPTION_DEFAULT_TAGSET_TAG_STR = '<type2:TagsetDescription xmi:id="8999" sofa="1" begin="0" end="0" layer="de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity" name="Named Entity tags" input="false"/>'


def get_attributes_string(class_name, object_dict):
    """Unimportant utility function to format __str__() and __repr()"""
    return f"""{class_name}({', '.join([
        f"{str(k)}: {str(v)}"
        for k, v in object_dict.items()
    ])})"""

# %%

class Corpus:
    def __init__(self, name, documents):
        self.name = name
        self.documents = documents
    @staticmethod
    def entity_fishing_from_tag_and_corpus(ef_xml_root_tag, corpus_folder = None):
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

class Document:
    def __init__(self, name, named_entities, text = ""):
        self.name = name
        self.named_entities = named_entities
        self.text = text
        
    def entity_fishing_get_text_from_corpus_folder(self, corpus_folder):
        text_file_path = path.join(corpus_folder, self.name) if corpus_folder else self.name
        with open(text_file_path) as f:
                self.text = f.read()
                return self.text
    def __repr__(self):
        return get_attributes_string("Document",self.__dict__)

    def inception_to_xml_string(self, force_single_sentence=False, named_entities_xmi_ids_start = 9000, tagset_tag_str=INCEPTION_DEFAULT_TAGSET_TAG_STR, **named_entity_to_tag_kwargs):
        """Returns a valid inception input file content in UIMA CAS XMI (XML 1.1) format
        
        Note: replaces " characters in text wth ', to simplify handling of XML.
        force_single_sentence=True forces the whole document text to be considered as a single sentence by inception,
        useful when text contains non-sentence-inducing dots (such as abbreviation dots in the DHS)
        """
        named_entities_str ="\n            ".join(ne.inception_to_tag_string(named_entities_xmi_ids_start+i, **named_entity_to_tag_kwargs) for i, ne in enumerate(self.named_entities))
        force_single_sentence_str = f'\n            <type4:Sentence xmi:id="8998" sofa="1" begin="0" end="{len(self.text)}"/>' if force_single_sentence else ""
        return f'''
        <?xml version="1.1" encoding="UTF-8"?>
        <xmi:XMI xmlns:pos="http:///de/tudarmstadt/ukp/dkpro/core/api/lexmorph/type/pos.ecore" xmlns:tcas="http:///uima/tcas.ecore" xmlns:xmi="http://www.omg.org/XMI" xmlns:cas="http:///uima/cas.ecore" xmlns:tweet="http:///de/tudarmstadt/ukp/dkpro/core/api/lexmorph/type/pos/tweet.ecore" xmlns:morph="http:///de/tudarmstadt/ukp/dkpro/core/api/lexmorph/type/morph.ecore" xmlns:dependency="http:///de/tudarmstadt/ukp/dkpro/core/api/syntax/type/dependency.ecore" xmlns:type5="http:///de/tudarmstadt/ukp/dkpro/core/api/semantics/type.ecore" xmlns:type8="http:///de/tudarmstadt/ukp/dkpro/core/api/transform/type.ecore" xmlns:type7="http:///de/tudarmstadt/ukp/dkpro/core/api/syntax/type.ecore" xmlns:type2="http:///de/tudarmstadt/ukp/dkpro/core/api/metadata/type.ecore" xmlns:type9="http:///org/dkpro/core/api/xml/type.ecore" xmlns:type3="http:///de/tudarmstadt/ukp/dkpro/core/api/ner/type.ecore" xmlns:type4="http:///de/tudarmstadt/ukp/dkpro/core/api/segmentation/type.ecore" xmlns:type="http:///de/tudarmstadt/ukp/dkpro/core/api/coref/type.ecore" xmlns:type6="http:///de/tudarmstadt/ukp/dkpro/core/api/structure/type.ecore" xmlns:constituent="http:///de/tudarmstadt/ukp/dkpro/core/api/syntax/type/constituent.ecore" xmlns:chunk="http:///de/tudarmstadt/ukp/dkpro/core/api/syntax/type/chunk.ecore" xmlns:custom="http:///webanno/custom.ecore" xmi:version="2.0">
            <cas:NULL xmi:id="0"/>
            {named_entities_str}{force_single_sentence_str}
            {tagset_tag_str}
            <cas:Sofa xmi:id="1" sofaNum="1" sofaID="_InitialView" mimeType="text" sofaString="{self.text.replace('"', "'")}"/>
            <cas:View sofa="1" members="{("8998 " if force_single_sentence else "")}8999 {" ".join(str(named_entities_xmi_ids_start+i) for i, ne in enumerate(self.named_entities))}"/>
        </xmi:XMI>
        '''.replace("\n    ","\n").strip()
    def inception_to_xml_file(self, folder="./", filename=None, **inception_to_xml_string_kwargs):
        if not filename:
            filename=self.name
        with open(path.join(folder,filename), "w") as outfile:
            outfile.write(self.inception_to_xml_string(**inception_to_xml_string_kwargs))
    @staticmethod
    def entity_fishing_from_tag(ef_xml_document_tag, corpus_folder = None):
        """Returns a Document from a lxml etree entity-fishing document tag"""
        named_entities_tags = ef_xml_document_tag.findall("annotation")
        doc = Document(
            ef_xml_document_tag.attrib["docName"],
            [NamedEntity.entity_fishing_from_tag(t) for t in named_entities_tags]
        )
        if corpus_folder:
            doc.entity_fishing_get_text_from_corpus_folder(corpus_folder)
        return doc

wikidata_entity_base_url = "http://www.wikidata.org/entity/"
class NamedEntity:
    def __init__(self, start, end, wikidata_entity_url=None):
        """Creates NamedEntity, one of end or length must be given, length has priority over end if both given"""
        self.start = start
        self.end = end
        self.wikidata_entity_url = wikidata_entity_url
    @property
    def length(self):
        return self.end-self.start
    @length.setter
    def set_length(self, new_length):
        self.end = self.start+new_length
    def inception_to_tag_string(self, xmi_id, tag_name="type3:NamedEntity", identifier_attribute_name="identifier"):
        """Returns a valid <type3:NamedEntity/> tag string for inception's UIMA CAS XMI (XML 1.1) format

        Tag & attribute name can be changed
        """
        return f'<{tag_name} xmi:id="{xmi_id}" sofa="1" begin="{self.start}" end="{self.end}" {identifier_attribute_name}="{self.wikidata_entity_url}"/>'
    def __repr__(self):
        return get_attributes_string("NamedEntity",self.__dict__)
    @staticmethod
    def entity_fishing_from_tag(ef_xml_annotation_tag):
        """
        
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
        return NamedEntity(offset, offset+length, wikidata_entity_base_url+wikidata_id)
        
# %%

