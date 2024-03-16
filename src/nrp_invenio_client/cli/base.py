import functools
import sys
from typing import List

import click
import httpx

from nrp_invenio_client.cli.output import print_dict_output
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


def handle_http_exceptions():
    def decorator(f):
        f = click.option("--show-exceptions", is_flag=True, help="Show exceptions")(f)

        @functools.wraps(f)
        def decorated(*args, **kwargs):
            show_exceptions = kwargs.pop("show_exceptions", False)
            try:
                return f(*args, **kwargs)
            except httpx.HTTPStatusError as e:
                response_text = e.response.text
                response_content_type = e.response.headers.get("content-type", "")
                if response_content_type == "application/json":
                    response_text = e.response.json()
                    print_dict_output(
                        response_text,
                        output_format=kwargs.get("output_format", "yaml"),
                        file=sys.stderr,
                    )
                    sys.exit(1)
                click.secho(
                    f"HTTP Error: {response_content_type} {response_text}",
                    fg="red",
                    file=sys.stderr,
                )
                sys.exit(1)
            except Exception as e:
                if show_exceptions:
                    raise
                click.secho(str(e), fg="red", file=sys.stderr)
                sys.exit(1)

        return decorated

    return decorator


def arg_split(ctx, param, value: str | List[str]):
    # split the value by comma and join into a single list
    ret = []
    if isinstance(value, str):
        ret.extend(x.strip() for x in value.split(","))
    else:
        for val in value:
            ret.extend(x.strip() for x in val.split(","))
    return [x for x in ret if x]
