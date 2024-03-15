# Table of Contents

* [nrp\_invenio\_client](#nrp_invenio_client)
* [nrp\_invenio\_client.files](#nrp_invenio_client.files)
  * [FileAdapter](#nrp_invenio_client.files.FileAdapter)
  * [NRPFile](#nrp_invenio_client.files.NRPFile)
    * [\_\_init\_\_](#nrp_invenio_client.files.NRPFile.__init__)
    * [metadata](#nrp_invenio_client.files.NRPFile.metadata)
    * [data](#nrp_invenio_client.files.NRPFile.data)
    * [key](#nrp_invenio_client.files.NRPFile.key)
    * [links](#nrp_invenio_client.files.NRPFile.links)
    * [delete](#nrp_invenio_client.files.NRPFile.delete)
    * [replace](#nrp_invenio_client.files.NRPFile.replace)
    * [open](#nrp_invenio_client.files.NRPFile.open)
    * [save](#nrp_invenio_client.files.NRPFile.save)
    * [to\_dict](#nrp_invenio_client.files.NRPFile.to_dict)
  * [NRPRecordFiles](#nrp_invenio_client.files.NRPRecordFiles)
    * [create](#nrp_invenio_client.files.NRPRecordFiles.create)
    * [to\_dict](#nrp_invenio_client.files.NRPRecordFiles.to_dict)
* [nrp\_invenio\_client.config.config](#nrp_invenio_client.config.config)
* [nrp\_invenio\_client.config](#nrp_invenio_client.config)
* [nrp\_invenio\_client.config.repository\_config](#nrp_invenio_client.config.repository_config)
  * [RepositoryConfig](#nrp_invenio_client.config.repository_config.RepositoryConfig)
* [nrp\_invenio\_client.records](#nrp_invenio_client.records)
  * [NRPRecord](#nrp_invenio_client.records.NRPRecord)
    * [data](#nrp_invenio_client.records.NRPRecord.data)
    * [to\_dict](#nrp_invenio_client.records.NRPRecord.to_dict)
    * [metadata](#nrp_invenio_client.records.NRPRecord.metadata)
    * [files](#nrp_invenio_client.records.NRPRecord.files)
    * [requests](#nrp_invenio_client.records.NRPRecord.requests)
    * [links](#nrp_invenio_client.records.NRPRecord.links)
    * [record\_id](#nrp_invenio_client.records.NRPRecord.record_id)
    * [clear\_data](#nrp_invenio_client.records.NRPRecord.clear_data)
    * [save](#nrp_invenio_client.records.NRPRecord.save)
    * [delete](#nrp_invenio_client.records.NRPRecord.delete)
    * [publish](#nrp_invenio_client.records.NRPRecord.publish)
    * [edit](#nrp_invenio_client.records.NRPRecord.edit)
  * [NRPRecordsApi](#nrp_invenio_client.records.NRPRecordsApi)
    * [get](#nrp_invenio_client.records.NRPRecordsApi.get)
    * [create](#nrp_invenio_client.records.NRPRecordsApi.create)
  * [record\_getter](#nrp_invenio_client.records.record_getter)
* [nrp\_invenio\_client.cli.describe](#nrp_invenio_client.cli.describe)
  * [describe\_repository](#nrp_invenio_client.cli.describe.describe_repository)
  * [describe\_models](#nrp_invenio_client.cli.describe.describe_models)
* [nrp\_invenio\_client.cli.files](#nrp_invenio_client.cli.files)
* [nrp\_invenio\_client.cli.alias](#nrp_invenio_client.cli.alias)
  * [list\_aliases](#nrp_invenio_client.cli.alias.list_aliases)
  * [add\_alias](#nrp_invenio_client.cli.alias.add_alias)
  * [select\_repository](#nrp_invenio_client.cli.alias.select_repository)
  * [remove\_alias](#nrp_invenio_client.cli.alias.remove_alias)
* [nrp\_invenio\_client.cli](#nrp_invenio_client.cli)
* [nrp\_invenio\_client.cli.utils](#nrp_invenio_client.cli.utils)
* [nrp\_invenio\_client.cli.record](#nrp_invenio_client.cli.record)
  * [get\_record](#nrp_invenio_client.cli.record.get_record)
* [nrp\_invenio\_client.cli.search](#nrp_invenio_client.cli.search)
  * [search\_records](#nrp_invenio_client.cli.search.search_records)
  * [list\_records](#nrp_invenio_client.cli.search.list_records)
* [nrp\_invenio\_client.cli.set](#nrp_invenio_client.cli.set)
* [nrp\_invenio\_client.cli.base](#nrp_invenio_client.cli.base)
  * [add\_group](#nrp_invenio_client.cli.base.add_group)
  * [select\_group](#nrp_invenio_client.cli.base.select_group)
  * [remove\_group](#nrp_invenio_client.cli.base.remove_group)
  * [list\_group](#nrp_invenio_client.cli.base.list_group)
  * [search\_group](#nrp_invenio_client.cli.base.search_group)
  * [describe\_group](#nrp_invenio_client.cli.base.describe_group)
  * [get\_group](#nrp_invenio_client.cli.base.get_group)
  * [create\_group](#nrp_invenio_client.cli.base.create_group)
  * [update\_group](#nrp_invenio_client.cli.base.update_group)
  * [delete\_group](#nrp_invenio_client.cli.base.delete_group)
  * [upload\_group](#nrp_invenio_client.cli.base.upload_group)
  * [set\_group](#nrp_invenio_client.cli.base.set_group)
  * [download\_group](#nrp_invenio_client.cli.base.download_group)
  * [replace\_group](#nrp_invenio_client.cli.base.replace_group)
* [nrp\_invenio\_client.cli.output](#nrp_invenio_client.cli.output)
* [nrp\_invenio\_client.utils](#nrp_invenio_client.utils)
  * [is\_doi](#nrp_invenio_client.utils.is_doi)
  * [is\_url](#nrp_invenio_client.utils.is_url)
  * [resolve\_record\_doi](#nrp_invenio_client.utils.resolve_record_doi)
  * [resolve\_repository\_url](#nrp_invenio_client.utils.resolve_repository_url)
  * [is\_mid](#nrp_invenio_client.utils.is_mid)
  * [get\_mid](#nrp_invenio_client.utils.get_mid)
  * [read\_input\_file](#nrp_invenio_client.utils.read_input_file)
* [nrp\_invenio\_client.search](#nrp_invenio_client.search)
  * [NRPSearchRequest](#nrp_invenio_client.search.NRPSearchRequest)
    * [execute](#nrp_invenio_client.search.NRPSearchRequest.execute)
    * [scan](#nrp_invenio_client.search.NRPSearchRequest.scan)
    * [page](#nrp_invenio_client.search.NRPSearchRequest.page)
    * [size](#nrp_invenio_client.search.NRPSearchRequest.size)
    * [order\_by](#nrp_invenio_client.search.NRPSearchRequest.order_by)
    * [published](#nrp_invenio_client.search.NRPSearchRequest.published)
    * [drafts](#nrp_invenio_client.search.NRPSearchRequest.drafts)
    * [query](#nrp_invenio_client.search.NRPSearchRequest.query)
    * [models](#nrp_invenio_client.search.NRPSearchRequest.models)
  * [NRPSearchBaseResponse](#nrp_invenio_client.search.NRPSearchBaseResponse)
  * [NRPSearchResponse](#nrp_invenio_client.search.NRPSearchResponse)
    * [\_\_iter\_\_](#nrp_invenio_client.search.NRPSearchResponse.__iter__)
    * [links](#nrp_invenio_client.search.NRPSearchResponse.links)
    * [total](#nrp_invenio_client.search.NRPSearchResponse.total)
  * [NRPScanResponse](#nrp_invenio_client.search.NRPScanResponse)
    * [\_\_iter\_\_](#nrp_invenio_client.search.NRPScanResponse.__iter__)
* [nrp\_invenio\_client.errors](#nrp_invenio_client.errors)
* [nrp\_invenio\_client.requests](#nrp_invenio_client.requests)
* [nrp\_invenio\_client.info](#nrp_invenio_client.info)
  * [NRPModelInfo](#nrp_invenio_client.info.NRPModelInfo)
    * [name](#nrp_invenio_client.info.NRPModelInfo.name)
    * [schemas](#nrp_invenio_client.info.NRPModelInfo.schemas)
    * [links](#nrp_invenio_client.info.NRPModelInfo.links)
    * [description](#nrp_invenio_client.info.NRPModelInfo.description)
    * [version](#nrp_invenio_client.info.NRPModelInfo.version)
    * [features](#nrp_invenio_client.info.NRPModelInfo.features)
    * [url](#nrp_invenio_client.info.NRPModelInfo.url)
    * [user\_url](#nrp_invenio_client.info.NRPModelInfo.user_url)
    * [to\_dict](#nrp_invenio_client.info.NRPModelInfo.to_dict)
  * [NRPRepositoryInfo](#nrp_invenio_client.info.NRPRepositoryInfo)
    * [name](#nrp_invenio_client.info.NRPRepositoryInfo.name)
    * [description](#nrp_invenio_client.info.NRPRepositoryInfo.description)
    * [version](#nrp_invenio_client.info.NRPRepositoryInfo.version)
    * [invenio\_version](#nrp_invenio_client.info.NRPRepositoryInfo.invenio_version)
    * [links](#nrp_invenio_client.info.NRPRepositoryInfo.links)
    * [features](#nrp_invenio_client.info.NRPRepositoryInfo.features)
    * [transfers](#nrp_invenio_client.info.NRPRepositoryInfo.transfers)
    * [to\_dict](#nrp_invenio_client.info.NRPRepositoryInfo.to_dict)
  * [NRPInfoApi](#nrp_invenio_client.info.NRPInfoApi)
    * [repository](#nrp_invenio_client.info.NRPInfoApi.repository)
    * [models](#nrp_invenio_client.info.NRPInfoApi.models)
    * [get\_model](#nrp_invenio_client.info.NRPInfoApi.get_model)
* [nrp\_invenio\_client.base](#nrp_invenio_client.base)
  * [ResponseFormat](#nrp_invenio_client.base.ResponseFormat)
    * [JSON](#nrp_invenio_client.base.ResponseFormat.JSON)
    * [RAW](#nrp_invenio_client.base.ResponseFormat.RAW)
  * [NRPInvenioClient](#nrp_invenio_client.base.NRPInvenioClient)
    * [\_\_init\_\_](#nrp_invenio_client.base.NRPInvenioClient.__init__)
    * [from\_config](#nrp_invenio_client.base.NRPInvenioClient.from_config)
    * [search](#nrp_invenio_client.base.NRPInvenioClient.search)
    * [scan](#nrp_invenio_client.base.NRPInvenioClient.scan)
    * [clone](#nrp_invenio_client.base.NRPInvenioClient.clone)

<a id="nrp_invenio_client"></a>

# nrp\_invenio\_client

A client for NRP Invenio API. Provides both python client class and a command line interface.

<a id="nrp_invenio_client.files"></a>

# nrp\_invenio\_client.files

<a id="nrp_invenio_client.files.FileAdapter"></a>

## FileAdapter Objects

```python
class FileAdapter()
```

Adapter to convert httpx stream to file-like object

<a id="nrp_invenio_client.files.NRPFile"></a>

## NRPFile Objects

```python
class NRPFile()
```

File object for NRPRecord. It contains the metadata and links of the file
stored inside the repository.

<a id="nrp_invenio_client.files.NRPFile.__init__"></a>

#### \_\_init\_\_

```python
def __init__(*, record: "NRPRecord", key: str, data: typing.Any)
```

Creates a new instance, usually not called directly.

**Arguments**:

- `record`: the record to which the file belongs
- `key`: the key of the file (filename)
- `data`: the metadata and links of the file

<a id="nrp_invenio_client.files.NRPFile.metadata"></a>

#### metadata

```python
@property
def metadata()
```

Returns the metadata of the file (the content of metadata element).

<a id="nrp_invenio_client.files.NRPFile.data"></a>

#### data

```python
@property
def data()
```

Returns the whole data of the file (metadata, links, technical metadata).

<a id="nrp_invenio_client.files.NRPFile.key"></a>

#### key

```python
@property
def key()
```

File key

<a id="nrp_invenio_client.files.NRPFile.links"></a>

#### links

```python
@property
def links()
```

The content of links section, such as "self" or "content"

<a id="nrp_invenio_client.files.NRPFile.delete"></a>

#### delete

```python
def delete()
```

Deletes the file from the record and the repository.

<a id="nrp_invenio_client.files.NRPFile.replace"></a>

#### replace

```python
def replace(stream)
```

Replaces the content of the file with the new stream.

<a id="nrp_invenio_client.files.NRPFile.open"></a>

#### open

```python
@contextlib.contextmanager
def open()
```

Return a file-like object (non-seekable) to read the content of the file from the repository

<a id="nrp_invenio_client.files.NRPFile.save"></a>

#### save

```python
def save()
```

Save the metadata of the file to the repository

<a id="nrp_invenio_client.files.NRPFile.to_dict"></a>

#### to\_dict

```python
def to_dict()
```

Get a json representation of the file

<a id="nrp_invenio_client.files.NRPRecordFiles"></a>

## NRPRecordFiles Objects

```python
class NRPRecordFiles(dict)
```

A dictionary-like object for the files of the NRPRecord.
The keys are the "key" properties of files (mostly filenames),
values are instances of NRPFile.

<a id="nrp_invenio_client.files.NRPRecordFiles.create"></a>

#### create

```python
def create(key, metadata, stream)
```

Creates a new file in the repository

**Arguments**:

- `key`: the key of the file. An exception will be risen if the key already exists
- `metadata`: metadata section of the file, contains user-specific metadata
- `stream`: the content of the file that will be uploaded to the repository

**Returns**:

the created file (instance of NRPFile)

<a id="nrp_invenio_client.files.NRPRecordFiles.to_dict"></a>

#### to\_dict

```python
def to_dict()
```

Dumps all the files (their metadata, not binary content) to a json object

<a id="nrp_invenio_client.config.config"></a>

# nrp\_invenio\_client.config.config

<a id="nrp_invenio_client.config"></a>

# nrp\_invenio\_client.config

<a id="nrp_invenio_client.config.repository_config"></a>

# nrp\_invenio\_client.config.repository\_config

<a id="nrp_invenio_client.config.repository_config.RepositoryConfig"></a>

## RepositoryConfig Objects

```python
@dataclasses.dataclass
class RepositoryConfig()
```

Configuration of the repository

<a id="nrp_invenio_client.records"></a>

# nrp\_invenio\_client.records

<a id="nrp_invenio_client.records.NRPRecord"></a>

## NRPRecord Objects

```python
class NRPRecord()
```

A record in the repository. It contains the metadata and links of the record
and might contain references to files and requests.

This class is not meant to be instantiated directly, use the `get/create` methods of
`NRPRecordsApi` instead.

<a id="nrp_invenio_client.records.NRPRecord.data"></a>

#### data

```python
@property
def data()
```

The whole data of the record (metadata, links, etc.)

<a id="nrp_invenio_client.records.NRPRecord.to_dict"></a>

#### to\_dict

```python
def to_dict()
```

Returns json representation of the record

<a id="nrp_invenio_client.records.NRPRecord.metadata"></a>

#### metadata

```python
@property
def metadata()
```

If the record has a metadata section, return that. Otherwise return the whole data.

<a id="nrp_invenio_client.records.NRPRecord.files"></a>

#### files

```python
@property
def files() -> NRPRecordFiles
```

Returns the files of the record

<a id="nrp_invenio_client.records.NRPRecord.requests"></a>

#### requests

```python
@property
def requests() -> NRPRecordRequests
```

Returns the requests of the record

<a id="nrp_invenio_client.records.NRPRecord.links"></a>

#### links

```python
@property
def links()
```

The content of links section, such as "self" or "draft"

<a id="nrp_invenio_client.records.NRPRecord.record_id"></a>

#### record\_id

```python
@property
def record_id()
```

Returns the id of the record in the form of "model/id" or "draft/model/id"

<a id="nrp_invenio_client.records.NRPRecord.clear_data"></a>

#### clear\_data

```python
def clear_data()
```

Removes all the data from the record except the links, parent, revision_id and id

<a id="nrp_invenio_client.records.NRPRecord.save"></a>

#### save

```python
def save()
```

Saves the metadata of the record to the repository

<a id="nrp_invenio_client.records.NRPRecord.delete"></a>

#### delete

```python
def delete()
```

Deletes the record from the repository

<a id="nrp_invenio_client.records.NRPRecord.publish"></a>

#### publish

```python
def publish()
```

Publishes a draft record

**Returns**:

The published record

<a id="nrp_invenio_client.records.NRPRecord.edit"></a>

#### edit

```python
def edit()
```

Edits a published record - creates a draft copy and returns that

**Returns**:

The draft record

<a id="nrp_invenio_client.records.NRPRecordsApi"></a>

## NRPRecordsApi Objects

```python
class NRPRecordsApi()
```

API for working with records in the repository. Use the `records` property of `NRPInvenioClient` to get an instance.

**Example**:

```
    client = NRPInvenioClient.from_config()
    records = client.records
    record = records.get("model/id")
```

<a id="nrp_invenio_client.records.NRPRecordsApi.get"></a>

#### get

```python
def get(mid: str | typing.Tuple[str, str],
        include_files=False,
        include_requests=False) -> NRPRecord
```

Returns a record by its id

**Arguments**:

- `mid`: Either a string mid "model/id within model" or a tuple (model, id within model).
For drafts, the mid is "draft/model/id within model" or tuple
("draft", model, id within model)
- `include_files`: If True, metadata the files of the record are fetched as well
and included in the returned object. This adds another http request
- `include_requests`: If True, the requests of the record are fetched as well included in the returned object.
This adds another http request

**Returns**:

The JSON data of the record

<a id="nrp_invenio_client.records.NRPRecordsApi.create"></a>

#### create

```python
def create(model, metadata) -> NRPRecord
```

Creates a new record in the repository

**Arguments**:

- `model`: name of the model
- `metadata`: metadata of the record, including the 'metadata' element

**Returns**:

The created record

<a id="nrp_invenio_client.records.record_getter"></a>

#### record\_getter

```python
def record_getter(config: NRPConfig,
                  record_id,
                  include_files=False,
                  include_requests=False,
                  client=None) -> NRPRecord
```

Gets a record, regardless of the format of the record id

**Arguments**:

- `config`: The configuration of known repositories
- `record_id`: if of the record in any supported formats (mid, doi, url)
- `include_files`: If True, metadata the files of the record are fetched as well
- `include_requests`: If True, the requests of the record are fetched as well included in the returned object.
- `client`: Preferred client to use for fetching the record, if the id does not specify a concrete repository

**Returns**:

The record

<a id="nrp_invenio_client.cli.describe"></a>

# nrp\_invenio\_client.cli.describe

<a id="nrp_invenio_client.cli.describe.describe_repository"></a>

#### describe\_repository

```python
@describe_group.command(name="repository")
@with_output_format()
@with_config()
@with_repository()
def describe_repository(*, client, output_format, **kwargs)
```

Show information about a repository

<a id="nrp_invenio_client.cli.describe.describe_models"></a>

#### describe\_models

```python
@describe_group.command(name="models")
@with_output_format()
@with_config()
@with_repository()
@click.argument("alias", required=False)
def describe_models(*, client, output_format, **kwargs)
```

Show information about models within the repository

<a id="nrp_invenio_client.cli.files"></a>

# nrp\_invenio\_client.cli.files

<a id="nrp_invenio_client.cli.alias"></a>

# nrp\_invenio\_client.cli.alias

<a id="nrp_invenio_client.cli.alias.list_aliases"></a>

#### list\_aliases

```python
@list_group.command(name="aliases")
@with_output_format()
@with_config()
def list_aliases(config: NRPConfig, output_format)
```

List known repositories

<a id="nrp_invenio_client.cli.alias.add_alias"></a>

#### add\_alias

```python
@add_group.command(name="alias")
@click.argument("servername")
@click.argument("alias", required=False)
@click.option("--default",
              is_flag=True,
              default=False,
              help="Set this repository as the default")
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
@click.option("--verify/--no-verify",
              default=True,
              help="Verify the repository certificate")
@with_config()
def add_alias(config: NRPConfig, alias, servername, default, token, skip_token,
              verify)
```

Add a new repository to the configuration

servername   ... servername or url of the repository (myrepo.mycompany.com, https://myrepo.mycompany.com)

alias        ... local alias to the repository, if not specified, the servername is used

<a id="nrp_invenio_client.cli.alias.select_repository"></a>

#### select\_repository

```python
@select_group.command(name="alias")
@click.argument("alias")
@with_config()
def select_repository(config, alias)
```

Select a default repository

<a id="nrp_invenio_client.cli.alias.remove_alias"></a>

#### remove\_alias

```python
@remove_group.command(name="alias")
@click.argument("alias")
@with_config()
def remove_alias(config, alias)
```

Remove an alias to a repository

<a id="nrp_invenio_client.cli"></a>

# nrp\_invenio\_client.cli

Commandline interface for the nrp-invenio-client.

<a id="nrp_invenio_client.cli.utils"></a>

# nrp\_invenio\_client.cli.utils

<a id="nrp_invenio_client.cli.record"></a>

# nrp\_invenio\_client.cli.record

<a id="nrp_invenio_client.cli.record.get_record"></a>

#### get\_record

```python
@get_group.command(name="record")
@click.option("-o",
              "--output-file",
              help="Output file, might use placeholders")
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
def get_record(config: NRPConfig, client: NRPInvenioClient, *, records_ids,
               output_file, include_files, include_requests, overwrite,
               output_format, **kwargs)
```

Retrieve a single record or a list of records given by id. The id can be of the following form:

* mid (model/id within model)
* id without model together with --model option (or without if there is just a single model inside the repository)
* full url (API or HTML)
* doi of the record

<a id="nrp_invenio_client.cli.search"></a>

# nrp\_invenio\_client.cli.search

<a id="nrp_invenio_client.cli.search.search_records"></a>

#### search\_records

```python
@search_group.command(name="records")
@search_decorator
def search_records(**kwargs)
```

Searches within records. You can either specify just a search query or
restrict to models of certain type, status (published or draft) or records belonging
to you.

<a id="nrp_invenio_client.cli.search.list_records"></a>

#### list\_records

```python
@list_group.command(name="records")
@search_decorator
def list_records(**kwargs)
```

Lists records. You can also specify search query or
restrict the listing to models of certain type,
status (published or draft) or records belonging to you.

<a id="nrp_invenio_client.cli.set"></a>

# nrp\_invenio\_client.cli.set

<a id="nrp_invenio_client.cli.base"></a>

# nrp\_invenio\_client.cli.base

<a id="nrp_invenio_client.cli.base.add_group"></a>

#### add\_group

```python
@nrp_command.group(name="add")
def add_group()
```

Add stuff - run without arguments to see what can be added.

<a id="nrp_invenio_client.cli.base.select_group"></a>

#### select\_group

```python
@nrp_command.group(name="select")
def select_group()
```

Select stuff - run without arguments to see what can be selected.

<a id="nrp_invenio_client.cli.base.remove_group"></a>

#### remove\_group

```python
@nrp_command.group(name="remove")
def remove_group()
```

Remove stuff - run without arguments to see what can be removed.

<a id="nrp_invenio_client.cli.base.list_group"></a>

#### list\_group

```python
@nrp_command.group(name="list")
def list_group()
```

List stuff - run without arguments to see what can be listed.

<a id="nrp_invenio_client.cli.base.search_group"></a>

#### search\_group

```python
@nrp_command.group(name="search")
def search_group()
```

Search stuff - run without arguments to see what can be searched.

<a id="nrp_invenio_client.cli.base.describe_group"></a>

#### describe\_group

```python
@nrp_command.group(name="describe")
def describe_group()
```

Describe repository, models, ... - run without arguments to see what can be described.

<a id="nrp_invenio_client.cli.base.get_group"></a>

#### get\_group

```python
@nrp_command.group(name="get")
def get_group()
```

Get stuff from repository - run without arguments to see what can be gotten.

<a id="nrp_invenio_client.cli.base.create_group"></a>

#### create\_group

```python
@nrp_command.group(name="create")
def create_group()
```

Create stuff in repository - run without arguments to see what can be created.

<a id="nrp_invenio_client.cli.base.update_group"></a>

#### update\_group

```python
@nrp_command.group(name="update")
def update_group()
```

Update stuff in repository - run without arguments to see what can be updated.

<a id="nrp_invenio_client.cli.base.delete_group"></a>

#### delete\_group

```python
@nrp_command.group(name="delete")
def delete_group()
```

Delete stuff - run without arguments to see what can be removed.

<a id="nrp_invenio_client.cli.base.upload_group"></a>

#### upload\_group

```python
@nrp_command.group(name="upload")
def upload_group()
```

Upload stuff - run without arguments to see what can be uploaded.

<a id="nrp_invenio_client.cli.base.set_group"></a>

#### set\_group

```python
@nrp_command.group(name="set")
def set_group()
```

Set stuff - run without arguments to see what can be set.

<a id="nrp_invenio_client.cli.base.download_group"></a>

#### download\_group

```python
@nrp_command.group(name="download")
def download_group()
```

Download stuff - run without arguments to see what can be downloaded.

<a id="nrp_invenio_client.cli.base.replace_group"></a>

#### replace\_group

```python
@nrp_command.group(name="replace")
def replace_group()
```

Replace stuff - run without arguments to see what can be replaced.

<a id="nrp_invenio_client.cli.output"></a>

# nrp\_invenio\_client.cli.output

<a id="nrp_invenio_client.utils"></a>

# nrp\_invenio\_client.utils

<a id="nrp_invenio_client.utils.is_doi"></a>

#### is\_doi

```python
def is_doi(record_id)
```

Returns true if the record_id is a DOI

**Arguments**:

- `record_id`: any string

**Returns**:

true if the record_id is a DOI

<a id="nrp_invenio_client.utils.is_url"></a>

#### is\_url

```python
def is_url(record_id)
```

Returns true if the record_id is a URL

**Arguments**:

- `record_id`: any string

**Returns**:

true if the record_id is a URL

<a id="nrp_invenio_client.utils.resolve_record_doi"></a>

#### resolve\_record\_doi

```python
def resolve_record_doi(config: "NRPConfig",
                       doi) -> Tuple["NRPInvenioClient", str]
```

Resolves the DOI and return a pair of the client and the API path within the client

<a id="nrp_invenio_client.utils.resolve_repository_url"></a>

#### resolve\_repository\_url

```python
def resolve_repository_url(config: "NRPConfig",
                           url) -> Tuple["NRPInvenioClient", str]
```

Resolves the URL and return a pair of the client and the API path within the client

**Arguments**:

- `config`: config of all known repositories
- `url`: URL of the record

**Returns**:

a pair of the client and the API path within the client

<a id="nrp_invenio_client.utils.is_mid"></a>

#### is\_mid

```python
def is_mid(record_id)
```

Returns true if the record_id is a mid (model+id)

**Arguments**:

- `record_id`: any string

**Returns**:

true if the record_id is a mid

<a id="nrp_invenio_client.utils.get_mid"></a>

#### get\_mid

```python
def get_mid(models: List[NRPModelInfo], data) -> Tuple[str, str]
```

Get a (model+id) from the data

**Arguments**:

- `models`: list of known models
- `data`: data from the record

**Returns**:

a pair (model, id)

<a id="nrp_invenio_client.utils.read_input_file"></a>

#### read\_input\_file

```python
def read_input_file(filename, format)
```

Reads the input file

**Arguments**:

- `filename`: path on filesystem, '-' for stdin or json string beginning with '{' or '['
- `format`: format of the file, if None, it is guessed from the filename

**Returns**:

content of the file parsed into a python json object (dict or list)

<a id="nrp_invenio_client.search"></a>

# nrp\_invenio\_client.search

<a id="nrp_invenio_client.search.NRPSearchRequest"></a>

## NRPSearchRequest Objects

```python
class NRPSearchRequest()
```

Search request builder. It allows to build a search query and execute it.
Do not instantiate this class directly, use `NRPInvenioClient.search` method instead.

<a id="nrp_invenio_client.search.NRPSearchRequest.execute"></a>

#### execute

```python
def execute() -> "NRPSearchResponse"
```

Executes the search query and returns the response.

<a id="nrp_invenio_client.search.NRPSearchRequest.scan"></a>

#### scan

```python
def scan()
```

Executes the search query in the scan mode, allowing to return more
than 10000 records. The result of this call must be used as a context manager,
for example:

query = ...
with query.scan() as results:
    for record in results:
        ...

<a id="nrp_invenio_client.search.NRPSearchRequest.page"></a>

#### page

```python
def page(page: int)
```

Fetch the specified page of results.

**Arguments**:

- `page`: page number, starting with 1

<a id="nrp_invenio_client.search.NRPSearchRequest.size"></a>

#### size

```python
def size(size: int)
```

The fetched pages will have this number of records.

**Arguments**:

- `size`: number of records per page

<a id="nrp_invenio_client.search.NRPSearchRequest.order_by"></a>

#### order\_by

```python
def order_by(*sort: str)
```

Sort the results by the specified fields.

**Arguments**:

- `sort`: fields to sort by. A field can have a '+/-' prefix to specify the sort order.

<a id="nrp_invenio_client.search.NRPSearchRequest.published"></a>

#### published

```python
def published()
```

Return only published records

<a id="nrp_invenio_client.search.NRPSearchRequest.drafts"></a>

#### drafts

```python
def drafts()
```

Return only draft records

<a id="nrp_invenio_client.search.NRPSearchRequest.query"></a>

#### query

```python
def query(query)
```

Set the search query. The query can be either a SOLR/Opensearch query string or a JSON query.

<a id="nrp_invenio_client.search.NRPSearchRequest.models"></a>

#### models

```python
@property
def models()
```

Models that will be searched within the query

<a id="nrp_invenio_client.search.NRPSearchBaseResponse"></a>

## NRPSearchBaseResponse Objects

```python
class NRPSearchBaseResponse()
```

Base class for search/scan responses

<a id="nrp_invenio_client.search.NRPSearchResponse"></a>

## NRPSearchResponse Objects

```python
class NRPSearchResponse(NRPSearchBaseResponse)
```

Search response. It is an iterable of NRPRecord objects.
This class is not intended to be instantiated directly, use `NRPSearchRequest.execute` method instead.

<a id="nrp_invenio_client.search.NRPSearchResponse.__iter__"></a>

#### \_\_iter\_\_

```python
def __iter__() -> typing.Iterator[NRPRecord]
```

Iterate over the records

<a id="nrp_invenio_client.search.NRPSearchResponse.links"></a>

#### links

```python
@property
def links()
```

Return the links section of the response, such as `next` or `prev` page.

<a id="nrp_invenio_client.search.NRPSearchResponse.total"></a>

#### total

```python
@property
def total()
```

Total number of found records

<a id="nrp_invenio_client.search.NRPScanResponse"></a>

## NRPScanResponse Objects

```python
class NRPScanResponse(NRPSearchBaseResponse)
```

Scan response. It is an iterable of NRPRecord objects but has to be used
as a context manager as it needs to be closed after the iteration.

Unlike search response, it does not return the total number of records
nor pagination links.

<a id="nrp_invenio_client.search.NRPScanResponse.__iter__"></a>

#### \_\_iter\_\_

```python
def __iter__() -> typing.Iterator[NRPRecord]
```

Iterate over the records

<a id="nrp_invenio_client.errors"></a>

# nrp\_invenio\_client.errors

<a id="nrp_invenio_client.requests"></a>

# nrp\_invenio\_client.requests

<a id="nrp_invenio_client.info"></a>

# nrp\_invenio\_client.info

<a id="nrp_invenio_client.info.NRPModelInfo"></a>

## NRPModelInfo Objects

```python
class NRPModelInfo()
```

Information about a model in the repository.

<a id="nrp_invenio_client.info.NRPModelInfo.name"></a>

#### name

```python
@property
def name()
```

Model name, used in all record's related calls

<a id="nrp_invenio_client.info.NRPModelInfo.schemas"></a>

#### schemas

```python
@property
def schemas()
```

A list of json schema identifiers that model's records must conform to.

<a id="nrp_invenio_client.info.NRPModelInfo.links"></a>

#### links

```python
@property
def links()
```

Links to the model's records, etc.

<a id="nrp_invenio_client.info.NRPModelInfo.description"></a>

#### description

```python
@property
def description()
```

Human description of the model

<a id="nrp_invenio_client.info.NRPModelInfo.version"></a>

#### version

```python
@property
def version()
```

Current model schema version

<a id="nrp_invenio_client.info.NRPModelInfo.features"></a>

#### features

```python
@property
def features()
```

A list of features implemented in the model (such as drafts, requests, ...)

<a id="nrp_invenio_client.info.NRPModelInfo.url"></a>

#### url

```python
@property
def url()
```

URL of model records

<a id="nrp_invenio_client.info.NRPModelInfo.user_url"></a>

#### user\_url

```python
@property
def user_url()
```

URL of model records belonging to the logged-in user (the user bearing the token)

<a id="nrp_invenio_client.info.NRPModelInfo.to_dict"></a>

#### to\_dict

```python
def to_dict()
```

Get a json representation of the model

<a id="nrp_invenio_client.info.NRPRepositoryInfo"></a>

## NRPRepositoryInfo Objects

```python
class NRPRepositoryInfo()
```

Information about the repository.

<a id="nrp_invenio_client.info.NRPRepositoryInfo.name"></a>

#### name

```python
@property
def name()
```

Repository name

<a id="nrp_invenio_client.info.NRPRepositoryInfo.description"></a>

#### description

```python
@property
def description()
```

Repository description

<a id="nrp_invenio_client.info.NRPRepositoryInfo.version"></a>

#### version

```python
@property
def version()
```

Version of the software of the repository

<a id="nrp_invenio_client.info.NRPRepositoryInfo.invenio_version"></a>

#### invenio\_version

```python
@property
def invenio_version()
```

Version of invenio libraries as aggregated in the `oarepo` package.

<a id="nrp_invenio_client.info.NRPRepositoryInfo.links"></a>

#### links

```python
@property
def links()
```

Links to models, ...

<a id="nrp_invenio_client.info.NRPRepositoryInfo.features"></a>

#### features

```python
@property
def features()
```

Features of the repository

<a id="nrp_invenio_client.info.NRPRepositoryInfo.transfers"></a>

#### transfers

```python
@property
def transfers()
```

Enabled binary data transfer types

<a id="nrp_invenio_client.info.NRPRepositoryInfo.to_dict"></a>

#### to\_dict

```python
def to_dict()
```

Get a json representation of the repository

<a id="nrp_invenio_client.info.NRPInfoApi"></a>

## NRPInfoApi Objects

```python
class NRPInfoApi()
```

Client API for invenio-based NRP repositories.

Accesses the info endpoint of the repository. As the information
returned is contained in a repository configuration (invenio.cfg),
or the code base itself, it is not expected to change at all.
That's why the information is cached.

If you need to update the information for whatever reason, create a new
NRPInvenioClient instance via the clone method.

<a id="nrp_invenio_client.info.NRPInfoApi.repository"></a>

#### repository

```python
@cached_property
def repository() -> NRPRepositoryInfo
```

Get information about the repository

<a id="nrp_invenio_client.info.NRPInfoApi.models"></a>

#### models

```python
@cached_property
def models() -> typing.List[NRPModelInfo]
```

Get information about the models in the repository

<a id="nrp_invenio_client.info.NRPInfoApi.get_model"></a>

#### get\_model

```python
def get_model(model_name: str)
```

Get information about a specific model in the repository

**Arguments**:

- `model_name`: name of the model

<a id="nrp_invenio_client.base"></a>

# nrp\_invenio\_client.base

<a id="nrp_invenio_client.base.ResponseFormat"></a>

## ResponseFormat Objects

```python
class ResponseFormat(Enum)
```

<a id="nrp_invenio_client.base.ResponseFormat.JSON"></a>

#### JSON

The response is expected to be JSON

<a id="nrp_invenio_client.base.ResponseFormat.RAW"></a>

#### RAW

The response is raw data, will return httpx.Response object

<a id="nrp_invenio_client.base.NRPInvenioClient"></a>

## NRPInvenioClient Objects

```python
class NRPInvenioClient()
```

Client API for invenio-based NRP repositories

<a id="nrp_invenio_client.base.NRPInvenioClient.__init__"></a>

#### \_\_init\_\_

```python
def __init__(server_url: str,
             token: str = None,
             verify: str | bool = True,
             retry_count=10,
             retry_interval=10,
             repository_config: NRPConfig = None)
```

Initialize the API client. Note: the parameters here are fixed for the lifetime of the client, can not be changed later.

**Arguments**:

- `server_url`: base url of the invenio server
- `token`: authentication token, can be skipped for anonymous access
- `verify`: verify the server certificate
- `retry_count`: number of retries for GET requests
- `retry_interval`: interval between retries for GET requests, if server does not respond with a Retry-After header

<a id="nrp_invenio_client.base.NRPInvenioClient.from_config"></a>

#### from\_config

```python
@classmethod
def from_config(
    cls,
    alias=None,
    config_or_config_file: Optional[str | Path | NRPConfig] = None
) -> "NRPInvenioClient"
```

Create a new NRPInvenioClient instance from a configuration file.

**Arguments**:

- `alias`: use this repository alias from the config file
- `config_or_config_file`: override the default location of the config file or pass the config object directly

**Returns**:

new NRPInvenioClient instance

<a id="nrp_invenio_client.base.NRPInvenioClient.search"></a>

#### search

```python
def search(models=None, **kwargs) -> NRPSearchResponse
```

Shortcut method for creating and executing a search request.

See NRPSearchRequest for more details.

**Arguments**:

- `models`: list of models, if none provided all models will be searched

**Returns**:

search response

<a id="nrp_invenio_client.base.NRPInvenioClient.scan"></a>

#### scan

```python
def scan(models=None, **kwargs) -> ContextManager[Iterable[JSON]]
```

Shortcut method for creating and executing a search request and returning all results.

See NRPSearchRequest for more details.

**Arguments**:

- `models`: list of models, if none provided all models will be searched

**Returns**:

generator of search results

<a id="nrp_invenio_client.base.NRPInvenioClient.clone"></a>

#### clone

```python
def clone()
```

Create a new NRPInvenioClient instance with the same parameters as this instance.

