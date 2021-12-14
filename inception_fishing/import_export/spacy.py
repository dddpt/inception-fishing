from typing import Sequence
from warnings import warn

from spacy.tokens import Doc, Token

from ..Annotation import Annotation
from ..Corpus import Corpus
from ..Document import Document


# Annotation
# ==============================================

def annotation_get_tokens(annotation, spacy_doc) -> Sequence[Token]:
    #print(f"<inception-fishing>.spacy.annotation_get_tokens() for {annotation}")
    tokens = [t for t in spacy_doc if (annotation.start <= t.idx < annotation.end)]
    if any((t.idx+len(t))>annotation.end for t in tokens):
        warn(f"spacy.annotation_get_tokens() tokens {[ f'token({t.text}, idx={t.idx}, len={len(t)}))' for t in tokens if (t.idx+len(t))>annotation.end]} overlapping with Annotation's end: {annotation}")
    if any((t.idx<annotation.start) and ((t.idx+len(t))>annotation.start) for t in spacy_doc):
        warn(f"spacy.annotation_get_tokens() tokens {[f'token({t.text}, idx={t.idx}, len={len(t)}))'  for t in tokens if (t.idx<annotation.start) and ((t.idx+len(t))>annotation.start)]} overlapping with Annotation's start: {annotation}")
    return tokens

# Documents
# ==============================================
    
def document_to_spacy_doc(document, spacy_nlp) -> Doc:
    """Transforms the Document into a spacy doc, adds annotations to tokens."""
    spacy_doc:Doc = spacy_nlp(document.text)
    #print(f"spacy.document_to_spacy_doc() for {document.name}")
    for t in spacy_doc:
        if not t.has_extension("wikidata_entity_id"):
            t.set_extension("wikidata_entity_id", default="")
        if not t.has_extension("wikipedia_page_id"):
            t.set_extension("wikipedia_page_id", default="")
    for a in document.annotations:
        tokens = annotation_get_tokens(a, spacy_doc)
        for t in tokens:
            t._.wikidata_entity_id = a.wikidata_entity_id
            t._.wikipedia_page_id = a.wikipedia_page_id
    return spacy_doc

# Corpus
# ==============================================