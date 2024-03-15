import re


def extract_alias(query):
    save_to_alias = [q for q in query if q.startswith("@")]
    query = [q for q in query if not q.startswith("@")]
    if save_to_alias and len(save_to_alias) != 1:
        raise ValueError(
            f"Only one record id alias can be specified via @<alias> argument, "
            f"you have specified {save_to_alias}"
        )
    return query, save_to_alias[0] if save_to_alias else None


def format_filename(fmt, f: dict):
    def sanitize(x):
        x = str(x)
        ret = x
        ret = ret.replace("../", "")
        ret = ret.replace("./", "")
        ret = re.sub("^[/.]+", "", ret)
        ret = re.sub("[/.]+$", "", ret)
        return ret

    replacements = {k: sanitize(v) for k, v in f.items()}
    for k, v in f.get("metadata", {}).items():
        replacements[k] = sanitize(v)

    return fmt.format(**replacements)
