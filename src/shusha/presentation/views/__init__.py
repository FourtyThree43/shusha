"""Presentation views, dashboard, and modal dialogs for Shusha."""

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
from shusha.presentation.views.dashboard_view import DashboardView
from shusha.presentation.views.doctor_view import DoctorView
from shusha.presentation.views.inbox_view import AcquisitionInboxView
from shusha.presentation.views.inspector_dialog import InspectorDialog
from shusha.presentation.views.main_window import MainWindow
from shusha.presentation.views.media_grabber_dialog import MediaGrabberDialog
from shusha.presentation.views.plugins_dialog import PluginsDialog
from shusha.presentation.views.settings_dialog import SettingsDialog

__all__ = [
    "AcquisitionInboxView",
    "AddDownloadDialog",
    "BatchAddDialog",
    "CreateTorrentDialog",
    "DashboardView",
    "DoctorView",
    "InspectorDialog",
    "MainWindow",
    "MediaGrabberDialog",
    "PluginsDialog",
    "SettingsDialog",
    "bencode",
    "expand_batch_pattern",
    "generate_torrent_file",
]
