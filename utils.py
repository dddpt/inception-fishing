
# %%

import re

from spacy.tokens import Token

# %%

def get_attributes_string(class_name, object_dict):
    """Unimportant utility function to format __str__() and __repr()"""
    return f"""{class_name}({', '.join([
        f"{str(k)}: {str(v)}"
        for k, v in object_dict.items()
    ])})"""

# %%

wikidata_entity_base_url = "http://www.wikidata.org/entity/"



default_tsv_col_to_token_extension = {
    "NEL-LIT": "wikidata_entity_id"
}
clef_hipe_scorer_tsv_data_columns_with_default= {
    "NE-COARSE-LIT": "O",
    "NE-COARSE-METO": "O",
    "NE-FINE-LIT": "O",
    "NE-FINE-METO": "O",
    "NE-FINE-COMP": "O",
    "NE-NESTED": "O",
    "NEL-LIT": "-",
    "NEL-METO": "-",
    "MISC": "-"
}
clef_hipe_scorer_tsv_columns = ["TOKEN"]+list(clef_hipe_scorer_tsv_data_columns_with_default.keys())


def spacy_token_to_tsv_line(
        token:Token,
        tsv_columns = clef_hipe_scorer_tsv_data_columns_with_default,
        tsv_col_to_token_extension=default_tsv_col_to_token_extension
    ):
    line = ""+token.text
    for col, default in tsv_columns.items():
        line += "\t"
        if col in tsv_col_to_token_extension and token._.get(tsv_col_to_token_extension[col]) is not None:
            line += token._.get(tsv_col_to_token_extension[col])
        else:
            line += default
    return line