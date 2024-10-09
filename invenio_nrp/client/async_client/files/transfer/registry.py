#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Registry of known transfer types."""
from typing import Type

from ..files import TransferType
from .base import Transfer


class TransferRegistry:
    """Registry of known transfer types."""

    def __init__(self):
        """
        Initialize the registry.
        """
        self.transfers = {}

    def register(self, transfer_type: TransferType, transfer: Type[Transfer]):
        """
        Register a transfer type.

        :param transfer_type:       transfer type
        :param transfer:            registered transfer
        """
        self.transfers[transfer_type] = transfer

    def get(self, transfer_type: TransferType) -> Transfer:
        """
        Get a transfer for a transfer type

        :param transfer_type:       transfer type
        :return:                    instance of a transfer
        """
        return self.transfers[transfer_type]()


transfer_registry = TransferRegistry()
"""Singleton for the transfer registry"""

#
# supported transfers are registered here
#
from .local import LocalTransfer

transfer_registry.register(TransferType.LOCAL, LocalTransfer)