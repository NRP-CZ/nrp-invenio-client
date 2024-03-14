import click

from nrp_invenio_client import NRPInvenioClient
from nrp_invenio_client.cli.base import with_repository, with_config, set_group, get_group, list_group, \
    with_output_format, delete_group, remove_group
from nrp_invenio_client.cli.output import print_output_list, print_output
from nrp_invenio_client.config import NRPConfig


@set_group.command(name="variable")
@click.argument("variable")
@click.argument("value")
@with_config()
@with_repository()
def set_variable(
    config: NRPConfig, client: NRPInvenioClient, *, variable, value, **kwargs
):
    client.repository_config.record_aliases[f"@{variable}"] = value
    config.save()

@get_group.command(name="variable")
@click.argument("variable")
@click.argument("value")
@with_config()
@with_repository()
def get_variable(
    config: NRPConfig, client: NRPInvenioClient, *, variable, value, **kwargs
):
    print(client.repository_config.record_aliases[f"@{variable}"])


@list_group.command(name="variables")
@with_output_format()
@with_config()
@with_repository()
def list_variables(
    config: NRPConfig, client: NRPInvenioClient, *, output_format, **kwargs
):
    if output_format in ('yaml', 'json'):
        ret = {k[1:]:v for k, v in client.repository_config.record_aliases.items()}
        print_output(ret, output_format)
    else:
        ret = [{
            'name': k[1:],
            'value': v
        } for k, v in client.repository_config.record_aliases.items()]
        print_output(ret, output_format)


@remove_group.command(name="variable")
@click.argument("variable")
@with_config()
@with_repository()
def delete_variable(
    config: NRPConfig, client: NRPInvenioClient, *, variable, **kwargs
):
    client.repository_config.record_aliases.pop(f"@{variable}", None)
    config.save()
