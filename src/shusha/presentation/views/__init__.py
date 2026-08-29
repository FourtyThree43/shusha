"""
Presentation views and modal dialogs for Shusha 2.
"""

from shusha.presentation.views.add_download_dialog import AddDownloadDialog
from shusha.presentation.views.batch_add_dialog import (
    BatchAddDialog,
    expand_batch_pattern,
)
from shusha.presentation.views.create_torrent_dialog import (
    CreateTorrentDialog,
    bencode,
    generate_torrent_file,
)
from shusha.presentation.views.inspector_dialog import InspectorDialog
from shusha.presentation.views.main_window import MainWindow
from shusha.presentation.views.settings_dialog import SettingsDialog

__all__ = [
    "AddDownloadDialog",
    "BatchAddDialog",
    "CreateTorrentDialog",
    "InspectorDialog",
    "MainWindow",
    "SettingsDialog",
    "bencode",
    "expand_batch_pattern",
    "generate_torrent_file",
]
