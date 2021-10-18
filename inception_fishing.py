# %%

from lxml import etree

# %%

class NamedEntity:
    def __init__(self, start, end, wikidata_entity_url):
        self.start = start
        self.end = end
        self.wikidata_entity_url = wikidata_entity_url
    def to_inception_tag_string(self, xmi_id):
        """Returns a valid <type3:NamedEntity/> tag string for inception's UIMA CAS XMI (XML 1.1) format"""
        return f'<type3:NamedEntity xmi:id="{xmi_id}" sofa="1" begin="{self.start}" end="{self.end}" identifier="{self.wikidata_entity_url}"/>'
    @staticmethod
    def from_entity_fishing_tag():
        pass
# %%

def get_inception_import_file_content(text, named_entities, named_entities_xmi_ids_start = 9000):
    """Returns a valid inception input file content in UIMA CAS XMI (XML 1.1) format
    
    Note: replaces " characters in text wth ', to simplify handling of XML.
    """
    return f'''
    <?xml version="1.1" encoding="UTF-8"?>
    <xmi:XMI xmlns:pos="http:///de/tudarmstadt/ukp/dkpro/core/api/lexmorph/type/pos.ecore" xmlns:tcas="http:///uima/tcas.ecore" xmlns:xmi="http://www.omg.org/XMI" xmlns:cas="http:///uima/cas.ecore" xmlns:tweet="http:///de/tudarmstadt/ukp/dkpro/core/api/lexmorph/type/pos/tweet.ecore" xmlns:morph="http:///de/tudarmstadt/ukp/dkpro/core/api/lexmorph/type/morph.ecore" xmlns:dependency="http:///de/tudarmstadt/ukp/dkpro/core/api/syntax/type/dependency.ecore" xmlns:type5="http:///de/tudarmstadt/ukp/dkpro/core/api/semantics/type.ecore" xmlns:type8="http:///de/tudarmstadt/ukp/dkpro/core/api/transform/type.ecore" xmlns:type7="http:///de/tudarmstadt/ukp/dkpro/core/api/syntax/type.ecore" xmlns:type2="http:///de/tudarmstadt/ukp/dkpro/core/api/metadata/type.ecore" xmlns:type9="http:///org/dkpro/core/api/xml/type.ecore" xmlns:type3="http:///de/tudarmstadt/ukp/dkpro/core/api/ner/type.ecore" xmlns:type4="http:///de/tudarmstadt/ukp/dkpro/core/api/segmentation/type.ecore" xmlns:type="http:///de/tudarmstadt/ukp/dkpro/core/api/coref/type.ecore" xmlns:type6="http:///de/tudarmstadt/ukp/dkpro/core/api/structure/type.ecore" xmlns:constituent="http:///de/tudarmstadt/ukp/dkpro/core/api/syntax/type/constituent.ecore" xmlns:chunk="http:///de/tudarmstadt/ukp/dkpro/core/api/syntax/type/chunk.ecore" xmlns:custom="http:///webanno/custom.ecore" xmi:version="2.0">
        <cas:NULL xmi:id="0"/>
        {"".join(ne.to_inception_tag_string(named_entities_xmi_ids_start+i) for i, ne in enumerate(named_entities))}
        <type2:TagsetDescription xmi:id="10141" sofa="1" begin="0" end="0" layer="de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity" name="Named Entity tags" input="false"/>
        <cas:Sofa xmi:id="1" sofaNum="1" sofaID="_InitialView" mimeType="text" sofaString="{text.replace('"', "'")}"/>
        <cas:View sofa="1" members="{" ".join(str(named_entities_xmi_ids_start+i) for i, ne in enumerate(named_entities))} 10141"/>
    </xmi:XMI>
    '''.replace("\n    ","\n").strip()


# %%


text = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed
do eiusmod tempor incididunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit
in voluptate velit esse cillum dolore eu fugiat nulla pariatur. \"Excepteur\"
sint occaecat cupidatat non proident, sunt in culpa qui officia 'deserunt' mollit
anim id est laborum."""

named_entities = [
    NamedEntity(28, 39, "http://www.wikidata.org/entity/Q1"),
    NamedEntity(127, 131, "http://www.wikidata.org/entity/Q2"),
    NamedEntity(162, 174, "http://www.wikidata.org/entity/Q3"),
    NamedEntity(162, 174, "http://www.wikidata.org/entity/Q4"),
    NamedEntity(412, 420, "http://www.wikidata.org/entity/Q5")
]

with open("inception-input-test.xmi", "w") as inception_file:
    inception_file.write(get_inception_import_file_content(text, named_entities))


with open("inception-input-test.xmi", "w") as inception_file:
    inception_file.write(get_inception_import_file_content(text, named_entities))
