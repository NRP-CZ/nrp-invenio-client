import functools
from typing import List

import click

from nrp_invenio_client.config import NRPConfig


@click.group(invoke_without_command=True)
@click.pass_context
def nrp_command(context):
    if context.invoked_subcommand:
        return
    click.secho(
        """
This is the nrp commandline tool. You can use it to access your repositories.

Repository aliases and tokens:
These are used to set up a connection to a repository. The alias is a local
name for the repository, the token is used to authenticate the user. You can
also create an anonymous connection to a repository.""",
        fg="yellow",
    )

    click.secho(
        """
nrp-command add alias       - add a new alias
nrp-command select alias    - select an alias as the default
nrp-command remove alias    - remove an alias
nrp-command list aliases    - list all aliases
    """,
        fg="green",
    )

    click.secho(
        """
Introspection commands:
""",
        fg="yellow",
    )

    click.secho(
        """
nrp-command describe repository  - show information about a repository
nrp-command describe models      - show information about the models in a repository
    """,
        fg="green",
    )

    click.secho(
        """
Record CRUD commands:
""",
        fg="yellow",
    )

    click.secho(
        """
nrp-command search records       - search for records
nrp-command get record           - 
nrp-command describe models      - show information about the models in a repository
    """,
        fg="green",
    )


def with_config():
    def decorator(f):
        f = click.option(
            "--config",
            type=click.Path(exists=True, dir_okay=False),
            help="Path to the configuration file",
        )(f)

        @functools.wraps(f)
        def decorated(config, **kwargs):
            cmd_config = NRPConfig()
            cmd_config.load(config)
            f(config=cmd_config, **kwargs)

        return decorated

    return decorator


def with_output_format():
    def decorator(f):
        return click.option(
            "--format",
            "output_format",
            type=click.Choice(["json", "yaml", "table", "long"]),
            help="Output format",
        )(f)

    return decorator


def with_input_format():
    def decorator(f):
        return click.option(
            "--format",
            "input_format",
            type=click.Choice(["json", "yaml"]),
            help="Format of the input data",
        )(f)

    return decorator


def with_repository():
    def decorator(f):
        f = click.option("--alias", help="Alias of the repository to use.")(f)
        f = click.option("--token", help="Token to use for authentication.")(f)
        f = click.option("--repository-url", help="Repository url.")(f)
        f = click.option("--retries", help="Number of retries", type=int, default=10)(f)
        f = click.option(
            "--retry-interval", help="Retry interval in seconds", type=int, default=10
        )(f)

        @functools.wraps(f)
        def decorated(*, config, **kwargs):
            from nrp_invenio_client import NRPInvenioClient

            if kwargs.get("repository_url"):
                if kwargs.get("alias"):
                    raise ValueError("You cannot specify both repository-url and alias")
                client = NRPInvenioClient(
                    server_url=kwargs["repository_url"],
                    token=kwargs.get("token"),
                    verify=kwargs.get("verify", True),
                    retry_count=kwargs.get("retries", 3),
                    retry_interval=kwargs.get("retry_interval", 1),
                )
            else:
                client = NRPInvenioClient.from_config(kwargs.get("alias"), config)
            f(client=client, config=config, **kwargs)

        return decorated

    return decorator


@nrp_command.group(name="add")
def add_group():
    """
    Add stuff - run without arguments to see what can be added.
    """


@nrp_command.group(name="select")
def select_group():
    """
    Select stuff - run without arguments to see what can be selected.
    """


@nrp_command.group(name="remove")
def remove_group():
    """
    Remove stuff - run without arguments to see what can be removed.
    """


@nrp_command.group(name="list")
def list_group():
    """
    List stuff - run without arguments to see what can be listed.
    """


@nrp_command.group(name="search")
def search_group():
    """
    Search stuff - run without arguments to see what can be searched.
    """


@nrp_command.group(name="describe")
def describe_group():
    """
    Describe repository, models, ... - run without arguments to see what can be described.
    """


@nrp_command.group(name="get")
def get_group():
    """
    Get stuff from repository - run without arguments to see what can be gotten.
    """


@nrp_command.group(name="create")
def create_group():
    """
    Create stuff in repository - run without arguments to see what can be created.
    """


@nrp_command.group(name="update")
def update_group():
    """
    Update stuff in repository - run without arguments to see what can be updated.
    """

@nrp_command.group(name="delete")
def delete_group():
    """
    Delete stuff - run without arguments to see what can be removed.
    """

@nrp_command.group(name="upload")
def upload_group():
    """
    Upload stuff - run without arguments to see what can be uploaded.
    """


@nrp_command.group(name="set")
def set_group():
    """
    Set stuff - run without arguments to see what can be set.
    """

@nrp_command.group(name="download")
def download_group():
    """
    Download stuff - run without arguments to see what can be downloaded.
    """

@nrp_command.group(name="replace")
def replace_group():
    """
    Replace stuff - run without arguments to see what can be replaced.
    """


def arg_split(ctx, param, value: str | List[str]):
    # split the value by comma and join into a single list
    ret = []
    if isinstance(value, str):
        ret.extend(x.strip() for x in value.split(","))
    else:
        for val in value:
            ret.extend(x.strip() for x in val.split(","))
    return [x for x in ret if x]
