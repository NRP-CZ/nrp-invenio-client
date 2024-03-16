import sys

import click
from deepmerge import always_merger

from nrp_invenio_client import NRPInvenioClient
from nrp_invenio_client.cli.base import (
    handle_http_exceptions,
    with_config,
    with_input_format,
    with_output_format,
    with_repository,
)
from nrp_invenio_client.cli.output import print_output
from nrp_invenio_client.cli.record import save_record_to_output_file
from nrp_invenio_client.config import NRPConfig
from nrp_invenio_client.records import record_getter
from nrp_invenio_client.utils import read_input_file


@click.option("-o", "--output-file", help="Output file, might use placeholders")
@click.argument("record_id", required=True)
@with_config()
@with_output_format()
@with_repository()
@handle_http_exceptions()
def list_requests(
    config: NRPConfig,
    client: NRPInvenioClient,
    *,
    record_id,
    output_file,
    output_format,
    **kwargs,
):
    """
    List requests of a record.

    * mid (model/id within model)
    * id without model together with --model option (or without if there is just a single model inside the repository)
    * full url (API or HTML)
    * doi of the record
    """

    if record_id.startswith("@"):
        record_id = client.repository_config.record_aliases[record_id]

    rec = record_getter(config, record_id, include_requests=True, client=client)

    if output_file:
        save_record_to_output_file(
            rec, output_file, output_format, saved_data=rec.requests.to_dict()
        )
    else:
        print_output(rec.requests.to_dict(), output_format or "yaml")


@click.option("-o", "--output-file", help="Output file, might use placeholders")
@click.argument("record_id", required=True)
@click.argument("request_id", required=True)
@click.argument("payload", required=False)
@click.argument("variable", required=False)
@click.option("--submit", is_flag=True, help="Submit the request for approval")
@with_config()
@with_output_format()
@with_input_format()
@with_repository()
@handle_http_exceptions()
def create_request(
    config: NRPConfig,
    client: NRPInvenioClient,
    *,
    record_id,
    request_id,
    payload,
    input_format,
    output_format,
    submit,
    variable,
    **kwargs,
):
    """
    Create a new requests on a record.

    The record_id is any recognized request id, e.g. "doi", "url", "mid".
    request_id is the identification of the request, run nrp-cmd list requests @record_id
    to see the available requests.
    You might pass a payload to the request, if the request requires it. In this case,
    the payload is either a json string starting with "{" or a file name.
    The payload might be '-' to read from stdin.
    """

    if record_id.startswith("@"):
        record_id = client.repository_config.record_aliases[record_id]

    if payload and payload.startswith("@"):
        variable = payload
        payload = None

    payload_data = read_input_file(payload, input_format) if payload else {}

    rec = record_getter(config, record_id, include_requests=True, client=client)
    request = rec.requests.create(request_id, metadata=payload_data, submit=submit)

    if variable:
        client.repository_config.record_aliases[variable] = (
            record_id + "/" + request.request_id
        )
        config.save()

    print_output(request.to_dict(), output_format or "yaml")


@click.option("-o", "--output-file", help="Output file, might use placeholders")
@click.argument("pid_or_request_id", required=True)
@click.argument("request_id", required=False)
@with_config()
@with_output_format()
@with_repository()
@handle_http_exceptions()
def get_request(
    config: NRPConfig,
    client: NRPInvenioClient,
    *,
    pid_or_request_id,
    request_id,
    output_format,
    output_file,
    **kwargs,
):
    """
    Get request
    """

    record, request = _get_request(client, config, pid_or_request_id, request_id)

    if output_file:
        save_record_to_output_file(
            record, output_file, output_format, saved_data=request.to_dict()
        )
    else:
        print_output(request.to_dict(), output_format or "yaml")


@click.argument("pid_or_request_id", required=True)
@click.argument("request_id", required=False)
@click.argument("data", required=False)
@click.option(
    "--replace",
    is_flag=True,
    help="Do not merge in the provided data, replace the request payload",
)
@with_config()
@with_input_format()
@with_output_format()
@with_repository()
@handle_http_exceptions()
def update_request(
    config: NRPConfig,
    client: NRPInvenioClient,
    *,
    pid_or_request_id,
    request_id,
    input_format,
    output_format,
    data,
    replace,
    **kwargs,
):
    """
    Update request
    """

    if not data:
        data = request_id
        request_id = None
    if not data:
        click.echo("No data provided", err=True)
        sys.exit(1)

    record, request = _get_request(client, config, pid_or_request_id, request_id)

    if replace:
        request.payload.clear()

    request.payload.update(
        always_merger.merge(request.payload, read_input_file(data, input_format))
    )
    request.save()

    print_output(request.to_dict(), output_format or "yaml")


@click.argument("pid_or_request_id", required=True)
@click.argument("request_id", required=False)
@with_config()
@with_output_format()
@with_repository()
@handle_http_exceptions()
def submit_request(
    config: NRPConfig,
    client: NRPInvenioClient,
    *,
    pid_or_request_id,
    request_id,
    output_format,
    **kwargs,
):
    """
    Submit request
    """
    record, request = _get_request(client, config, pid_or_request_id, request_id)

    request.submit()

    print_output(request.to_dict(), output_format or "yaml")


@click.argument("pid_or_request_id", required=True)
@click.argument("request_id", required=False)
@with_config()
@with_output_format()
@with_repository()
@handle_http_exceptions()
def cancel_request(
    config: NRPConfig,
    client: NRPInvenioClient,
    *,
    pid_or_request_id,
    request_id,
    output_format,
    **kwargs,
):
    """
    Submit request
    """
    record, request = _get_request(client, config, pid_or_request_id, request_id)

    request.cancel()

    print_output(request.to_dict(), output_format or "yaml")


@click.argument("pid_or_request_id", required=True)
@click.argument("request_id", required=False)
@with_config()
@with_output_format()
@with_repository()
@handle_http_exceptions()
def accept_request(
    config: NRPConfig,
    client: NRPInvenioClient,
    *,
    pid_or_request_id,
    request_id,
    output_format,
    **kwargs,
):
    """
    Accept request
    """
    record, request = _get_request(client, config, pid_or_request_id, request_id)

    request.accept()

    print_output(request.to_dict(), output_format or "yaml")


@click.argument("pid_or_request_id", required=True)
@click.argument("request_id", required=False)
@with_config()
@with_output_format()
@with_repository()
@handle_http_exceptions()
def decline_request(
    config: NRPConfig,
    client: NRPInvenioClient,
    *,
    pid_or_request_id,
    request_id,
    output_format,
    **kwargs,
):
    """
    Decline request
    """
    record, request = _get_request(client, config, pid_or_request_id, request_id)

    request.decline()

    print_output(request.to_dict(), output_format or "yaml")


def _get_request(client, config, pid_or_request_id, request_id):
    if request_id:
        record_id = pid_or_request_id
        if record_id.startswith("@"):
            record_id = client.repository_config.record_aliases[record_id]
    else:
        request_id = pid_or_request_id
        if request_id.startswith("@"):
            request_id = client.repository_config.record_aliases[request_id]

        # TODO: not efficient, rethink the API to get the request by id
        record_id, request_id = request_id.rsplit("/", maxsplit=1)
    rec = record_getter(config, record_id, include_requests=True, client=client)
    for rt in rec.requests:
        request = rt.get(request_id)
        return rec, request

    click.echo(f"Request {request_id} not found", err=True)
    sys.exit(1)
