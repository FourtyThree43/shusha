"""
Strongly typed aria2 RPC client adapters, options registry, and WebSocket transport for Shusha 2.
"""

from shusha.infrastructure.aria2.client import Aria2Client, RpcTransport
from shusha.infrastructure.aria2.errors import (
    Aria2AuthenticationError,
    Aria2ConnectionError,
    Aria2EngineError,
    Aria2OptionValidationError,
    Aria2ProtocolError,
    Aria2RpcError,
)
from shusha.infrastructure.aria2.jsonrpc import JsonRpcTransport
from shusha.infrastructure.aria2.option_registry import OptionDefinition, OptionRegistry
from shusha.infrastructure.aria2.parsers import (
    map_aria2_status_to_state,
    parse_download_file,
    parse_download_source,
    parse_download_status,
    parse_global_stat,
    parse_peer,
    parse_server,
)
from shusha.infrastructure.aria2.ws_client import Aria2WebSocketClient
from shusha.infrastructure.aria2.xmlrpc import XmlRpcTransport

__all__ = [
    "Aria2AuthenticationError",
    "Aria2Client",
    "Aria2ConnectionError",
    "Aria2EngineError",
    "Aria2OptionValidationError",
    "Aria2ProtocolError",
    "Aria2RpcError",
    "Aria2WebSocketClient",
    "JsonRpcTransport",
    "OptionDefinition",
    "OptionRegistry",
    "RpcTransport",
    "XmlRpcTransport",
    "map_aria2_status_to_state",
    "parse_download_file",
    "parse_download_source",
    "parse_download_status",
    "parse_global_stat",
    "parse_peer",
    "parse_server",
]
