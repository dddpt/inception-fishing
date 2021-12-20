
# %%

OVERLAP_START = "overlap_start"
OVERLAP_END = "overlap_end"
OVERLAP_INCLUDES = "overlap_includes"
OVERLAP_IS_INCLUDED = "overlap_is_included"
OVERLAP_IDENTICAL = "same_span"
OVERLAP_NONE = "no_overlap"
def get_spans_overlap_status(starta, enda, startb, endb):
    """Gives whether the two spans overlap
    
    Possible return values:
    - OVERLAP_START = "overlap_start"
    - OVERLAP_END = "overlap_end"
    - OVERLAP_INCLUDES = "overlap_includes"
    - OVERLAP_IS_INCLUDED = "overlap_is_included"
    - OVERLAP_IDENTICAL = "same_span"
    - OVERLAP_NONE = "no_overlap"
    """
    if enda<starta:
        raise Exception(f"inception_fishing.utils.get_spans_overlap_status(): span a ends before its starts: error. starta={starta}, enda={enda}")
    if endb<startb:
        raise Exception(f"inception_fishing.utils.get_spans_overlap_status(): span b ends before its starts: error. startb={startb}, endb={endb}")
    
    if starta==startb and enda==endb:
        return OVERLAP_IDENTICAL


    b_is_around_a = (startb <= starta and endb>enda) or (startb < starta and endb>=enda)
    if b_is_around_a:
        return OVERLAP_IS_INCLUDED

    a_is_around_b = (starta <= startb and enda>endb) or (starta < startb and enda>=endb)
    if a_is_around_b:
        return OVERLAP_INCLUDES

    b_starts_in_a = (startb >= starta) and (startb < enda) 
    b_ends_in_a = (endb > starta) and (endb <= enda)
    if (not b_starts_in_a) and b_ends_in_a:
        return OVERLAP_START
    if b_starts_in_a and not b_ends_in_a:
        return OVERLAP_END

    return OVERLAP_NONE
    

def do_spans_intersect(starta, enda, startb, endb, inclusion_is_intersection=False):
    """Tells whether 2 spans intersect
    
    if inclusion_is_intersection=True, "a same span as b", "a includes b", and
    "b includes a" count as intersection"""
    overlap_status = get_spans_overlap_status(starta, enda, startb, endb)
    if overlap_status in [OVERLAP_START, OVERLAP_END]:
        return True
    if inclusion_is_intersection and overlap_status in [OVERLAP_INCLUDES, OVERLAP_IS_INCLUDED, OVERLAP_IDENTICAL]:
        return True
    return False


# %%

def get_attributes_string(class_name, object_dict):
    """Unimportant utility function to format __str__() and __repr()"""
    return f"""{class_name}({', '.join([
        f"{str(k)}: {str(v)}"
        for k, v in object_dict.items()
        if v is not None
    ])})"""

# %%

wikidata_entity_base_url = "http://www.wikidata.org/entity/"



# %%

ANNOTATION_ORIGIN_DHS_ARTICLE_TITLE = "dhs_article_title"
ANNOTATION_ORIGIN_DHS_ARTICLE_TEXT_BLOCK = "dhs_article_text_block"
ANNOTATION_ORIGIN_DHS_ARTICLE_TEXT_LINK = "dhs_article_text_links"
ANNOTATION_ORIGIN_ENTITY_FISHING = "entity_fishing"

