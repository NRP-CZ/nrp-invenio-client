import contextlib
import typing

import httpx

if typing.TYPE_CHECKING:
    from nrp_invenio_client.records import NRPRecord


class FileAdapter:
    """
    Adapter to convert httpx stream to file-like object
    """

    def __init__(self, stream: httpx.Response):
        self.stream = stream
        self.iterator = None

    def read(self, size):
        if self.iterator is None:
            self.iterator = self.stream.iter_bytes(size)
        try:
            return next(self.iterator)
        except StopIteration:
            return b""

    def close(self):
        self.stream.close()


class NRPFile:
    """
    File object for NRPRecord. It contains the metadata and links of the file
    stored inside the repository.
    """

    def __init__(self, *, record: "NRPRecord", key: str, data: typing.Any):
        """
        Creates a new instance, usually not called directly.

        :param record:    the record to which the file belongs
        :param key:       the key of the file (filename)
        :param data:      the metadata and links of the file
        """
        self._record = record
        self._key = key
        self._data = data

    @property
    def metadata(self):
        """
        Returns the metadata of the file (the content of metadata element).
        """
        return self._data.setdefault("metadata", {})

    @property
    def data(self):
        """
        Returns the whole data of the file (metadata, links, technical metadata).
        """
        return self._data

    @property
    def key(self):
        """
        File key
        """
        return self._key

    @property
    def links(self):
        """
        The content of links section, such as "self" or "content"
        """
        return self._data["links"]

    def delete(self):
        """
        Deletes the file from the record and the repository.
        """
        self._record.files.pop(self._key)
        self._record._client.delete(self.links["self"])

    def replace(self, stream):
        """
        Replaces the content of the file with the new stream.
        """
        if self.data["status"] == "completed":
            self.delete()
            md = self._record._client.post(
                self._record.links["files"], data=[{"key": self.key, **self.metadata}]
            )
            self._data = [x for x in md["entries"] if x["key"] == self.key][0]

        self._record._client.put(self.links["content"], data=stream)
        ret = self._record._client.post(self.links["commit"], data={})
        self._data = ret

    @contextlib.contextmanager
    def open(self):
        """
        Return a file-like object (non-seekable) to read the content of the file from the repository
        """
        content_url = self.links["content"]
        with self._record._client.stream(content_url) as f:
            yield FileAdapter(f)

    def save(self):
        """
        Save the metadata of the file to the repository
        """
        ret = self._record._client.put(self.links["self"], data=self.metadata)
        self._data = ret

    def to_dict(self):
        """
        Get a json representation of the file
        """
        return self.data


class NRPRecordFiles(dict):
    """
    A dictionary-like object for the files of the NRPRecord.
    The keys are the "key" properties of files (mostly filenames),
    values are instances of NRPFile.
    """

    def __init__(self, record: "NRPRecord", *args, **kwargs):
        self.record = record
        super().__init__(*args, **kwargs)

    def create(self, key, metadata, stream):
        """
        Creates a new file in the repository

        :param key:         the key of the file. An exception will be risen if the key already exists
        :param metadata:    metadata section of the file, contains user-specific metadata
        :param stream:      the content of the file that will be uploaded to the repository
        :return:            the created file (instance of NRPFile)
        """
        md = self.record._client.post(
            self.record.links["files"], data=[{"key": key, **metadata}]
        )
        md = [x for x in md["entries"] if x["key"] == key][0]

        f = NRPFile(record=self.record, key=key, data=md)
        self[key] = f

        self.record._client.put(f.links["content"], data=stream)
        ret = self.record._client.post(f.links["commit"], data={})
        f._data = ret

        return f

    def to_dict(self):
        """
        Dumps all the files (their metadata, not binary content) to a json object
        """
        return [f.metadata for f in self.values()]
