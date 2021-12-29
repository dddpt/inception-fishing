

from __future__ import annotations
import re
from typing import Sequence, Dict
from warnings import warn

from .Annotation import Annotation
from .utils import *

# %%


# %%
INTERSECTION_BEHAVIOUR_SKIP_REPLACEMENT = "skip_replacement"
INTERSECTION_BEHAVIOUR_REMOVE_ANNOTATION = "remove_annotation"

class Document:
    def __init__(self, name:str, annotations, text = "", extra_fields=dict()):
        self.name:str = name
        self.annotations:Sequence[Annotation] = annotations
        self.text:str = text
        self.extra_fields:Dict = extra_fields
    
    def replace_span(self, start, end, replacement, intersection_behaviour=None, warn_on_annotation_removal=True):
        """Replaces given span in Document text
        
        if replacement intersects with an annotation, 3 possible intersection_behaviours:
        - intersection_behaviour==INTERSECTION_BEHAVIOUR_SKIP_REPLACEMENT: give up the replacement
        - intersection_behaviour==INTERSECTION_BEHAVIOUR_REMOVE_ANNOTATION: remove the intersecting annotations
        - intersection_behaviour is other: Throws an exception if span intersects with an existing annotation

        annotations that are fully included (and hence not intersecting) in replacement are removed.

        returns an incremental match, a tuple consisting of:
        0) start
        1) span original content
        2) replacement
        3) annotation_indexation_shift
        """
        replaced_length = end-start
        replacement_length=len(replacement)
        annotation_indexation_shift = replacement_length - replaced_length
        old_span_content = self.text[start:end]
        new_text = self.text[:start] + replacement + self.text[end:]
        annotations_to_remove = set()
        for a in self.annotations:
            overlap_status = get_spans_overlap_status(a.start, a.end, start, end)
            # print(f"start_between: {start_between}, end_between: {end_between}")
            # replacement is around annotation: remove annotation
            if overlap_status==OVERLAP_IS_INCLUDED: 
                if warn_on_annotation_removal:
                    warn(f"Document.replace_span({start}, {end}, {replacement}) for doc {self.name} englobes annotation {a}. This annotation is removed from document.")
                annotations_to_remove.add(a)
            # replacement intersects with annotation: intersection_behaviour
            elif overlap_status in [OVERLAP_START, OVERLAP_END]: 
                # intersection_behaviour remove annotation
                if intersection_behaviour == INTERSECTION_BEHAVIOUR_REMOVE_ANNOTATION:
                    if warn_on_annotation_removal:
                        warn(f"Document.replace_span({start}, {end}, {replacement}) for doc {self.name} intersects annotation {a}. This annotation is removed from document per {intersection_behaviour}.")
                    annotations_to_remove.add(a)
                # intersection_behaviour skip replacement
                elif intersection_behaviour == INTERSECTION_BEHAVIOUR_SKIP_REPLACEMENT:        
                    return (start, old_span_content, old_span_content, 0)
                # intersection_behaviour None: error
                else:
                    raise Exception(f"Document.replace_span({start}, {end}, {replacement}) for doc {self.name} intersects with {a}. Text:\n{self.text}")
        # remove annotations that need to be
        self.annotations = [
            a for a in self.annotations
            if a not in annotations_to_remove
        ]
        # shift annotations that are after the replacements
        for a in self.annotations:
            if a.start >= end:
                a.start += annotation_indexation_shift
            if a.end >= end:
                a.end += annotation_indexation_shift
        self.text=new_text
        return (start, old_span_content, replacement, annotation_indexation_shift)

    def replace_regex(self, to_replace_regex, replacement, **replace_span_kwargs):
        """Replaces the given regex in the text

        returns the list of incremental matches tuples from replace_span(), see replace_span() doc

        Not that incremental matches' starts are incrementally computed and do not directly correspond to the new Document text.
        If you want to re-modify the replacements, you have to do so in reverse order for starts to match.
        """
        match = re.search(to_replace_regex, self.text)
        incremental_matches = []
        search_start=0
        while match is not None:
            start, end = match.span()    
            start += search_start
            end += search_start
            #incremental_matches.append((start, self.text[start:end]))
            incremental_matches.append(self.replace_span(start, end, replacement, **replace_span_kwargs))
            search_start = start + len(replacement)
            match = re.search(to_replace_regex, self.text[search_start:])
        return incremental_matches
    def reverse_replace_span(self, incremental_match, **replace_span_kwargs):
        """Reverse a single replace_span() call from its incremental_match return
        
        see replace_span() doc
        """
        start, original_content, replacement, shift = incremental_match
        self.replace_span(start, start+len(replacement), original_content, **replace_span_kwargs)
    def reverse_consecutive_replace_span(self, incremental_matches, **replace_span_kwargs):
        """Reverse a consecutive list of replace_span() call from their incremental_matches list
        
        typically used to reverse a replace_regex() call
        """
        #print(f"Doc.reverse_consecutive_replace_span() incremental_matches={incremental_matches.reverse()}")
        reversed_incremental_matches = [im for im in incremental_matches]
        reversed_incremental_matches.reverse()
        if replace_span_kwargs.get("intersection_behaviour")==INTERSECTION_BEHAVIOUR_SKIP_REPLACEMENT:
            replace_span_kwargs["intersection_behaviour"] = None
        return [
            self.reverse_replace_span(incremental_match, **replace_span_kwargs)
            for incremental_match in reversed_incremental_matches
        ]
    def update_mentions(self):
        for a in self.annotations:
            a.set_mention(self)
    def get_annotations_nesting_level(self):
        nesting_levels = {
            a: 0
            for a in self.annotations
        }
        if len(self.annotations) <= 1:
            return nesting_levels
        self.annotations.sort(key=lambda a: a.start)
        for i,a in enumerate(self.annotations[:-1]):
            for a2 in self.annotations[i+1:]:
                if a2.start<a.end:
                    #print(f"NESTING: {a2}\ninsid\n{a}\n")
                    nesting_levels[a2] = nesting_levels[a2]+1
                else:
                    break
        return nesting_levels
    def remove_nested_annotations(self):
        nesting_levels = self.get_annotations_nesting_level()
        self.annotations = [a for a in self.annotations if nesting_levels[a]==0]
    def filter_annotations(self, filter):
        self.annotations = [a for a in self.annotations if filter(a)]
    def __repr__(self):
        return get_attributes_string("Document",self.__dict__)
    def __deepcopy__(self) -> Document:
        return Document(
            self.name,
            [a.__deepcopy__() for a in self.annotations],
            self.text
        )

# %%