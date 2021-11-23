
# %%

import re

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

