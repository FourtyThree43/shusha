import threading
import tkinter as tk
from pathlib import Path
from typing import Any, Callable

import ttkbootstrap as ttk
from ttkbootstrap.tableview import TableRow, Tableview
from ttkbootstrap.toast import ToastNotification
from ttkbootstrap.tooltip import ToolTip

from shusha.controller.api import ShushaAPI as Api
from shusha.models.logger import LoggerService
from shusha.models.structs_downloads import Download
from shusha.models.structs_stats import Stats
from shusha.views.add_win import AddWindow
from shusha.views.status_win import DownloadWindow

logger = LoggerService(__name__)
SCRIPT_PATH = Path(__file__).parent
ASSETS_PATH = SCRIPT_PATH / Path("../resources/assets/")


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)


class Aria2Gui(ttk.Frame):
    """
    The main application window class.

    :param master: The parent widget.
    """

    def __init__(self, master):
        """
        Initializes the main application window and sets up various components and attributes.

        :param master: The parent widget.
        """
        super().__init__(master, padding=10)
        self.pack(fill=tk.BOTH, expand=tk.YES)

        self.api = Api()
        self.start_server()
        self.download_gid = None

        self.colors = ttk.Style().colors

        image_files = {
            "add-download": "icons8-add-64.png",
            "start-download": "icons8-circled-play-64.png",
            "pause-download": "icons8-pause-button-64.png",
            "refresh": "icons8-refresh-64.png",
            "move-up": "icons8-arrow-64.png",
            "move-down": "icons8-scroll-down-64.png",
            "remove-download": "icons8-remove-64.png",
            "logs": "icons8-log-64.png",
            "settings": "icons8-slider_2-64.png",
            "start-queue-": "icons8-circled-play-64.png",
            "pause-queue": "icons8-pause-button-64.png",
            "clear-queue": "icons8-clear-64.png",
            "queue-settings": "icons8-slider-64.png",
        }

        self.photoimages = []
        for key, val in image_files.items():
            _path = relative_to_assets(val)
            self.photoimages.append(ttk.PhotoImage(name=key, file=_path))

        self.create_buttonbar()
        self.create_table_view()
        self.create_bottom_bar()

        self.after(1000, self.get_stats)

    def create_buttonbar(self):
        """
        Create and configure the button bar with various action buttons and their respective tooltips.
        """
        # top buttonbar
        # header and labelframe buttonbar container
        self.buttonbar = ttk.Labelframe(self, text="Actions")
        self.buttonbar.pack(fill=tk.X, expand=tk.YES, anchor=tk.N)

        opts_row = ttk.Frame(self.buttonbar)
        opts_row.pack(fill=tk.X, expand=tk.YES)

        add_btn = ttk.Button(
            master=opts_row,
            text="Add",
            image="add-download",
            command=self.open_toplevel,
            width=8,
            bootstyle="outline-dark",
        )
        add_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(
            add_btn,
            text="Add new download",
            bootstyle=(ttk.WARNING, ttk.INVERSE),
        )

        start_btn = ttk.Button(
            master=opts_row,
            text="Start",
            image="start-download",
            command=lambda: DownloadWindow(api=self.api),
            width=8,
            bootstyle="outline-dark",
        )
        start_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(
            start_btn,
            text="Start downloads",
            bootstyle=(ttk.WARNING, ttk.INVERSE),
        )

        pause_btn = ttk.Button(
            master=opts_row,
            text="Pause",
            image="pause-download",
            command=self.stop_downloads,
            width=8,
            bootstyle="outline-dark",
        )
        pause_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(
            pause_btn,
            text="Pause downloads",
            bootstyle=(ttk.WARNING, ttk.INVERSE),
        )

        refresh_btn = ttk.Button(
            master=opts_row,
            text="Refresh",
            image="refresh",
            command=lambda: print("Refresh downloads list"),
            width=8,
            bootstyle="outline-dark",
        )
        refresh_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(
            refresh_btn,
            text="Refresh downloads list",
            bootstyle=(ttk.WARNING, ttk.INVERSE),
        )

        mvup_btn = ttk.Button(
            master=opts_row,
            text="Move Up",
            image="move-up",
            command=lambda: print("Move UP"),
            width=8,
            bootstyle="outline-dark",
        )
        mvup_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(
            mvup_btn,
            text="Move download up",
            bootstyle=(ttk.WARNING, ttk.INVERSE),
        )

        mvdown_btn = ttk.Button(
            master=opts_row,
            text="Move Down",
            image="move-down",
            command=lambda: print("Move Down"),
            width=8,
            bootstyle="outline-dark",
        )
        mvdown_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(
            mvdown_btn,
            text="Move download down",
            bootstyle=(ttk.WARNING, ttk.INVERSE),
        )

        rem_btn = ttk.Button(
            master=opts_row,
            text="Remove",
            image="remove-download",
            command=lambda: print("Remove downloads"),
            width=8,
            bootstyle="outline-dark",
        )
        rem_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(
            rem_btn,
            text="Remove downloads",
            bootstyle=(ttk.DANGER, ttk.INVERSE),
        )

        sett_btn = ttk.Button(
            master=opts_row,
            text="Settings",
            image="settings",
            command=lambda: print("Open Settings"),
            width=8,
            bootstyle="outline-dark",
        )
        sett_btn.pack(side=tk.RIGHT, padx=(0, 1), pady=1)
        ToolTip(
            sett_btn, text="Open settings", bootstyle=(ttk.WARNING, ttk.INVERSE)
        )

        logs_btn = ttk.Button(
            master=opts_row,
            text="Logs",
            image="logs",
            command=lambda: self.show_toast(),
            width=8,
            bootstyle="outline-dark",
        )
        logs_btn.pack(side=tk.RIGHT, padx=(0, 1), pady=1)
        ToolTip(
            logs_btn, text="Open logs", bootstyle=(ttk.WARNING, ttk.INVERSE)
        )

    def create_table_view(self):
        """
        Creates and populates a table view with the specified columns and row data.
        """
        self.table_lf = ttk.Labelframe(self, text="Downloads List")
        self.table_lf.pack(fill=tk.BOTH, expand=tk.YES, side=tk.TOP)

        _columns = [
            "Filename",
            "Status",
            "Size",
            "Progress",
            "Speed",
            "ETA",
            "Date",
            "Note",
        ]

        _rowdata = []

        # _downloads = self.api.get_downloads()
        # add items to download_list
        # for download in downloads:
        #     _rowdata.append((
        #         download.name,
        #         download.status,
        #         download.total_length_string(),
        #         download.progress_string(),
        #         download.download_speed_string(),
        #         download.eta_string(),
        #         download.bitfield,
        #         download.info_hash,
        #     ))

        self.dt = Tableview(
            master=self.table_lf,
            coldata=_columns,
            rowdata=_rowdata,
            paginated=True,
            searchable=True,
            bootstyle="warning",
            stripecolor=(self.colors.dark, None),
        )

        self.dt.pack(fill=tk.BOTH, expand=tk.YES, padx=10)

    def create_bottom_bar(self):
        """
        Create a bottom bar containing buttons and dropdowns for queue actions.
        """
        # bottom buttonbar
        # header and labelframe buttonbar container
        self.bottom_bar = ttk.Labelframe(self, text="Queue Actions")
        self.bottom_bar.pack(fill=tk.X, expand=tk.YES, anchor=tk.S)

        opts_row = ttk.Frame(self.bottom_bar)
        opts_row.pack(fill=tk.X, expand=tk.YES)
        _categories = [
            "All",
            "Active",
            "Completed",
            "Seeding",
            "Inactive",
            "Error",
            "Paused",
            "Queued",
        ]

        category = ttk.Combobox(master=opts_row, values=_categories, width=12)
        category.pack(side=ttk.LEFT, padx=10, pady=1)
        ToolTip(
            category,
            text="Select category",
            bootstyle=(ttk.WARNING, ttk.INVERSE),
        )

        start_btn = ttk.Button(
            master=opts_row,
            text="Start",
            image="start-queue-",
            command=lambda: print("start queue"),
            width=8,
            bootstyle="outline-dark",
        )
        start_btn.pack(side=ttk.LEFT, padx=(1, 0), pady=1)
        ToolTip(
            start_btn, text="Start queue", bootstyle=(ttk.WARNING, ttk.INVERSE)
        )

        pause_btn = ttk.Button(
            master=opts_row,
            text="Pause",
            image="pause-queue",
            command=lambda: print("pause queue"),
            width=8,
            bootstyle="outline-dark",
        )
        pause_btn.pack(side=ttk.LEFT, padx=(1, 0), pady=1)
        ToolTip(
            pause_btn, text="Pause queue", bootstyle=(ttk.WARNING, ttk.INVERSE)
        )

        refresh_btn = ttk.Button(
            master=opts_row,
            text="Clear",
            image="clear-queue",
            command=lambda: print("clear queue list"),
            width=8,
            bootstyle="outline-dark",
        )
        refresh_btn.pack(side=ttk.LEFT, padx=(1, 0), pady=1)
        ToolTip(
            refresh_btn,
            text="Clear queue list",
            bootstyle=(ttk.DANGER, ttk.INVERSE),
        )

        sett_btn = ttk.Button(
            master=opts_row,
            text="Queue Settings",
            image="queue-settings",
            command=lambda: print("Open Queue Settings"),
            width=8,
            bootstyle="outline-dark",
        )
        sett_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(
            sett_btn,
            text="Open queue settings",
            bootstyle=(ttk.WARNING, ttk.INVERSE),
        )

        self.stats_frame = tk.Frame(opts_row)
        self.stats_frame.pack(side=tk.RIGHT, padx=10, pady=10)

    def show_toast(self, message="This is a toast message"):
        """
        Show a toast notification with the given message.

        :param message: The message to display in the toast notification (default is "This is a toast message")
        :return: None
        """
        toast = ToastNotification(
            title="ttkbootstrap toast message",
            message=message,
            duration=3000,
        )

        toast.show_toast()

    def _thread(self, target: Callable, *args: Any) -> None:
        """
        Helper method to run the target function in a separate thread.

        :param target: (Callable) The function to be run in a separate thread.
        :param args: (Any) The arguments for the target function.
        :return: None
        """
        threading.Thread(target=target, args=args, daemon=True).start()

    def stats_thread(self):
        """
        Method to perform the statistics and execute the stats_thread function.
        """
        try:
            global_stats = self.api.get_stats()
            self.update_stats_frame(global_stats)

            self.after(1000, self.stats_thread)
        except Exception as e:
            self.log_error(f"Error in get_stats: {e}")

    def get_stats(self):
        """
        Method to perform the statistics and execute the stats_thread function.
        """
        self._thread(self.stats_thread)

    def update_stats_frame(self, global_stats: Stats):
        """
        Method to update the stats frame.

        :param global_stats: (Stats) The Stats object to be updated.
        """
        stats_info = {
            "Download Speed": global_stats.download_speed_string(),
            "Active": global_stats.num_active,
            "Waitting": global_stats.num_waiting,
            "Stopped": global_stats.num_stopped,
            "Total Stopped": global_stats.num_stopped_total,
            "Upload Speed": global_stats.upload_speed_string(),
        }

        column_index = 0
        for key, value in stats_info.items():
            label = tk.Label(self.stats_frame, text=f"{key}:")
            label.grid(row=0, column=column_index, sticky="w", padx=5)

            value_label = tk.Label(self.stats_frame, text=value)
            value_label.grid(row=1, column=column_index, sticky="e", padx=5)

            column_index += 1

    def open_toplevel(self):
        """
        Method to open the AddWindow in a separate toplevel window.
        """

        def handle_result(uris: list[tk.StringVar], options: dict):
            """
            Callback function for the AddWindow.

            :param uris: (list[tk.StringVar]) The list of URIs to be downloaded.
            :param options: (dict) The options for the download.
            :return: None
            """

            for uri in uris:
                # self._thread(self.download_thread, uri, options)
                self.download_thread(uri, options)

        # create a new toplevel window
        AddWindow(callback=handle_result)

    def download_thread(self, uri, options: dict):
        """
        Method to start a download in a separate thread.

        :param uri: (str) The URI to be downloaded.
        :param options: (dict) The options for the download.
        :return: None
        """
        try:
            uris = []
            uris.append(str(uri.get()))

            download = self.api.add_uris(uris, options)

            if download:
                msg = f"Added Dowload: {download.name}"
                self.show_toast(message=msg)

                download_window = DownloadWindow(api=self.api)
                download_window.update_stats_frame(download)

                self.add_download_to_table(download)

        except Exception as e:
            self.log_error(f"Error starting download: {e}")

    def add_download_to_table(self, download: Download):
        """
        Method to add a download to the table.

        :param download: (Download) Download object to be added to the table.
        """
        if self.dt:
            data = self.get_download_row_data(download)
            _row = self.dt.insert_row(index="end", values=data)
            self.dt.load_table_data()

            if not download.is_complete and not download.has_failed:
                self.after(1000, self.update_rows_periodically, download, _row)

        else:
            self.log_info("Tableview not found. Skipping update...")

    def update_rows_periodically(self, download: Download, _row: TableRow):
        """
        Method to update the rows periodically.

        :param download: (Download) The download object to be updated.
        :param _row: (TableRow) The TableRow object to be updated.
        """
        if download.gid is None or download.is_complete or download.has_failed:
            return
        
        download.update()
        
        new_data = self.get_download_row_data(download)
        _row.configure(iid=_row.iid, values=new_data)
        self.dt.load_table_data()

        self.after(1000, self.update_rows_periodically, download, _row)

    def get_download_row_data(self, download: Download):
        """
        Method to get the download row data.

        :param download: (Download) The download object to be updated.
        :return: (tuple) The tuple of values for the download row.
        """
        return [
            download.name,
            download.status,
            download.total_length_string(),
            download.progress_string(),
            download.download_speed_string(),
            download.eta_string(),
            download.bitfield,
            download.info_hash,
        ]

    def pause_download(self):
        """
        Method to pause a download.
        """
        if self.download_gid:
            logger.log("Stopping download...")
            self._thread(self.api.pause, self.download_gid)

    def stop_downloads(self):
        """
        Method to stop all downloads.
        """
        logger.log("Stopping download...")
        self._thread(
            self.api.pause_all,
        )

    def start_server(self):
        """
        Method to start the Aria2 server.
        """
        self._thread(
            self.api.start_server,
        )

    def stop_server(self):
        """
        Method to stop the Aria2 server.
        """
        self._thread(
            self.api.stop_server,
        )

    def cleanup(self):
        """
        Method to perform cleanup operations.
        """
        logger.log("Performing cleanup...")
        if self.download_gid:
            self.stop_downloads()

        # self.api.save_session()
        self.stop_server()

    def log_error(self, message):
        logger.log(message, level="error")

    def log_warning(self, message):
        logger.log(message, level="warning")

    def log_debug(self, message):
        logger.log(message, level="debug")

    def log_info(self, message):
        logger.log(message, level="info")

    def log_critical(self, message):
        logger.log(message, level="critical")


if __name__ == "__main__":

    def on_close():
        my_app_instance.cleanup()

        # Destroy the ttk.Window instance
        app.destroy()

    app = ttk.Window(
        title="App",
        themename="darkly",
        size=(1270, 550),
        resizable=(False, False),
        position=(10, 140),
    )

    my_app_instance = Aria2Gui(app)
    app.wm_protocol("WM_DELETE_WINDOW", on_close)
    app.mainloop()
