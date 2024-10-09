#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""
Python module with high-level functions
for interacting with the NRP repositories
and plain invenio RDM.
"""


# from invenio_nrp.client.async_client import AsyncClient
# from invenio_nrp.types.record import RecordBase
# from invenio_nrp.types.requests import RequestBase

#
# async def get_records[
#     RecordBase, RequestBase
# ](
#     *,
#     record_urls: Optional[List[str | URL]] = None,
#     record_dois: Optional[List[str]] = None,
#     record_ids=None,
#     client=None,
#     alias=None,
# ) -> List[Union[RecordBase, AsyncRecordMixin[RecordBase, RequestBase]]]:
#     """
#     Get records from the repository in the fastest manner, using parallelism.
#
#     :param record_urls:   URLs of the records to get
#     :param record_ids:    IDs of the records to get. This needs the client parameter to be filled up.
#     :param record_dois:   DOIs of the records to get
#     :param client:        the client to use for the operation, required only for ids. Exclusive with alias.
#     :param alias:         alias of the repository to use. Exclusive with client.
#     :return:
#     """
#     raise NotImplementedError("Not implemented yet")
#
#
# def get_records_sync(
#     *,
#     record_urls: Optional[List[str | URL]] = None,
#     record_dois: Optional[List[str]] = None,
#     record_ids=None,
#     client=None,
#     alias=None,
# ):  # TODO: -> List[SyncRecord]:
#     """
#     Get records from the repository.
#
#     :param record_urls:   URLs of the records to get
#     :param record_ids:    IDs of the records to get. This needs the client parameter to be filled up.
#     :param record_dois:   DOIs of the records to get
#     :param client:        the client to use for the operation, required only for ids. Exclusive with alias.
#     :param alias:         alias of the repository to use. Exclusive with client.
#     :return:
#     """
#     raise NotImplementedError("Not implemented yet")
#
#
# class AsyncReadableStream(Protocol):
#     async def read(self, n: int) -> bytes: ...
#     async def seek(self, offset: int) -> None: ...
#     async def close(self) -> None: ...
#
#
# class FileFactory(Protocol):
#
#     def __call__(self, start_byte, end_byte) -> BinaryIO: ...
#
#
# @dataclasses.dataclass
# class UploadedRecordFile:
#     record: Union[RecordBase, AsyncRecordMixin[RecordBase, RequestBase]]
#     key: str
#     metadata: Dict[str, any] = dataclasses.field(default_factory=dict)
#     transfer_metadata: Dict[str, any] = dataclasses.field(default_factory=dict)
#     file_size: Optional[int] = None
#     file_path: Optional[str] = None
#     file_content: Optional[bytes | AsyncReadableStream] = None
#     file_factory: Optional[FileFactory] = None
#
#
# async def upload_files(*files: List[UploadedRecordFile], replace=True):
#     """
#     Upload files to the repository, using parallel and multipart upload if supported by the repository.
#
#     :param      files: Files to upload, with metadata and transfer metadata
#     :param      replace: If True, replace the files if they already exist in the repository
#     :return:
#     """
#     raise NotImplementedError("Not implemented yet")
