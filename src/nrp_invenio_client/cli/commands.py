import functools
import itertools

from nrp_invenio_client.cli.alias import list_aliases, add_alias, select_alias, remove_alias
from nrp_invenio_client.cli.describe import describe_repository, describe_models
from nrp_invenio_client.cli.files import upload_file, list_files, download_file, update_file_metadata, replace_file, \
    delete_file
from nrp_invenio_client.cli.record import get_record, create_record, update_record, delete_record, publish_record, \
    edit_record
from nrp_invenio_client.cli.search import search_records, list_records
from nrp_invenio_client.cli.set import set_variable, get_variable, list_variables, remove_variable
from nrp_invenio_client.cli.base import nrp_command

commands = [
    ("list", "aliases", list_aliases),
    ("add", "alias", add_alias),
    ("select", "alias", select_alias),
    ("remove", "alias", remove_alias),
    ("describe", "repository", describe_repository),
    ("describe", "models", describe_models),
    ("upload", "file", upload_file),
    ("list", "files", list_files),
    ("download", "file", download_file),
    ("update", "file", update_file_metadata),
    ("replace", "file", replace_file),
    ("delete", "file", delete_file),
    ("get", "record", get_record),
    ("create", "record", create_record),
    ("update", "record", update_record),
    ("delete", "record", delete_record),
    ("publish", "record", publish_record),
    ("edit", "record", edit_record),
    ("search", "records", search_records),
    ("list", "records", list_records),
    ("set", "variable", set_variable),
    ("get", "variable", get_variable),
    ("list", "variables", list_variables),
    ("remove", "variable", remove_variable),
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
        subcommands = ' '.join(subcommands)
        group = nrp_command.group(name=grp, help=f"{grp} [{subcommands}]")
        group = group(lambda *args, **kwargs: None)
        for _, cmd, func in data:
            group.command(name=cmd)(wrapper(func))
    # object to verb
    for grp, data in itertools.groupby(sorted(commands, key=lambda x: (x[1], x[0])), lambda x: x[1]):
        data = list(data)
        subcommands = set(x[0] for x in data)
        subcommands = ' '.join(subcommands)
        group = nrp_command.group(name=grp, help=f"{grp} [{subcommands}]")
        group = group(lambda *args, **kwargs: None)
        for cmd, _, func in data:
            group.command(name=cmd)(wrapper(func))


generate_commands()
