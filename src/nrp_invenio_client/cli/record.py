
import click

from nrp_invenio_client import NRPInvenioClient
from nrp_invenio_client.cli.base import (
    create_group,
    get_group,
    with_config,
    with_input_format,
    with_output_format,
    with_repository, update_group, delete_group,
)
from nrp_invenio_client.cli.output import print_output
from nrp_invenio_client.config import NRPConfig
from nrp_invenio_client.records import record_getter
from nrp_invenio_client.utils import read_input_file


@get_group.command(name="record")
@click.option("-o", "--output-file", help="Output file, might use placeholders")
@click.option(
    "--files/--no-files",
    "include_files",
    help="Add a list of files associated with the record to the output",
)
@click.option(
    "--requests/--no-requests",
    "include_requests",
    help="Add a list of requests associated with the record to the output",
)
@click.option("--overwrite/--no-overwrite", help="Overwrite the file")
@click.argument("records_ids", nargs=-1, required=True)
@with_config()
@with_output_format()
@with_repository()
def get_record(
    config: NRPConfig,
    client: NRPInvenioClient,
    *,
    records_ids,
    output_file,
    include_files,
    include_requests,
    overwrite,
    output_format,
    **kwargs,
):
    """
    Retrieve a single record or a list of records given by id. The id can be of the following form:

    * mid (model/id within model)
    * id without model together with --model option (or without if there is just a single model inside the repository)
    * full url (API or HTML)
    * doi of the record
    """

    for record_id in records_ids:
        try:
            rec = record_getter(
                config, record_id, include_files, include_requests, client=client
            )
            # TODO: store to file
            print_output(rec.to_dict(), output_format or "yaml")
        except ValueError as e:
            click.secho(str(e), fg="red")
            raise click.Abort()


@create_group.command(name="record")
@click.argument("model")
@click.argument("data")
@with_config()
@with_input_format()
@with_repository()
def create_record(
    config: NRPConfig, client: NRPInvenioClient, *, model, data, input_format, **kwargs
):
    data = read_input_file(data, input_format)
    rec = client.records.create(model, data)
    print_output(rec.to_dict(), input_format or "yaml")


@update_group.command(name="record")
@click.argument("record_id", required=True)
@click.argument("data", required=True)
@click.option("--overwrite", is_flag=True, help="Do not merge in the provided data, overwrite the record with the data")
@with_config()
@with_input_format()
@with_repository()
def update_record(
    config: NRPConfig, client: NRPInvenioClient, *, record_id, data, input_format, overwrite, **kwargs
):
    data = read_input_file(data, input_format)
    rec = record_getter(
        config, record_id, False, False, client=client
    )
    if overwrite:
        rec.clear_data()

    rec.data.update(data)
    rec.save()
    print_output(rec.to_dict(), input_format or "yaml")

@delete_group.command(name="record")
@click.argument("record_id", required=True)
@with_config()
@with_repository()
def update_record(
    config: NRPConfig, client: NRPInvenioClient, *, record_id, **kwargs
):
    rec = record_getter(
        config, record_id, False, False, client=client
    )
    response = rec.delete()
    print_output(response, "yaml")