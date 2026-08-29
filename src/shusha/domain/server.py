"""
Connected server model for HTTP/FTP/SFTP downloads in Shusha 2.
"""

from dataclasses import dataclass

from shusha.domain.values import BitRate, Uri


@dataclass(frozen=True, slots=True)
class Server:
    """Connected HTTP/FTP/SFTP origin or mirror server."""

    uri: Uri
    current_uri: Uri
    download_speed: BitRate
