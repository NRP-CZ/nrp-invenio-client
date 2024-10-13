#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""CLI commands for managing repositories."""

import sys
import urllib
import urllib.parse
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator, Optional

import typer
from rich import box
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated

from invenio_nrp import Config, SyncClient
from invenio_nrp.config.repository import RepositoryConfig

from .base import OutputFormat, OutputWriter

if TYPE_CHECKING:
    from invenio_nrp.types import ModelInfo


def add_repository(
    url: Annotated[str, typer.Argument(help="The URL of the repository")],
    alias: Annotated[
        Optional[str], typer.Argument(help="The alias of the repository")
    ] = None,
    token: Annotated[
        Optional[str], typer.Option(help="The token to access the repository")
    ] = None,
    tls_verify: Annotated[bool, typer.Option(help="Verify the TLS certificate")] = True,
    retry_count: Annotated[int, typer.Option(help="Number of retries")] = 5,
    retry_after_seconds: Annotated[
        int, typer.Option(help="Retry after this interval")
    ] = 5,
    anonymous: Annotated[
        bool, typer.Option(help="Do not store the token in the configuration")
    ] = False,
    default: Annotated[
        bool, typer.Option(help="Set this repository as the default")
    ] = False,
) -> None:
    """Add a new repository to the configuration."""
    console = Console()
    console.print()

    if not url.startswith("https://"):
        url = f"https://{url}"

    if alias is None:
        alias = urllib.parse.urlparse(url).netloc

    config = Config.from_file()

    try:
        config.get_repository(alias)
        console.print(f'[red]Repository with alias "{alias}" already exists[/red]')
        sys.exit(1)
    except KeyError:
        pass

    console.print(
        f"Adding repository [green]{url}[/green] with alias [green]{alias}[/green]"
    )

    if token is None and not anonymous:
        # open  default browser with url to create token

        login_url = f"{url}/account/settings/applications/tokens/new"

        console.print(
            f"\nI will try to open the following url in your browser:\n{login_url}\n",
        )
        console.print(
            "Please log in inside the browser.\nWhen the browser tells you "
            "that the token has been created, \ncopy the token and paste it here.",
        )
        console.print("Press enter to continue")
        typer.getchar()

        try:
            typer.launch(login_url)
        except Exception as e:  # noqa
            print("Failed to open the browser. Please open the URL above manually.")

        # wait until the token is created at /account/settings/applications/tokens/retrieve
        token = typer.prompt("\nPaste the token here").strip()

    config.add_repository(
        RepositoryConfig(
            alias=alias,
            url=url,
            token=token,
            tls_verify=tls_verify,
            retry_count=retry_count,
            retry_after_seconds=retry_after_seconds,
        )
    )
    if default or len(config.repositories) == 1:
        config.set_default_repository(alias)

    # check if the repository is reachable and get its parameters
    SyncClient(config=config, alias=alias).info(refresh=True)

    console.print(f"[green]Added repository {alias} -> {url}[/green]")
    config.save()


def remove_repository(
    alias: Annotated[str, typer.Argument(help="The alias of the repository")],
) -> None:
    """Remove a repository from the configuration."""
    console = Console()
    console.print()
    client: SyncClient = SyncClient()

    client.config.remove_repository(alias)
    console.print(f"[green]Removed repository {alias}[/green]")
    client.config.save()


def select_repository(
    alias: Annotated[str, typer.Argument(help="The alias of the repository")],
) -> None:
    """Select a default repository."""
    console = Console()
    console.print()
    config = Config.from_file()

    config.set_default_repository(alias)
    console.print(f"[green]Selected repository {alias}[/green]")
    config.save()


def list_repositories(
    verbose: Annotated[
        bool, typer.Option(help="Show more information about the repositories")
    ] = False,
    output_file: Annotated[
        Optional[Path],
        typer.Option(help="Save the output to a file", metavar="output"),
    ] = None,
    output_format: Annotated[
        Optional[OutputFormat],
        typer.Option(help="The format of the output"),
    ] = None,
) -> None:
    """List all repositories."""
    console = Console()
    config = Config.from_file()

    with OutputWriter(
        output_file,
        output_format,
        console,
        partial(output_tables, config=config, verbose=verbose),
    ) as printer:
        if verbose:
            printer.output(
                [dump_repo_configuration(repo) for repo in config.repositories]
            )
        else:
            printer.output([repo.alias for repo in config.repositories])


def dump_repo_configuration(repo: RepositoryConfig) -> dict:
    """Dump the repository configuration into a json-compatible structure."""
    return {
        "alias": repo.alias,
        "url": str(repo.url),
        "token": "***" if repo.token else "anonymous",
        "tls_verify": repo.verify_tls,
        "retry_count": repo.retry_count,
        "retry_after_seconds": repo.retry_after_seconds,
        "info": repo.info.model_dump(mode="json") if repo.info else None,
    }


def output_tables(*, config: Config, verbose: bool, **kwargs: dict) -> Generator[Table]:
    """Output the information about the repositories formatted as a table."""
    if not verbose:
        table = Table(title="Repositories", box=box.SIMPLE, title_justify="left")
        table.add_column("Alias", style="cyan")
        table.add_column("URL")
        table.add_column("Default", style="green")
        for repo in config.repositories:
            table.add_row(
                repo.alias,
                str(repo.url),
                "✓" if repo == config.default_repository else "",
            )
        yield table
    else:
        for repo in config.repositories:
            yield from output_repository_info_table(config, repo)


def output_repository_info_table(
    config: Config,
    repo: RepositoryConfig,
    **kwargs: Any,  # noqa: ANN401
) -> Generator[Table]:
    """Output the information about a repository formatted as a table."""
    table = Table(
        title=f"Repository '{repo.alias}'",
        box=box.SIMPLE,
        show_header=False,
        title_justify="left",
    )
    table.add_column("", style="cyan")
    table.add_column("")
    if repo.info:
        table.add_row("Name", repo.info.name)
    table.add_row("URL", str(repo.url))
    table.add_row("Token", "***" if repo.token else "anonymous")
    table.add_row("TLS Verify", "✓" if repo.verify_tls else "[red]skip[/red]")
    table.add_row("Retry Count", str(repo.retry_count))
    table.add_row("Retry After Seconds", str(repo.retry_after_seconds))
    table.add_row("Default", "✓" if repo == config.default_repository else "")
    if repo.info:
        table.add_row("Version", repo.info.version)
        table.add_row("Invenio Version", repo.info.invenio_version)
        table.add_row("Transfers", ", ".join(repo.info.transfers))
        table.add_row("Records url", str(repo.info.links.records))
        table.add_row("User records url", str(repo.info.links.user_records))
    yield table

    if repo.info:
        model_info: ModelInfo
        for model_name, model_info in repo.info.models.items():
            table = Table(
                title=f"Model '{model_name}'",
                box=box.SIMPLE,
                show_header=False,
                title_justify="left",
            )
            table.add_column("", style="cyan")
            table.add_column("")
            table.add_row("Name", model_info.name)
            table.add_row("Description", model_info.description)
            table.add_row("Version", model_info.version)
            table.add_row("Features", ", ".join(model_info.features))
            table.add_row("Schemas", str(model_info.schemas))
            table.add_row("API", str(model_info.links.api))
            table.add_row("HTML", str(model_info.links.html))
            table.add_row("Schemas", str(model_info.links.schemas))
            table.add_row("Model Schema", str(model_info.links.model))
            table.add_row("Published Records URL", str(model_info.links.published))
            table.add_row("User Records URL", str(model_info.links.user_records))
            yield table


def describe_repository(
    alias: Annotated[str, typer.Argument(help="The alias of the repository")],
    refresh: Annotated[
        bool, typer.Option(help="Force a refresh of the information")
    ] = False,
    output_file: Annotated[
        Optional[Path],
        typer.Option(help="Save the output to a file"),
    ] = None,
    output_format: Annotated[
        Optional[OutputFormat],
        typer.Option(help="The format of the output"),
    ] = None,
) -> None:
    """Get information about a repository."""
    console = Console()
    config = Config.from_file()
    client: SyncClient = SyncClient(alias=alias, config=config)

    if refresh:
        client.info(refresh=refresh)
        client.config.save()

    with OutputWriter(
        output_file,
        output_format,
        console,
        partial(
            output_repository_info_table, config=config, repo=client.repository_config
        ),
    ) as printer:
        printer.output(dump_repo_configuration(client.repository_config))
