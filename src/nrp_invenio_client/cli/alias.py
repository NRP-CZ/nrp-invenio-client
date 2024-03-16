import urllib
import urllib.parse

import click

from nrp_invenio_client.config import NRPConfig
from nrp_invenio_client.config.repository_config import RepositoryConfig

from .base import with_config, with_output_format
from .output import print_output


@with_output_format()
@with_config()
def list_aliases(config: NRPConfig, output_format):
    """
    List known repositories
    """
    click.secho("")
    data = [
        {
            "alias": repo.alias,
            "default": repo.alias == config.default_repository,
            "verify": repo.verify,
            "url": repo.url,
        }
        for repo in config.repositories
    ]
    print_output(data, output_format)


@click.argument("servername")
@click.argument("alias", required=False)
@click.option(
    "--default", is_flag=True, default=False, help="Set this repository as the default"
)
@click.option(
    "--token",
    help="Token to use for authentication. If not specified, browser is opened",
)
@click.option(
    "--skip-token",
    default=False,
    is_flag=True,
    help="Skip token creation and use the repository without authentication",
)
@click.option(
    "--verify/--no-verify", default=True, help="Verify the repository certificate"
)
@with_config()
def add_alias(config: NRPConfig, alias, servername, default, token, skip_token, verify):
    """
    Add a new repository to the configuration

    servername   ... servername or url of the repository (myrepo.mycompany.com, https://myrepo.mycompany.com)

    alias        ... local alias to the repository, if not specified, the servername is used
    """
    url = servername

    if not url.startswith("https://"):
        url = f"https://{url}"

    if alias is None:
        alias = urllib.parse.urlparse(url).netloc

    if token is None and not skip_token:
        # open  default browser with url to create token

        login_url = f"{url}/account/settings/applications/tokens/new"

        click.secho(
            f"\nI will try to open the following url in your browser:\n{login_url}\n",
            fg="yellow",
        )
        click.secho(
            "Please log in inside the browser.\nWhen the browser tells you "
            "that the token has been created, \ncopy the token and paste it here.",
            fg="yellow",
        )
        click.secho("Press enter to continue")
        click.getchar()

        try:
            click.launch(login_url)
        except:
            pass

        # wait until the token is created at /account/settings/applications/tokens/retrieve
        token = click.prompt("\nPaste the token here").strip()

    config.repositories = [repo for repo in config.repositories if repo.alias != alias]
    config.repositories.append(
        RepositoryConfig(
            alias=alias,
            url=url,
            token=token,
            verify=verify,
        )
    )
    if default:
        config.default_repository = alias
    click.secho(f"Added repository {alias} -> {url}", fg="green")
    config.save()


@click.argument("alias")
@with_config()
def select_alias(config, alias):
    """
    Select a default repository
    """
    if config.default_repository == alias:
        click.secho(f"Repository {alias} is already selected", fg="yellow")
        return

    if not any(repo.alias == alias for repo in config.repositories):
        click.secho(f"Repository {alias} not found", fg="red")
        return

    config.default_repository = alias
    config.save()
    click.secho(f"Repository {alias} selected", fg="green")


@click.argument("alias")
@with_config()
def remove_alias(config, alias):
    """
    Remove an alias to a repository
    """
    if not any(repo.alias == alias for repo in config.repositories):
        click.secho(f"Repository {alias} not found", fg="red")
        return

    config.repositories = [repo for repo in config.repositories if repo.alias != alias]
    if config.default_repository == alias:
        config.default_repository = None
    config.save()
    click.secho(f"Repository {alias} deleted", fg="green")
