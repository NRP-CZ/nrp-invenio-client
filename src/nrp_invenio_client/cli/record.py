from pathlib import Path

import click
from deepmerge import always_merger

from nrp_invenio_client import NRPInvenioClient
from nrp_invenio_client.cli.base import (
    create_group,
    delete_group,
    get_group,
    update_group,
    with_config,
    with_input_format,
    with_output_format,
    with_repository,
)
from nrp_invenio_client.cli.output import print_output, print_dict_output
from nrp_invenio_client.cli.utils import format_filename
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

    expanded_record_ids = []
    for record_id in records_ids:
        if record_id.startswith("@"):
            record_id_or_ids = client.repository_config.record_aliases[record_id]
            if isinstance(record_id_or_ids, str):
                expanded_record_ids.append(record_id_or_ids)
            else:
                expanded_record_ids.extend(record_id_or_ids)
        else:
            expanded_record_ids.append(record_id)
    records_ids = expanded_record_ids

    for record_id in records_ids:
        try:
            rec = record_getter(
                config, record_id, include_files, include_requests, client=client
            )
            if output_file:
                save_record_to_output_file(rec, output_file, output_format)
            else:
                print_output(rec.to_dict(), output_format or "yaml")
        except ValueError as e:
            click.secho(str(e), fg="red")
            raise click.Abort()


def save_record_to_output_file(rec, output_file, output_format):
    data = rec.to_dict()
    output_file = format_filename(output_file, data)
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        if not output_format:
            if output_file.endswith(".yaml"):
                output_format = "yaml"
            elif output_file.endswith(".json"):
                output_format = "json"
            else:
                output_format = "json"
        print_dict_output(data, output_format, file=f)


@create_group.command(name="record")
@click.argument("model")
@click.argument("data")
@click.argument("save_to_alias", required=False)
@with_config()
@with_input_format()
@with_repository()
def create_record(
    config: NRPConfig,
    client: NRPInvenioClient,
    *,
    model,
    data,
    input_format,
    save_to_alias,
    **kwargs,
):

    data = read_input_file(data, input_format)
    rec = client.records.create(model, data)
    print_output(rec.to_dict(), input_format or "yaml")

    if save_to_alias:
        client.repository_config.record_aliases[save_to_alias] = rec.record_id
        config.save()


@update_group.command(name="record")
@click.argument("record_id", required=True)
@click.argument("data", required=True)
@click.option(
    "--replace",
    is_flag=True,
    help="Do not merge in the provided data, replace the record",
)
@with_config()
@with_input_format()
@with_repository()
def update_record(
    config: NRPConfig,
    client: NRPInvenioClient,
    *,
    record_id,
    data,
    input_format,
    replace,
    **kwargs,
):
    data = read_input_file(data, input_format)
    if record_id.startswith("@"):
        record_id = client.repository_config.record_aliases[record_id]
        if isinstance(record_id, list):
            raise ValueError(
                f"Alias points to multiple records '{record_id}', please specify the record id directly"
            )

    rec = record_getter(config, record_id, False, False, client=client)
    if replace:
        rec.clear_data()

    rec.data.update(always_merger.merge(rec.data, data))
    rec.save()

    print_output(rec.to_dict(), input_format or "yaml")


@delete_group.command(name="record")
@click.argument("record_id", required=True)
@with_config()
@with_repository()
def delete_record(config: NRPConfig, client: NRPInvenioClient, *, record_id, **kwargs):
    if record_id.startswith("@"):
        record_id = client.repository_config.record_aliases[record_id]
        if isinstance(record_id, list):
            raise ValueError(
                f"Alias points to multiple records '{record_id}', please specify the record id directly"
            )

    rec = record_getter(config, record_id, False, False, client=client)
    response = rec.delete()
    print_output(response, "yaml")
