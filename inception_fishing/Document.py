

from __future__ import annotations
import re
from typing import Sequence, Dict
from warnings import warn

from .Annotation import Annotation
from .utils import get_attributes_string

# %%


# %%


class Document:
    def __init__(self, name:str, annotations, text = "", extra_fields=dict()):
        self.name:str = name
        self.annotations:Sequence[Annotation] = annotations
        self.text:str = text
        self.extra_fields:Dict = extra_fields
    
    def replace_span(self, start, end, replacement):
        """Replaces given span in Document text
        
        Throws an exception if span intersects with an existing annotation

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
            #a_starts_in_replacement = (a.start >= start) and (a.start <end) 
            #a_ends_in_replacement = (a.end > start) and (a.end > end)
            replacement_starts_in_a = (start >= a.start) and (start < a.end) 
            replacement_ends_in_a = (end > a.start) and (end <= a.end)
            replacement_is_around_a = (start <= a.start and end>a.end) or (start < a.start and end>=a.end)
            # print(f"start_between: {start_between}, end_between: {end_between}")
            if replacement_is_around_a:
                warn(f"Document.replace_span({start}, {end}, {replacement}) for doc {self.name} englobes annotation {a}. This annotation is removed from document.")
                annotations_to_remove.add(a)
            elif replacement_starts_in_a != replacement_ends_in_a and start!=end:
                raise Exception(f"Document.replace_span({start}, {end}, {replacement}) for doc {self.name} intersects with {a}. Text:\n{self.text}")
            else:
                if a.start >= end:
                    a.start += annotation_indexation_shift
                if a.end >= end:
                    a.end += annotation_indexation_shift
        self.annotations = [
            a for a in self.annotations
            if a not in annotations_to_remove
        ]
        self.text=new_text
        return (start, old_span_content, replacement, annotation_indexation_shift)

    def replace_regex(self, to_replace_regex, replacement):
        """Replaces the given regex in the text

        returns the list of incremental matches tuples from replace_span(), see replace_span() doc

        Not that incremental matches' starts are incrementally computed and do not directly correspond to the new Document text.
        If you want to re-modify the replacements, you have to do so in reverse order for starts to match.
        """
        match = re.search(to_replace_regex, self.text)
        incremental_matches = []
        while match is not None:
            start, end = match.span()
            incremental_matches.append((start, self.text[start:end]))
            incremental_matches.append(self.replace_span(start, end, replacement))
            match = re.search(to_replace_regex, self.text)
        return incremental_matches
    def reverse_replace_span(self, incremental_match):
        """Reverse a single replace_span() call from its incremental_match return
        
        see replace_span() doc
        """
        start, original_content, replacement, shift = incremental_match
        self.replace_span(start, start+len(replacement), original_content)
    def reverse_consecutive_replace_span(self, incremental_matches):
        """Reverse a consecutive list of replace_span() call from their incremental_matches list
        
        typically used to reverse a replace_regex() call
        """
        return [
            self.reverse_replace_span(incremental_match)
            for incremental_match in incremental_matches.reverse()
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