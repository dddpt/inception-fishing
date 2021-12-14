
from __future__ import annotations
from os import path, listdir
from typing import Sequence

import xml.etree.ElementTree as ET

from .Document import Document
from .utils import get_attributes_string

# %%

class Corpus:
    def __init__(self, name, documents):
        self.name:str = name
        self.documents:Sequence[Document] = documents

    def __repr__(self):
        return get_attributes_string(
            "Corpus",
            {"name": self.name,
            "documents": [d.name for d in self.documents]}
        )
    def __deepcopy__(self) -> Corpus:
        return Corpus(
            self.name,
            [d.__deepcopy__() for d in self.documents],
        )
# %%