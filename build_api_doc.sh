#!/bin/bash

source .venv/bin/activate

pydoc-markdown -I src -p nrp_invenio_client --render-toc > docs/api.md