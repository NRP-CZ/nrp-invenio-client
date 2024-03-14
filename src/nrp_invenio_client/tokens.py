import typing

if typing.TYPE_CHECKING:
    from nrp_invenio_client.base import NRPInvenioClient


class NRPTokensApi:
    def __init__(self, api: "NRPInvenioClient"):
        self.api = api

    def fetch_token(self, token_uuid: str):
        """
        Get Bearer token from a repository, based on the token_uuid.
        Note: this is a one-time operation, the token_uuid can be used only once.
        On network errors, the operation can not be retried and a new token request
        (and thus a new token_uuid) is needed.
        """
        return self.api.get(
            path="/api/tokens/{token_uuid}",
        )["token"]
