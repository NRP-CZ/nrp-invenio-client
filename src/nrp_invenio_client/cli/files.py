import shutil
import sys
from pathlib import Path

import click
from deepmerge import always_merger

from nrp_invenio_client import NRPInvenioClient
from nrp_invenio_client.cli.base import with_config, with_output_format, with_repository
from nrp_invenio_client.cli.output import print_output, print_output_list
from nrp_invenio_client.cli.utils import format_filename
from nrp_invenio_client.config import NRPConfig
from nrp_invenio_client.records import record_getter
from nrp_invenio_client.utils import read_input_file


@click.argument("record_id", required=True)
@click.argument("filename", required=True)
@click.argument("metadata", required=False)
@click.option("--key", help="Key of the file")
@with_config()
@with_output_format()
@with_repository()
def upload_file(
    config: NRPConfig,
    client: NRPInvenioClient,
    *,
    record_id,
    output_format,
    filename,
    key,
    metadata,
    **kwargs,
):
    record_id = _resolve_record_id(client, record_id)

    rec = record_getter(config, record_id, include_files=True, client=client)

    if not key:
        if filename == "-":
            click.secho("--key is required when uploading from stdin", fg="red")
            sys.exit(1)

        key = Path(filename).name

    if key in rec.files:
        click.secho(
            f"File with key '{key}' already exists in record '{record_id}'", fg="red"
        )
        sys.exit(1)

    metadata = read_input_file(metadata, "json")

    if filename == "-":
        stream = click.get_binary_stream("stdin")
    else:
        stream = open(filename, "rb")
    try:
        created_file = rec.files.create(key, metadata, stream)
        print_output(created_file.data, output_format or "yaml")
    finally:
        if filename != "-":
            stream.close()


def _resolve_record_id(client, record_id):
    if record_id.startswith("@"):
        record_id = client.repository_config.record_aliases[record_id]
        if isinstance(record_id, list):
            raise ValueError(
                f"Alias points to multiple records '{record_id}', please specify the record id directly"
            )
    return record_id


@click.argument("record_id", required=True)
@with_output_format()
@with_config()
@with_repository()
def list_files(
    config: NRPConfig, client: NRPInvenioClient, *, record_id, output_format, **kwargs
):
    record_id = _resolve_record_id(client, record_id)

    rec = record_getter(config, record_id, include_files=True, client=client)
    data = [x.to_dict() for x in rec.files.values()]
    print_output_list(data, output_format or "yaml")


@click.argument("record_id", required=True)
@click.argument("filenames", required=True, nargs=-1)
@click.option("-o", "--output", help="Output file", default="{key}")
@with_config()
@with_repository()
def download_file(
    config: NRPConfig,
    client: NRPInvenioClient,
    *,
    record_id,
    filenames,
    output,
    **kwargs,
):
    record_id = _resolve_record_id(client, record_id)

    rec = record_getter(config, record_id, include_files=True, client=client)

    transformed_filenames = {}
    for filename in filenames:
        if filename == "*":
            for file in rec.files.values():
                transformed_filenames[file.key] = format_filename(
                    output, file.to_dict()
                )
        else:
            file = rec.files.get(filename)
            transformed_filenames[file.key] = format_filename(output, file.to_dict())

    for k, v in transformed_filenames.items():
        file = rec.files.get(k)
        if v != "-":
            pth = Path(v)
            pth.parent.mkdir(parents=True, exist_ok=True)

        with file.open() as s:
            if v == "-":
                shutil.copyfileobj(s, sys.stdout.buffer)
            else:
                with open(v, "wb") as f:
                    shutil.copyfileobj(s, f)


@click.argument("record_id", required=True)
@click.argument("key", required=True)
@click.argument("metadata", required=False)
@click.option(
    "--replace",
    is_flag=True,
    help="Do not merge in the provided metadata, " "replace the metadata",
)
@with_config()
@with_output_format()
@with_repository()
def update_file_metadata(
    config: NRPConfig,
    client: NRPInvenioClient,
    *,
    record_id,
    output_format,
    replace,
    key,
    metadata,
    **kwargs,
):
    record_id = _resolve_record_id(client, record_id)

    rec = record_getter(config, record_id, include_files=True, client=client)
    f = rec.files.get(key)
    if not f:
        click.secho(
            f"File with key '{key}' does not exist in record '{record_id}'", fg="red"
        )
        sys.exit(1)

    metadata = read_input_file(metadata, "json")
    if replace:
        f.metadata.clear()

    f.metadata.update(always_merger.merge(f.metadata, metadata))

    f.save()

    print_output(f.data, output_format or "yaml")


@click.argument("record_id", required=True)
@click.argument("key", required=True)
@click.argument("filename", required=True)
@with_config()
@with_output_format()
@with_repository()
def replace_file(
    config: NRPConfig,
    client: NRPInvenioClient,
    *,
    record_id,
    filename,
    key,
    output_format,
    **kwargs,
):
    record_id = _resolve_record_id(client, record_id)

    rec = record_getter(config, record_id, include_files=True, client=client)

    f = rec.files.get(key)
    if not f:
        click.secho(
            f"File with key '{key}' does not exist in record '{record_id}'", fg="red"
        )
        sys.exit(1)

    with open(filename, "rb") as stream:
        f.replace(stream)

    print_output(f.data, output_format or "yaml")


@click.argument("record_id", required=True)
@click.argument("key", required=True)
@with_config()
@with_repository()
def delete_file(
    config: NRPConfig, client: NRPInvenioClient, *, record_id, key, **kwargs
):
    record_id = _resolve_record_id(client, record_id)

    rec = record_getter(config, record_id, include_files=True, client=client)

    f = rec.files.get(key)
    if not f:
        click.secho(
            f"File with key '{key}' does not exist in record '{record_id}'", fg="red"
        )
        sys.exit(1)
    f.delete()
