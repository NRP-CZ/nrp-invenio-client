"""
Commandline interface for the nrp-invenio-client.
"""

import nrp_invenio_client.cli.commands  # noqa

from .base import nrp_command

__all__ = ("nrp_command",)
