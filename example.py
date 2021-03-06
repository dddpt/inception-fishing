from os import path

from lxml import etree

from inception_fishing import *

# %% Testing writing inception XML input 

text = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed
do eiusmod tempor incididunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit
in voluptate velit esse cillum dolore eu fugiat nulla pariatur. \"Excepteur\"
sint occaecat cupidatat non proident, sunt in culpa qui officia 'deserunt' mollit
anim id est laborum."""

named_entities = [
    Annotation(28, 39, "http://www.wikidata.org/entity/Q1"),
    Annotation(127, 131, "http://www.wikidata.org/entity/Q2"),
    Annotation(162, 174, "http://www.wikidata.org/entity/Q3"),
    Annotation(162, 174, "http://www.wikidata.org/entity/Q4"),
    Annotation(412, 420, "http://www.wikidata.org/entity/Q5")
]
doc = Document("test", named_entities, text)

#doc.inception_to_xml_file()

# %%

language = "fr"

entity_fishing_corpus_folder = f"../entity-fishing/data/corpus/corpus-long/dhs-training-{language}/"
entity_fishing_annotation_output_file = path.join(entity_fishing_corpus_folder,f"dhs-training-{language}.xml")
entity_fishing_corpus_rawtext_folder = path.join(entity_fishing_corpus_folder, "RawText/")

with open(entity_fishing_annotation_output_file) as entity_fishing_xml_file:
    entity_fishing_xml_root = etree.parse(entity_fishing_xml_file).getroot()
    corpus = entity_fishing.corpus_from_tag_and_corpus(entity_fishing_xml_root, entity_fishing_corpus_rawtext_folder)
# %%

inception_tagset_tag_str = '<type2:TagsetDescription xmi:id="1780" sofa="1" begin="0" end="0" layer="webanno.custom.Entityfishinglayer" name="Grobid-NER" input="false"/>'

inception_import_folder = "../inception-import-xml/"
for d in corpus.documents:
    print(f"doing Document  {d.name}")
    inception.document_to_xml_file(d, inception_import_folder, force_single_sentence=True, tagset_tag_str=inception_tagset_tag_str, tag_name="custom:Entityfishinglayer", identifier_attribute_name="wikidataidentifier")
# %%
