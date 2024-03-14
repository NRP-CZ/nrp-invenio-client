import contextlib
import typing


if typing.TYPE_CHECKING:
    from nrp_invenio_client.records import NRPRecord

class FileAdapter:
    def __init__(self, stream):
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
    def __init__(self, *, record: "NRPRecord", key: str, data: typing.Any):
        self._record = record
        self._key = key
        self._data = data

    @property
    def metadata(self):
        return self._data.setdefault('metadata', {})

    @property
    def data(self):
        return self._data

    @property
    def key(self):
        return self._key

    @property
    def links(self):
        return self._data["links"]

    def delete(self):
        self._record.files.pop(self._key)
        self._record._client.delete(self.links["self"])

    def replace(self, stream):
        if self.data['status'] == 'completed':
            self.delete()
            md = self._record._client.post(
                self._record.links["files"], data=[{"key": self.key, **self.metadata}]
            )
            self._data = [x for x in md['entries'] if x['key'] == self.key][0]

        self._record._client.put(self.links["content"], data=stream)
        ret = self._record._client.post(self.links['commit'], data={})
        self._data = ret

    @contextlib.contextmanager
    def open(self):
        content_url = self.links["content"]
        with self._record._client.stream(content_url) as f:
            yield FileAdapter(f)


    def save(self):
        ret = self._record._client.put(self.links["self"], data=self.metadata)
        self._data = ret

    def to_dict(self):
        return self.data

class NRPRecordFiles(dict):
    def __init__(self, record: "NRPRecord", *args, **kwargs):
        self.record = record
        super().__init__(*args, **kwargs)

    def create(self, key, metadata, stream):
        md = self.record._client.post(
            self.record.links["files"], data=[{"key": key, **metadata}]
        )
        md = [x for x in md['entries'] if x['key'] == key][0]

        f = NRPFile(record=self.record, key=key, data=md)
        self[key] = f

        self.record._client.put(f.links["content"], data=stream)
        ret = self.record._client.post(f.links['commit'], data={})
        f._data = ret

        return f

    def to_dict(self):
        return [f.metadata for f in self.values()]
