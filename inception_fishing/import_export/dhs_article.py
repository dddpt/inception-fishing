
from __future__ import annotations
import re
from typing import Dict, Sequence

from ..Annotation import Annotation
from ..Corpus import Corpus
from ..Document import Document

# Annotation
# ==============================================

def annotations_from_dhs_article():
    pass

# Documents
# ==============================================

def document_from_dhs_article(
    dhs_article,
    dhs_wikidata_wikipedia_links_dict:Dict[str,Dict]|None = None,
    wikipedia_page_name_language = "fr",
    p_text_blocks_separator = "\n",
    non_p_text_blocks_separator = "\n",
):
    """Creates a document from a dhs_article annotating text blocks and text_links 
    
    dhs_wikidata_wikipedia_links should be a dict of dict with structure:
    {dhs-id: dict(
        - item (wikidata id)
        - itemLabel 
        - dhsid
        - namefr (wikipedia name fr)
        - articlefr (wikipedia url fr)
        - namede
        - articlede
        - nameit
        - articleit
        - nameen
        - articleen
        - instanceof
        - instanceofLabel
        - gndid
    )}

    Creates to two types of annotations:
    - annotations for text blocks with extra_fields "dhs_type"->"text_block" and "dhs_html_tag"->html tag name
    - annotations for text links with extra_fields "dhs_type"->"text_link", "dhs_id"->dhs_id and "dhs_href"->internal dhs link
    """
    if dhs_wikidata_wikipedia_links_dict is None:
        dhs_wikidata_wikipedia_links_dict=dict()
    
    annotations:Sequence[Annotation] = []
    dhs_article_id_from_url_regex = re.compile(r"(fr|de|it)/articles/(\d+)/")

    # assembling text blocks as annotations
    text_blocks = dhs_article.parse_text_blocks()
    whole_text = ""
    for tag, text in text_blocks:
        new_whole_text = whole_text+text
        annotations.append(Annotation(
            len(whole_text),
            len(new_whole_text),
            extra_fields = {"dhs_type": "text_block", "dhs_html_tag": tag}
        ))
        if tag =="p":
            whole_text = new_whole_text+p_text_blocks_separator
        else:
            whole_text = new_whole_text+non_p_text_blocks_separator

    # assembling text links as annotations with wikidata ids
    text_links_per_blocks = dhs_article.parse_text_links()
    for i, text_links in enumerate(text_links_per_blocks):
        text_block_start = annotations[i].start
        for text_link in text_links:
            start, end, mention, href = text_link.values()
            # get text link correspondance in wikidata & wikipedia (if present)
            wikidata_entity_url = None
            wikipedia_page_title = None
            dhs_id_match = dhs_article_id_from_url_regex.search(href)
            if dhs_id_match:
                dhs_id = dhs_id_match.group(2)
                wikidata_entry = dhs_wikidata_wikipedia_links_dict.get(dhs_id)
                if wikidata_entry:
                    wikidata_entity_url = wikidata_entry["item"]
                    wikidata_entity_url = wikidata_entity_url if wikidata_entity_url!="" else None
                    wikipedia_page_title = wikidata_entry["name"+wikipedia_page_name_language]
                    wikipedia_page_title = wikipedia_page_title if wikipedia_page_title!="" else None
            annotations.append(Annotation(
                text_block_start+start,
                text_block_start+end,
                wikidata_entity_url = wikidata_entity_url,
                wikipedia_page_title = wikipedia_page_title,
                mention = mention,
                extra_fields={"dhs_type": "text_link", "dhs_href": href, "dhs_id": dhs_id}
            ))
            
    return Document(dhs_article.title, annotations, whole_text)


def document_replace_initial_from_dhs_article(document:Document, dhs_article):
    if dhs_article.initial is not None:
        return document.replace_regex(dhs_article.initial+r"\.", dhs_article.title)
    else:
        return []

def document_annotate_title_from_dhs_article(document:Document, dhs_article):
    wikidata_id, wikipedia_page_title, wiki_links = dhs_article.get_wikidata_links()
    new_annotations = []
    for match in re.finditer(dhs_article.title, document.text):
        start, end = match.span()
        new_annotations.append(Annotation(
            start,
            end,
            wikidata_entity_id=wikidata_id,
            wikipedia_page_id=None, # TODO TODO TODO TODO TODO TODO TODO TODO TODO
            wikipedia_page_title=wikipedia_page_title,
            mention=document.text[start:end],
            extra_fields={
                "origin": "document_annotate_title_from_dhs_article"
            }
        ))
    document.annotations += new_annotations
    return new_annotations



# Corpus
# ==============================================

