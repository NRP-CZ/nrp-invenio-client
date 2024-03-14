class NRPInvenioClientError(Exception):
    def __init__(self, url, message):
        super().__init__(message)
        self.url = url


class NRPInvenioClientNotFoundError(NRPInvenioClientError):
    pass


class NRPInvenioClientInvalidContentTypeError(NRPInvenioClientError):
    def __init__(self, url, message, content_type):
        super().__init__(url, message)
        self.content_type = content_type


class NRPInvenioClientServerBusyError(NRPInvenioClientError):
    def __init__(self, url, message, retry_after):
        super().__init__(url, message)
        self.retry_after = retry_after


__all__ = (
    "NRPInvenioClientError",
    "NRPInvenioClientNotFoundError",
    "NRPInvenioClientInvalidContentTypeError",
    "NRPInvenioClientServerBusyError",
)
