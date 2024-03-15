"""
Commandline interface for the nrp-invenio-client.
"""

from .base import nrp_command

import nrp_invenio_client.cli.commands # noqa

__all__ = ("nrp_command",)
