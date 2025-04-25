# services package
from .base_rpc import BaseRpc
from .odoo_client import get_client, find_data, create_data

__all__ = ["BaseRpc", "get_client", "find_data", "create_data"]
