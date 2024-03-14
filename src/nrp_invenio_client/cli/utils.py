def extract_alias(query):
    save_to_alias = [q for q in query if q.startswith('@')]
    query = [q for q in query if not q.startswith('@')]
    if save_to_alias and len(save_to_alias) != 1:
        raise ValueError(f"Only one record id alias can be specified via @<alias> argument, "
                         f"you have specified {save_to_alias}")
    return query, save_to_alias[0] if save_to_alias else None
