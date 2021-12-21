
from __future__ import annotations
from warnings import warn
import re
from typing import Dict, Sequence

from ..Annotation import Annotation
from ..Corpus import Corpus
from ..Document import Document
from ..utils import *

from .entity_fishing import document_named_entity_linking
from .get_dhs_id_from_wikidata_id import get_infos_from_wikidata_id
from .wikipedia import document_set_annotations_page_titles_and_ids

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
            extra_fields = {"dhs_type": "text_block", "dhs_html_tag": tag, "origin": ANNOTATION_ORIGIN_DHS_ARTICLE_TEXT_BLOCK}
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
        annotations_to_include = set([ANNOTATION_ORIGIN_DHS_ARTICLE_TEXT_BLOCK, ANNOTATION_ORIGIN_DHS_ARTICLE_TEXT_LINK, ANNOTATION_ORIGIN_DHS_ARTICLE_TITLE])
       
        for i, text_links in enumerate(text_links_per_blocks):
            text_block_start = document.annotations[i].start
            for text_link in text_links:
                if "origin" not in text_link or text_link["origin"] in (annotations_to_include):
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
                            extra_fields={"dhs_type": "text_link", "dhs_href": href, "dhs_id": dhs_id, "origin": ANNOTATION_ORIGIN_DHS_ARTICLE_TEXT_LINK}
                        ))
    
    if replace_initial_from_dhs_article:
        document_replace_initial_from_dhs_article(document, dhs_article)
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
        skip = any(a.start==start and a.end==end and a.wikidata_entity_url==wikidata_url for a in document.annotations)
        if not skip:
            new_annotations.append(Annotation(
                start,
                end,
                wikidata_entity_url=wikidata_url,
                wikipedia_page_id=None,
                wikipedia_page_title=wikipedia_page_title,
                mention=document.text[start:end],
                extra_fields={
                    "origin": ANNOTATION_ORIGIN_DHS_ARTICLE_TITLE
                }
            ))
    document.annotations += new_annotations
    return new_annotations

def document_get_text_block_annotations(document:Document):
    text_blocks = [a for a in document.annotations if a.extra_fields.get("origin")==ANNOTATION_ORIGIN_DHS_ARTICLE_TEXT_BLOCK]
    text_blocks.sort(key = lambda x: x.start)
    return text_blocks

def document_get_entity_fishing_annotations(document:Document):
    entity_fishing_annotations = [a for a in document.annotations if a.extra_fields.get("origin")==ANNOTATION_ORIGIN_ENTITY_FISHING]
    entity_fishing_annotations.sort(key = lambda x: x.start)
    return entity_fishing_annotations

def document_reintegrate_annotations_into_dhs_article(document:Document, dhs_article):
    """add annotations back into dhs_article.text_links
    
    Skips annotation that are from dhs_article (title, text_links, text_blocks)
    
    each text_link has fields:
    - start: start of annotation in text_block
    - end: end of annotation in text_block
    - mention: content of the link
    - href: link to article
    - dhsid: dhsid
    - wiki: object with links to wikidata and wikipedias.
    - origin: a.extra_fields.get("origin"), most often "entity_fishing"
    - annotation: the 6 Annotation field: wikidata_entity_id, wikipedia_page_id, wikipedia_page_title, wikidata_entity_url, grobid_tag, extra_fields
    """

    #print(f"{len(document.annotations)} annotations to reintegrate into {dhs_article.title}")
    text_blocks = document_get_text_block_annotations(document)
    annotations_to_avoid = set([ANNOTATION_ORIGIN_DHS_ARTICLE_TEXT_BLOCK, ANNOTATION_ORIGIN_DHS_ARTICLE_TEXT_LINK, ANNOTATION_ORIGIN_DHS_ARTICLE_TITLE])
    for i, tb in enumerate(text_blocks):
        tb.start
        for a in document.annotations:
            overlap_status = get_spans_overlap_status(a.start, a.end, tb.start, tb.end)
            if overlap_status in [OVERLAP_START, OVERLAP_END, OVERLAP_INCLUDES]:
                warn(
                    f"inception_fishing.import_export.dhs_article.document_reintegrate_annotations_into_dhs_article() problem for document '{document.name}':" + \
                    f" annotation overlapping with text_block.\nannotation: {a}\ntext_block: {tb}"
                )
            #if a.start >= tb.start and a.start<tb.end and \
            elif overlap_status in [OVERLAP_IS_INCLUDED, OVERLAP_IDENTICAL] and a.extra_fields.get("origin") not in annotations_to_avoid:
                wiki_infos = get_infos_from_wikidata_id(a.wikidata_entity_id)
                text_link = {
                    "start": a.start-tb.start,
                    "end": a.end-tb.start,
                    "mention": a.mention,
                    "origin": a.extra_fields.get("origin"),
                    "annotation": {
                        "wikidata_entity_id": a.wikidata_entity_id,
                        "wikipedia_page_id": a.wikipedia_page_id,
                        "wikipedia_page_title": a.wikipedia_page_title,
                        "wikidata_entity_url": a.wikidata_entity_url,
                        "grobid_tag": a.grobid_tag,
                        "extra_fields": a.extra_fields
                    }
                }
                if wiki_infos is not None:
                    text_link["href"] = dhs_article.language+"/articles/" + wiki_infos["dhsid"]
                    text_link["dhsid"] = wiki_infos["dhsid"]
                    text_link["wiki"] = wiki_infos
                else:
                    pass#print(f"wiki_infos is None for wikidata_id: {a.wikidata_entity_id}\nannotation: {a}\n{dhs_article.title} with id: {dhs_article.id}")
                dhs_article.text_links[i].append(text_link)
            elif overlap_status not in [OVERLAP_NONE]:
                pass#print(f" unwanted annotation with overlap_status: {overlap_status}, annotation: {a}")

    return dhs_article

# DhsArticle
# ==============================================

def link_entities(dhs_article, verbose=True, **entity_linking_kwargs):
    """Does the whole process of sending a dhs_article through entity_fishing and reintegrating the obtained annotations
    
    Modify article in place, returns it anyway
    """

    if verbose:
        print(f"Parsing article {dhs_article.id} {dhs_article.title} in {dhs_article.language}. ", end = '')

    dhs_article.parse_text_blocks()
    dhs_article.parse_text_links()
    dhs_article.add_wikidata_url_wikipedia_page_title()
    dhs_article.add_wikidata_wikipedia_to_text_links()

    d = document_from_dhs_article(dhs_article)
    document_set_annotations_page_titles_and_ids(d, dhs_article.language)
    linked_doc = document_named_entity_linking(d, dhs_article.language, **entity_linking_kwargs)

    if verbose:
        print(f"Found {len(document_get_entity_fishing_annotations(linked_doc))} annotations. ", end = '')
    

    document_reintegrate_annotations_into_dhs_article(linked_doc, dhs_article)

    if verbose:
        print(f"Reintegration as text_links done")
    return dhs_article


def link_dhs_articles(dhs_articles:Sequence, **entity_linking_kwargs):
    """Generator for link_entities()"""
    for a in dhs_articles:
        yield link_entities(a, **entity_linking_kwargs)

