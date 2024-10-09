#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
import requests


def resolve_doi(doi):
    """Resolve a DOI to a record ID."""
    response = requests.get(f"https://api.datacite.org/dois/{doi}")
    response.raise_for_status()
    data = response.json()
    return data["data"]["attributes"]["url"]
