import functools
from typing import Any, Generator

import click

from ..config import NRPConfig
from ..records import NRPRecord
from .base import arg_split, with_config, with_output_format, with_repository
from .output import print_output, print_output_list
from .utils import extract_alias


def search_decorator(f):
    @with_config()
    @with_output_format()
    @with_repository()
    @click.option(
        "--model",
        "models",
        multiple=True,
        help="Name of the model which will be searched. If not specified, all models will be searched. "
        "This option can be specified multiple times.",
        callback=arg_split,
    )
    @click.option(
        "--size", default=10, help="Number of results to return. Default is 10."
    )
    @click.option("--page", default=1, help="Page number to return. Default is 1.")
    @click.option(
        "--all-records",
        is_flag=True,
        help="If specified, all records will be returned. This will override the --size and --page modifiers. "
        "You need to be authenticated to use this option.",
    )
    @click.option(
        "--sort",
        multiple=True,
        help="Sort order. The format is <field>:<order>, where <field> is the name of the field to sort by "
        "and <order> is either asc or desc. The default order is asc. This option can be specified multiple times "
        "or the options can be split with comma.",
        callback=arg_split,
    )
    @click.option(
        "--drafts",
        is_flag=True,
        help="If specified, only draft records will be returned.",
    )
    @click.option(
        "--published",
        is_flag=True,
        help="If specified, only published records will be returned.",
    )
    @click.argument("query", nargs=-1)
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)

    return wrapper


@search_decorator
def search_records(**kwargs):
    """
    Searches within records. You can either specify just a search query or
    restrict to models of certain type, status (published or draft) or records belonging
    to you.
    """
    internal_search(**kwargs)


@search_decorator
def list_records(**kwargs):
    """
    Lists records. You can also specify search query or
    restrict the listing to models of certain type,
    status (published or draft) or records belonging to you.
    """
    internal_search(**kwargs)


def internal_search(
    *,
    config: NRPConfig,
    client,
    output_format,
    models,
    size,
    page,
    all_records,
    sort,
    drafts,
    published,
    query,
    **kwargs,
):
    query, save_to_alias = extract_alias(query)
    if save_to_alias:
        if not client.repository_config:
            raise click.ClickException(
                "A repository alias must be specified to save the results to an alias."
            )

    request = client.search_request(models)

    if page is not None:
        request.page(page)
    if size is not None:
        request.size(size)
    if sort is not None:
        request.order_by(*sort)
    if published:
        request.published()
    if drafts:
        request.drafts()
    if query is not None:
        request.query(query)

    record_aliases = []
    if all_records:

        def alias_saver(results: Generator[NRPRecord, Any, None]):
            for res in results:
                if save_to_alias:
                    record_aliases.append(res.record_id)
                yield res.to_dict()

        with request.scan() as results:
            print_output_list(alias_saver(results), output_format or "yaml")
    else:
        r = request.execute()
        results = list(r)
        print_output(
            {
                "hits": list(rec.to_dict() for rec in results),
                "total": r.total,
                "links": r.links,
            },
            output_format or "yaml",
        )
        if save_to_alias:
            record_aliases.extend(rec.record_id for rec in results)

    if save_to_alias:
        client.repository_config.record_aliases[save_to_alias] = record_aliases
    config.save()
