
from __future__ import annotations
import re
from typing import Dict, Sequence

from ..Annotation import Annotation
from ..Corpus import Corpus
from ..Document import Document

# Annotation
# ==============================================


# Documents
# ==============================================

def document_from_dhs_article(
    dhs_article,
    p_text_blocks_separator = "\n",
    non_p_text_blocks_separator = "\n",
    include_text_links_annotations=True,
    include_title_annotations=True,
    replace_initial_from_dhs_article=True
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
            extra_fields = {"dhs_type": "text_block", "dhs_html_tag": tag, "origin": "dhs_article_text_block"}
        ))
        if tag =="p":
            whole_text = new_whole_text+p_text_blocks_separator
        else:
            whole_text = new_whole_text+non_p_text_blocks_separator
    
    document = Document(dhs_article.title, annotations, whole_text)

    if include_text_links_annotations:
        # assembling text links as annotations with wikidata ids
        text_links_per_blocks = dhs_article.parse_text_links()
        dhs_article.add_wikidata_wikipedia_to_text_links()
        for i, text_links in enumerate(text_links_per_blocks):
            text_block_start = document.annotations[i].start
            for text_link in text_links:
                start = text_link["start"]
                end = text_link["end"]
                mention = text_link["mention"]
                href = text_link["href"]
                # get text link correspondance in wikidata & wikipedia (if present)
                dhs_id_match = dhs_article_id_from_url_regex.search(href)
                if dhs_id_match:
                    dhs_id = dhs_id_match.group(2)
                    document.annotations.append(Annotation(
                        text_block_start+start,
                        text_block_start+end,
                        wikidata_entity_url = text_link.get("wikidata_url"),
                        wikipedia_page_title = text_link.get("wikipedia_page_title"),
                        mention = mention,
                        extra_fields={"dhs_type": "text_link", "dhs_href": href, "dhs_id": dhs_id, "origin": "dhs_article_text_links"}
                    ))
    
    if replace_initial_from_dhs_article:
        document_annotate_title_from_dhs_article(document, dhs_article)
    if include_title_annotations:
        document_annotate_title_from_dhs_article(document, dhs_article)
    return document


def document_replace_initial_from_dhs_article(document:Document, dhs_article):
    if dhs_article.initial is not None:
        return document.replace_regex(dhs_article.initial+r"\.", dhs_article.title)
    else:
        return []

def document_annotate_title_from_dhs_article(document:Document, dhs_article):
    """mostly works after document_replace_initial_from_dhs_article"""
    wikidata_url, wikipedia_page_title, wiki_links = dhs_article.get_wikidata_links()
    new_annotations = []
    for match in re.finditer(dhs_article.title, document.text):
        start, end = match.span()
        new_annotations.append(Annotation(
            start,
            end,
            wikidata_entity_url=wikidata_url,
            wikipedia_page_id=None,
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

