"""
Presentation layer for Shusha 2: ttkbootstrap UI shell, components, and views.
"""

from shusha.presentation.app_context import AppContext
from shusha.presentation.components import (
    AppSidebar,
    AppStatusBar,
    AppToolbar,
    BaseDialog,
    BaseFrame,
    DownloadTable,
)
from shusha.presentation.dispatcher import UiDispatcher
from shusha.presentation.views import MainWindow

__all__ = [
    "AppContext",
    "AppSidebar",
    "AppStatusBar",
    "AppToolbar",
    "BaseDialog",
    "BaseFrame",
    "DownloadTable",
    "MainWindow",
    "UiDispatcher",
]
