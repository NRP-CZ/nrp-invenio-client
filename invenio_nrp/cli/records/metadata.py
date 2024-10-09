import json
import sys
from pathlib import Path


def read_metadata(metadata):
    if metadata == '-':
        # read metadata from stdin
        metadata = sys.stdin.read()
    pth = Path(metadata)
    if pth.exists():
        # metadata is path on filesystem
        metadata = pth.read_text()
    else:
        metadata = metadata.strip()
        if not (
                metadata.startswith("{") or
                metadata.startswith("[") or
                metadata == 'true' or
                metadata == 'false' or
                metadata == 'null' or
                metadata.isdigit() or
                metadata.startswith('"')
        ):
            metadata = f"\"{metadata}\""
    metadata = json.loads(metadata)
    return metadata
