import contextlib
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import ttkbootstrap as ttk

from shusha.controller.api import ShushaAPI
from shusha.models.structs_downloads import Download
from shusha.models.structs_stats import Stats
from shusha.views.app import Aria2Gui, relative_to_assets


class TestAppActions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = ttk.Window(themename="bootstrap-dark")
            cls.root.withdraw()
            cls.has_display = True
        except Exception:
            cls.has_display = False

    @classmethod
    def tearDownClass(cls):
        if cls.has_display and hasattr(cls, "root") and cls.root:
            with contextlib.suppress(Exception):
                cls.root.destroy()

    def setUp(self):
        if not self.has_display:
            self.skipTest("No display available for Tkinter GUI test")

        self.mock_api = MagicMock(spec=ShushaAPI)
        self.mock_api.client = MagicMock()
        self.app = Aria2Gui(self.root, api=self.mock_api)

    def tearDown(self):
        if hasattr(self, "app"):
            with contextlib.suppress(Exception):
                self.app.destroy()

    def test_relative_to_assets(self):
        p = relative_to_assets("icons8-add-64.png")
        self.assertIsInstance(p, Path)

    def test_initialization_and_widgets(self):
        self.assertIsNotNone(self.app.buttonbar)
        self.assertIsNotNone(self.app.table_lf)
        self.assertIsNotNone(self.app.dt)
        self.assertIsNotNone(self.app.bottom_bar)
        self.assertIsNotNone(self.app.context_menu)

    def test_update_stats_frame(self):
        stats = Stats.from_dict({
            "downloadSpeed": "1048576",
            "uploadSpeed": "524288",
            "numActive": "2",
            "numWaiting": "1",
            "numStopped": "5",
        })
        self.app.update_stats_frame(stats)
        self.assertIn("1.00 MiB/s", self.app.stats_vars["Download Speed"].get())
        self.assertIn("512.00 KiB/s", self.app.stats_vars["Upload Speed"].get())

    def test_get_selected_downloads_and_single(self):
        mock_dl1 = MagicMock(spec=Download)
        mock_dl1.gid = "gid1"
        mock_dl2 = MagicMock(spec=Download)
        mock_dl2.gid = "gid2"

        self.app.downloads_map = {"gid1": mock_dl1, "gid2": mock_dl2}

        with patch.object(self.app.dt, "get_rows") as mock_get_rows:
            mock_row1 = MagicMock()
            mock_row1.values = ["file1.zip", "10 MB", "100%", "Active", "1 MB/s", "10s", "gid1"]
            mock_row2 = MagicMock()
            mock_row2.values = ["file2.iso", "100 MB", "50%", "Active", "2 MB/s", "30s", "gid2"]

            mock_get_rows.return_value = [mock_row1, mock_row2]

            selected = self.app.get_selected_downloads()
            self.assertEqual(len(selected), 2)
            self.assertEqual(selected[0].gid, "gid1")

            single = self.app.get_selected_download()
            self.assertIsNotNone(single)
            assert single is not None
            self.assertEqual(single.gid, "gid1")

    def test_start_and_pause_selected_downloads(self):
        mock_dl = MagicMock(spec=Download)
        mock_dl.gid = "gid_action"
        self.app.downloads_map = {"gid_action": mock_dl}

        with patch.object(self.app, "get_selected_downloads", return_value=[mock_dl]):
            self.app._start_downloads_bg([mock_dl])
            self.mock_api.resume.assert_called_with("gid_action")

            self.app._pause_downloads_bg([mock_dl])
            self.mock_api.pause.assert_called_with("gid_action")

    def test_remove_selected_download_with_and_without_files(self):
        mock_dl = MagicMock(spec=Download)
        mock_dl.gid = "gid_remove"

        self.app._remove_downloads_bg([mock_dl], files=False)
        self.mock_api.remove.assert_called_with("gid_remove", files=False)

        self.app._remove_downloads_bg([mock_dl], files=True)
        self.mock_api.remove.assert_called_with("gid_remove", files=True)

    def test_queue_actions(self):
        with patch("threading.Thread") as mock_thread:
            self.app.start_queue()
            self.app.pause_queue()
            self.app.clear_queue()
            self.assertEqual(mock_thread.call_count, 3)

    def test_move_download_up_and_down(self):
        mock_dl = MagicMock(spec=Download)
        mock_dl.gid = "gid_move"

        with patch.object(self.app, "get_selected_download", return_value=mock_dl):
            self.app.move_download_up()
            self.mock_api.client.change_position.assert_called_with("gid_move", -1, "POS_CUR")

            self.app.move_download_down()
            self.mock_api.client.change_position.assert_called_with("gid_move", 1, "POS_CUR")

    def test_category_matching_and_filtering(self):
        mock_active = MagicMock(spec=Download)
        mock_active.status = "active"
        mock_active.is_active = True
        mock_active.is_complete = False
        mock_active.is_paused = False
        mock_active.has_failed = False
        mock_active.gid = "g_act"
        mock_active.name = "active.bin"
        mock_active.total_length_string.return_value = "1 MB"
        mock_active.progress_string.return_value = "10%"
        mock_active.download_speed_string.return_value = "100 KB/s"
        mock_active.eta_string.return_value = "10s"

        mock_complete = MagicMock(spec=Download)
        mock_complete.status = "complete"
        mock_complete.is_active = False
        mock_complete.is_complete = True
        mock_complete.is_paused = False
        mock_complete.has_failed = False
        mock_complete.gid = "g_comp"
        mock_complete.name = "complete.bin"
        mock_complete.total_length_string.return_value = "5 MB"
        mock_complete.progress_string.return_value = "100%"
        mock_complete.download_speed_string.return_value = "0 B/s"
        mock_complete.eta_string.return_value = "0s"

        self.mock_api.get_downloads.return_value = [mock_active, mock_complete]

        self.app.active_category = "Downloading"
        self.app._refresh_downloads_bg()

        self.app.active_category = "Completed"
        self.app._refresh_downloads_bg()

        self.app.active_category = "Paused"
        self.app._refresh_downloads_bg()

        self.app.active_category = "Waiting"
        self.app._refresh_downloads_bg()

        self.app.active_category = "Error"
        self.app._refresh_downloads_bg()

        self.app.active_category = "Inactive"
        self.app._refresh_downloads_bg()

        self.app.active_category = "All"
        self.app._refresh_downloads_bg()

    def test_open_windows_and_dialogs(self):
        with (
            patch("shusha.views.app.AddWindow") as mock_add_win,
            patch("shusha.views.app.UriManagerWindow") as mock_uri_win,
            patch("shusha.views.app.DownloadWindow") as mock_dl_win,
            patch("shusha.views.app.TorrentFilesWindow") as mock_tor_win,
            patch("shusha.views.app.SettingsWindow") as mock_set_win,
            patch("shusha.views.app.open_path_in_file_manager") as mock_open_path,
        ):
            mock_dl = MagicMock(spec=Download)
            mock_dl.gid = "gid_win"
            mock_dl.dir = Path("/tmp")
            mock_dl.files = [MagicMock(uris=[{"uri": "http://example.com/test.zip"}])]

            with patch.object(self.app, "get_selected_download", return_value=mock_dl):
                self.app.open_toplevel()
                mock_add_win.assert_called_once()

                self.app.open_uri_manager()
                mock_uri_win.assert_called_once()

                self.app.open_selected_details()
                mock_dl_win.assert_called_once()

                self.app.open_selective_files()
                mock_tor_win.assert_called_once()

                self.app.open_settings_window()
                mock_set_win.assert_called_once()

                self.app.open_selected_folder()
                mock_open_path.assert_called_once()

    def test_download_thread_and_table_row_addition(self):
        mock_dl = MagicMock(spec=Download)
        mock_dl.gid = "gid_add_tbl"
        mock_dl.name = "added_file.zip"
        mock_dl.status = "active"
        mock_dl.total_length_string.return_value = "10 MB"
        mock_dl.progress_string.return_value = "50%"
        mock_dl.download_speed_string.return_value = "1 MB/s"
        mock_dl.eta_string.return_value = "5s"
        mock_dl.is_complete = False
        mock_dl.has_failed = False

        self.mock_api.add_uris.return_value = mock_dl
        self.mock_api.get_downloads.return_value = [mock_dl]

        self.app.add_download_to_table(mock_dl)
        self.assertIn("gid_add_tbl", self.app.downloads_map)

        # Periodic row update test
        mock_row = MagicMock()
        mock_row.iid = "1"
        self.app.update_rows_periodically(mock_dl, mock_row)

    def test_context_menu_and_double_click(self):
        mock_dl = MagicMock(spec=Download)
        mock_dl.gid = "gid_ctx"
        mock_dl.name = "ctx.zip"

        with (
            patch.object(self.app, "get_selected_download", return_value=mock_dl),
            patch.object(self.app, "open_selected_details") as mock_open_det,
        ):
            event = MagicMock()
            event.x_root = 100
            event.y_root = 100
            self.app.show_context_menu(event)

            self.app.on_double_click_row(event)
            mock_open_det.assert_called_once()

    def test_copy_selected_link(self):
        mock_dl = MagicMock(spec=Download)
        mock_dl.files = [MagicMock(uris=[{"uri": "http://example.com/download.zip"}])]

        with patch.object(self.app, "get_selected_download", return_value=mock_dl):
            self.app.copy_selected_link()

    def test_tray_minimization_and_restore(self):
        self.app.minimize_to_tray()
        self.app.restore_from_tray()

    def test_show_toast(self):
        with patch("shusha.views.app.ToastNotification") as mock_toast:
            self.app.show_toast("Test notification")
            mock_toast.assert_called_once()


if __name__ == "__main__":
    unittest.main()
