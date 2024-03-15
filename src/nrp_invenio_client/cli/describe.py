import click

from .base import with_config, with_output_format, with_repository
from .output import print_output, print_output_list


@with_output_format()
@with_config()
@with_repository()
def describe_repository(*, client, output_format, **kwargs):
    """
    Show information about a repository
    """
    repository_info = client.info.repository

    print_output(repository_info.to_dict(), output_format, order={"description": 10})


@with_output_format()
@with_config()
@with_repository()
@click.argument("alias", required=False)
def describe_models(*, client, output_format, **kwargs):
    """
    Show information about models within the repository
    """
    models = client.info.models
    print_output_list([x.to_dict() for x in models], output_format)
