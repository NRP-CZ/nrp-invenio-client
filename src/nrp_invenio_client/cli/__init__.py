import nrp_invenio_client.cli.alias  # noqa
import nrp_invenio_client.cli.describe  # noqa
import nrp_invenio_client.cli.record  # noqa
import nrp_invenio_client.cli.search  # noqa
import nrp_invenio_client.cli.files   # noqa
import nrp_invenio_client.cli.set     # noqa

from .base import nrp_command

__all__ = ("nrp_command",)
