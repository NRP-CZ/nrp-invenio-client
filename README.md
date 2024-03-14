

### Getting record

To get record metadata, invoke

```bash
nrp-command get record <pid>
```

The command will output the record to stdout, for example in yaml:

```yaml
id: 1
mid: datasets/1
links:
  self: https://myserver.cesnet.cz/api/datasets/1
  self_html: https://myserver.cesnet.cz/datasets/1
metadata:
  title: My dataset
```

You can specify additional parameters:

* `-o`, `--output-file fn` - will save the record as this output file
* `--files` - will add a list of files to the output
* `--requests` - will add a list of requests to the output
* `--format` - will change the output format to `json` or `yaml`
* `--overwrite` - will overwrite the output file if it already exists

The value of the `--output-file` can contain placeholders `{model}` and `{id}` which
will be replaced with the model name and the record id. The placeholders can also
reference metadata from within the record, such as `{metadata.title}.json`. 
Subdirectories are allowed within the `--output-file` and will be created if necessary.

If the output file already exists, an error will be raised.

#### Getting multiple records at once

To get multiple records at once, invoke:

```bash
nrp-command get record <pid1> <pid2> ...
```

If you do not use the `-o/--output-file` option, the records will be output to stdout
as an json array/yaml multidoc. With `-o`, the records will be saved to the specified file/files.
With placeholders, each record will be saved to a separate file. Without them, the records
will be saved as a json array/yaml multidoc.

If the output file already exists, an error will be raised.

#### Downloading complete record with files

To download all files with the record, specify `--with-files` option. For example:

```bash
nrp-command get record <pid> --with-files -o <pattern>
```

will create the following structure:

```text
+ `dirname(outfile)`
  + outfile
  + file1.txt
  + file2.pdf
```

If the file already exists, an error will be raised.

#### Downloading a single file

If you'd like to get a single file, specify the `--file` option. The file will get
downloaded to the specified `-o` file. If you do not specify the output file,
the file will be output to stdout.

```bash
nrp-command get file <pid> <file_key> -o <outfile>

# or

nrp-command get file <pid>/<file_key> -o <outfile>

# or

nrp-command get file <file url> -o <outfile>
```

#### Parallel downloading

To download file(s) in parallel, use `--parallel n` option.

```bash
nrp-command get file <pid> <file_key> --parallel 10 -o <outfile>
```

## Creating a record

To create a record, invoke:

```bash
nrp-command create record <model>
metadata are comming here
^D (Ctrl+D)
``` 

The metadata can also be entered with the `--metadata` option:

```bash
nrp-command create record <model> --metadata <metadata_file>
```

The command will output the id of the created record in the form of `<model>/<id>`
along with `Location` http header.

### Attaching files to the record

To attach files to the record, you can either use the `create file` command
or the `--file` (and --file-metadata) option of `create model`:

```bash
nrp-command create record <model> --file <file1> ...
```

or 

```bash
nrp-command create file <model>/<id> --file file --file-metadata <metadata_file>
```

Note: you can only attach files to a record which has not been submitted yet.

### Updating a record

To update a record, invoke:

```bash
nrp-command update record <model>/<id>
metadata are comming here in the defined format
^D (Ctrl+D)
```

As in `create` command, you can also specify the metadata using the `--metadata` option.

### Deleting a record

To delete a record, invoke:

```bash
nrp-command delete record <alias> <model>/<id>
```

This will delete the record and all its files. It can only
be used on draft records.

To delete a published record, use the request commandline
client described below.

### Submitting the record

To submit the record, invoke:

```bash
nrp-command submit record <alias> <model>/<id>
```

This will change the record status to `submitted`, all modifications will be prevented
and either curators/reviewers will be notified that a record is waiting for their approval
or the record will be published immediately, depending on the repository configuration.

### Editing the record

To edit an already published record, invoke:

```bash
nrp-command edit record <alias> <model>/<id>
```

The command will return an id of a new draft record which can be edited and submitted again.

### Requests

A list of possible requests for a record can be accessed via
the `--requests` option of the `get` command. Each request
contains a set of actions which can be performed by the
current user on the record.

#### Creating a new request

To create a new request, use the request name without any action:

```bash
nrp-command create request datasets/1 publish
<request payload goes here>

# or

nrp-command create request datasets/1 publish --payload <request payload>
```

The command will return the id of the created request together with the `Location` header.
The returned id will be in the form of `<model>/<record_id>/<request_id>`, for example `datasets/1/1231`.

#### Adding an event to a request (comment etc.)

To add an event to a request, invoke:

```bash
nrp-command create event <record_id>/<request_id> <eventtype>
<event payload>

# or 

nrp-command create event <record_id>/<request_id> <eventtype> --payload <event payload>

# Example:

nrp-command create event datasets/1/1231 comment
{
  "text": "My comment"
  "format": "html"
}
```

#### Approving/Denying a request

The command will return the id of the created event together with the `Location` header.

To perform an action, invoke:

```bash
nrp-command <action> request <model>/<id> <request_name>
```

To approve a request, invoke:

```bash
nrp-command approve request datasets/1 review -m "Looks good to me"
```

To decline it, invoke:

```bash
nrp-command request datasets/1 review decline
Please fix the following issues:

1. ...
2. ...
^D (Ctrl+D)
``` 

To create a new request, use the request name without any action:

```bash
nrp-command request datasets/1 revoke
```

In place of record identifier and request name you can use
the request url:

```bash
nrp-command request https://myserver.cesnet.cz/api/datasets/1/requests/review approve
```


