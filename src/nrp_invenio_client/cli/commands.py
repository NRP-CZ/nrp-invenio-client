import functools
import itertools

from nrp_invenio_client.cli.alias import (
    add_alias,
    list_aliases,
    remove_alias,
    select_alias,
)
from nrp_invenio_client.cli.base import nrp_command
from nrp_invenio_client.cli.describe import describe_models, describe_repository
from nrp_invenio_client.cli.files import (
    delete_file,
    download_file,
    list_files,
    replace_file,
    update_file_metadata,
    upload_file,
)
from nrp_invenio_client.cli.record import (
    create_record,
    delete_record,
    edit_record,
    get_record,
    publish_record,
    update_record,
    validate_record,
)
from nrp_invenio_client.cli.requests import (
    accept_request,
    cancel_request,
    create_request,
    decline_request,
    get_request,
    list_requests,
    submit_request,
    update_request,
)
from nrp_invenio_client.cli.search import list_records, search_records
from nrp_invenio_client.cli.set import (
    get_variable,
    list_variables,
    remove_variable,
    set_variable,
)

commands = [
    ("list", "aliases", list_aliases),
    ("add", "alias", add_alias),
    ("select", "alias", select_alias),
    ("remove", "alias", remove_alias),
    ("describe", "repository", describe_repository),
    ("describe", "models", describe_models),
    ("search", "records", search_records),
    ("list", "records", list_records),
    ("get", "record", get_record),
    ("create", "record", create_record),
    ("update", "record", update_record),
    ("delete", "record", delete_record),
    ("publish", "record", publish_record),
    ("edit", "record", edit_record),
    ("validate", "record", validate_record),
    ("upload", "file", upload_file),
    ("list", "files", list_files),
    ("download", "file", download_file),
    ("update", "file", update_file_metadata),
    ("replace", "file", replace_file),
    ("delete", "file", delete_file),
    ("set", "variable", set_variable),
    ("get", "variable", get_variable),
    ("list", "variables", list_variables),
    ("remove", "variable", remove_variable),
    ("list", "requests", list_requests),
    ("create", "request", create_request),
    ("get", "request", get_request),
    ("update", "request", update_request),
    ("submit", "request", submit_request),
    ("cancel", "request", cancel_request),
    ("accept", "request", accept_request),
    ("decline", "request", decline_request),
]


def wrapper(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def generate_commands():
    # verb to object
    for grp, data in itertools.groupby(sorted(commands), lambda x: x[0]):
        data = list(data)
        subcommands = set(x[1] for x in data)
        subcommands = " ".join(subcommands)
        group = nrp_command.group(name=grp, help=f"{grp} [{subcommands}]")
        group = group(lambda *args, **kwargs: None)
        for _, cmd, func in data:
            group.command(name=cmd)(wrapper(func))
    # object to verb
    for grp, data in itertools.groupby(
        sorted(commands, key=lambda x: (x[1], x[0])), lambda x: x[1]
    ):
        data = list(data)
        subcommands = set(x[0] for x in data)
        subcommands = " ".join(subcommands)
        group = nrp_command.group(name=grp, help=f"{grp} [{subcommands}]", hidden=True)
        group = group(lambda *args, **kwargs: None)
        for cmd, _, func in data:
            group.command(name=cmd)(wrapper(func))


generate_commands()
