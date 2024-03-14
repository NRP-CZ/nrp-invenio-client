import json
import re
import sys
from itertools import chain
from typing import TYPE_CHECKING, Tuple
from urllib.parse import urlparse

import pydoi
import yaml

if TYPE_CHECKING:
    from nrp_invenio_client import NRPInvenioClient
    from nrp_invenio_client.config import NRPConfig


doi_regex = re.compile(r"^\s*(10.(\d)+/(\S)+)\s*$")


def is_doi(record_id):
    if record_id.startswith("doi:"):
        return True
    if record_id.startswith("https://doi.org/"):
        return True
    return doi_regex.match(record_id)


def is_url(record_id):
    return record_id.startswith("http://") or record_id.startswith("https://")


def resolve_record_doi(config: "NRPConfig", doi) -> Tuple["NRPInvenioClient", str]:
    """
    Resolves the DOI and return a pair of the client and the API path within the client
    """
    # 1. call the DOI resolver to get the URL of the record
    if doi.startswith("doi:"):
        doi = doi[4:]
    if doi.startswith("https://doi.org/"):
        doi = doi[16:]
    url = pydoi.get_url(doi)
    return resolve_repository_url(config, url)


def resolve_repository_url(config: "NRPConfig", url):
    from nrp_invenio_client import NRPInvenioClient

    # 1. check if the url matches a preconfigured repository and if so, return a pre-configured client (including token)
    for repo in config.repositories:
        if url.startswith(repo.url):
            # keep leading '/' in the path
            repo_url = repo.url
            if repo_url.endswith("/"):
                repo_url = repo_url[:-1]
            return (
                NRPInvenioClient.from_config(repo.alias, config),
                url[len(repo_url) :],
            )
    # 2. if not, create a dummy, unconfigured client for the URL and return it
    parsed_url = urlparse(url)
    return NRPInvenioClient(parsed_url._replace(path="").geturl()), parsed_url.path


def is_mid(record_id):
    return "/" in record_id


def get_mid(models, data):
    if "mid" in data:
        return data["mid"].split("/")

    if len(models) == 1:
        return (models[0].name, data["id"])

    # go through $schema and find the model
    schema = data["$schema"]
    for model_info in models:
        if any(schema == x for x in model_info.schemas):
            return (model_info.name, data["id"])

    potential_schemas = list(chain(*[x.schemas for x in models]))
    raise KeyError(
        f"Model for schema {schema} not found. Available models: {potential_schemas}"
    )


def read_input_file(filename, format):
    filename = filename.strip()
    if filename and filename[0] in ("[", "{"):
        return json.loads(filename)

    if filename != "-":
        stream = open(filename, "r", encoding="utf-8")
        if not format:
            format = filename.split(".")[-1]
    else:
        stream = sys.stdin
        if not format:
            format = "json"

    try:
        if format == "json":
            return json.load(stream)
        if format == "yaml":
            return yaml.safe_load(stream)
        raise ValueError(
            f"Unknown input format {format}, supported formats are 'json' and 'yaml'"
        )
    finally:
        if stream != sys.stdin:
            stream.close()
