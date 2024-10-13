#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""A downloader for potentially large files.

Its primary use is to download files from the NRP Invenio API and save them to a local file,
but can be used for any other download as well.

Usage:

with Downloader(progress=ProgressBar(), auth=SomeAuth()) as downloader:
    downloader.add(url="https://example.com/file", sink=FileSink(Path("output.txt")))
"""

from .downloader import Downloader
from .progress import ProgressKeeper
from .progress_bar import ProgressBar

__all__ = ["ProgressKeeper", "ProgressBar", "Downloader"]
