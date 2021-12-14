
# %%


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



