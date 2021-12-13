
from spacy.tokens import Token

from .Annotation import Annotation
from .Corpus import Corpus
from .Document import Document

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

# Annotation
# ==============================================

# Documents
# ==============================================

def document_to_conllu_tsv(document, spacy_nlp,
        language="fr", date="1918-11-08", newspaper= "DHS",
        **spacy_token_to_tsv_line_kwargs
    ) -> str:
    intro = f"# language = {language}									\n" + \
            f"# newspaper = {newspaper}									\n" + \
            f"# date = {date}									\n" + \
            f"# document_id = {document.name}									\n"
    sentence_intro = f"# segment_iiif_link = _									\n"

    spacy_doc = document.spacy_to_doc(spacy_nlp)
    sentence_tsv_lines = sentence_intro + "\n".join([
        spacy_token_to_tsv_line(t, **spacy_token_to_tsv_line_kwargs)
        for t in spacy_doc
    ])
        
    return intro+sentence_tsv_lines[:-1]+"EndOfLine|EndOfParagraph"

# Corpus
# ==============================================

def corpus_to_conllu_tsv(corpus, filepath, spacy_nlp, **document_kwargs):
    doc_tsv_separator = "\n"+(2*"									\n")
    alphabetic_ordered_docs = sorted(corpus.documents, key= lambda d: d.name)
    tsv_docs = [document_to_conllu_tsv(d, spacy_nlp, **document_kwargs) for d in alphabetic_ordered_docs]

    tsv_content = "\t".join(clef_hipe_scorer_tsv_columns)+"\n"+doc_tsv_separator.join(tsv_docs)
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(tsv_content)
    return tsv_content