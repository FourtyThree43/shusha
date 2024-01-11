import threading
import tkinter as tk
from pathlib import Path
from tkinter import Entry, StringVar, filedialog
from typing import Callable

import ttkbootstrap as ttk
from controller.api import Api
from models.logger import LoggerService
from models.utilities import sizeof_fmt
from ttkbootstrap.tableview import Tableview
from ttkwidgets import DebugWindow

logger = LoggerService(logger_name="ShushaAPP")


class Aria2Gui(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Aria2 GUI")
        self.geometry("1200x500")

        self.debug_window = DebugWindow(self)

        self.api = Api()
        self.download_gid = None
        self.api.start_server()
        self.api.load_db()

        self.create_widgets()
        self.dt = None

        self.protocol("WM_DELETE_WINDOW", self.cleanup)

    def create_stats_frame(self, frame: tk.Frame):
        gstats = self.api.get_stats()
        stats_frame = tk.Frame(frame)
        stats_frame.pack(side=tk.LEFT, padx=10, pady=10)

        for key, value in gstats.items():
            label = tk.Label(stats_frame, text=f"{key}:")
            label.grid(row=0,
                       column=len(stats_frame.winfo_children()),
                       sticky="w",
                       padx=5)

            value_label = tk.Label(stats_frame, text=value)
            value_label.grid(row=1,
                             column=len(stats_frame.winfo_children()) - 1,
                             sticky="e",
                             padx=5)

    def create_widgets(self):

        top_fr = tk.Frame(self)
        top_fr.pack(side=tk.TOP, padx=10, pady=10)

        # Entry for URL
        self.url_var = StringVar()
        url_entry = Entry(top_fr, textvariable=self.url_var)
        url_entry.pack(side=tk.LEFT, pady=10, padx=5)
        url_entry.insert(0, "https://proof.ovh.net/files/10Mb.dat")

        # Button to select download directory
        select_dir_button = tk.Button(top_fr,
                                      text="Select Directory",
                                      command=self.select_directory)
        select_dir_button.pack(side=tk.LEFT, pady=10, padx=5)

        # Entry for download directory
        self.dir_var = StringVar()
        self.dir_ent = Entry(top_fr, textvariable=self.dir_var)
        self.dir_ent.pack(side=tk.LEFT, pady=10, padx=5)
        self.dir_ent.insert(0, "path/to/downloads")

        # Buttons
        start_button = tk.Button(top_fr,
                                 text="Start Download",
                                 command=self.start_download_2)
        start_button.pack(side=tk.LEFT, pady=10, padx=5)

        pause_button = tk.Button(top_fr,
                                 text="Pause Download",
                                 command=self.pause_download)
        pause_button.pack(side=tk.LEFT, pady=10, padx=5)

        pause_all_button = tk.Button(top_fr,
                                     text="Stop",
                                     command=self.stop_downloads)
        pause_all_button.pack(side=tk.LEFT, pady=10, padx=5)

        options_button = tk.Button(top_fr,
                                   text="Options",
                                   command=self.show_options)
        options_button.pack(side=tk.LEFT, pady=10, padx=5)

        all_downloads_button = tk.Button(top_fr,
                                         text="All Downloads",
                                         command=self.get_all_downloads)
        all_downloads_button.pack(side=tk.LEFT, pady=10, padx=5)

        tellsts_button = tk.Button(top_fr,
                                   text="Status",
                                   command=self.show_download_status)
        tellsts_button.pack(side=tk.LEFT, pady=10, padx=5)

        tellactv_btn = tk.Button(top_fr,
                                 text="Active",
                                 command=self.show_active_downloads)
        tellactv_btn.pack(side=tk.LEFT, pady=10, padx=5)

        tellwait_btn = tk.Button(top_fr,
                                 text="Waiting",
                                 command=self.show_wait_downloads)
        tellwait_btn.pack(side=tk.LEFT, pady=10, padx=5)

        tellstp_button = tk.Button(top_fr,
                                   text="Stoped",
                                   command=self.show_stop_downloads)
        tellstp_button.pack(side=tk.LEFT, pady=10, padx=5)

        btm_fr = tk.Frame(self)
        btm_fr.pack(side=tk.BOTTOM, padx=10, pady=10)

        status_row = tk.Frame(btm_fr)
        status_row.pack(side=tk.TOP, padx=10, pady=10)
        # Status
        self.status_label = tk.Label(status_row, text="Status:")
        self.status_label.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        stats_row = tk.Frame(btm_fr)
        stats_row.pack(side=tk.LEFT, padx=10, pady=10)
        # Stats
        # self.stats_label = tk.Label(stats_row, text="Stats:")
        # self.stats_label.pack(side=tk.LEFT, fill=tk.X, padx=10, pady=10)

        # self.create_stats_frame(stats_row)
        self.stats_frame = tk.Frame(stats_row)
        self.stats_frame.pack(side=tk.LEFT, padx=10, pady=10)

        tf = tk.Frame(self)
        tf.pack(side=tk.LEFT, padx=10, pady=10)

        self.create_table_view(tf)

    def create_table_view(self, frame: tk.Frame):
        self.desired_columns = [
            "gid", "status", "totalLength", "completedLength", "downloadSpeed",
            "uploadSpeed", "connections", "numSeeders", "numPieces"
        ]
        _db = self.api.db.table('downloads')
        data = _db.all()

        # Column mapping for display names
        column_mapping = {
            "gid": "Gid",
            "status": "Status",
            "totalLength": "Total Size",
            "completedLength": "Completed",
            "downloadSpeed": "Download Speed",
            "uploadSpeed": "Upload Speed",
            "connections": "Connections",
            "numSeeders": "Seeders",
            "numPieces": "Pieces"
        }

        # Extract columns using the mapping
        coldata = [
            column_mapping.get(col, col) for col in self.desired_columns
        ]

        # Define sizes and speeds for formatting
        self.sizes = ["totalLength", "completedLength"]
        self.speeds = ["downloadSpeed", 'uploadSpeed']

        # Extract rows with formatted values
        rowdata = [[
            self.format_size(float(row.get(col, ''))) if col in self.sizes else
            self.format_speed(float(row.get(col, '')))
            if col in self.speeds else row.get(col, '')
            for col in self.desired_columns
        ] for row in data]

        # Create Tableview
        self.dt = Tableview(
            master=frame,
            coldata=coldata,
            rowdata=rowdata,
            paginated=True,
            searchable=True,
            bootstyle=ttk.PRIMARY,
        )
        self.dt.pack(fill=ttk.BOTH, expand=ttk.YES, padx=10, pady=10)

    def select_directory(self):
        output_path = filedialog.askdirectory()
        if output_path:
            self.api.change_global_options({"dir": str(output_path)})
            self.status_label.config(
                text=f"Download directory set to: {output_path}")
            self.dir_var.set(output_path)

    def modify_stats_keys(self, gstats):
        # Mapping of keys to display names
        key_mapping = {
            'downloadSpeed': 'Download Speed',
            'numActive': 'Active',
            'numStopped': 'Stopped',
            'numStoppedTotal': 'Total Stopped',
            'numWaiting': 'Waiting',
            'uploadSpeed': 'Upload Speed'
        }

        # Modify keys as needed
        modified_gstats = {
            f"{key_mapping.get(key, key)}": value
            for key, value in gstats.items()
        }
        return modified_gstats

    def format_speed(self, speed):
        return sizeof_fmt(speed, suffix="B/s")

    def format_size(self, size):
        return sizeof_fmt(size, suffix="B")

    def update_stats_frame(self, gstats):
        modified_gstats = self.modify_stats_keys(gstats)

        # Clear existing labels in the stats frame
        for child in self.stats_frame.winfo_children():
            child.destroy()

        for key, value in modified_gstats.items():
            label = tk.Label(self.stats_frame, text=f"{key}:")
            label.pack(side=tk.LEFT, padx=5)

            # Format values for 'Download Speed' and 'Upload Speed'
            if key in ['Download Speed', 'Upload Speed']:
                value = self.format_speed(float(value))

            value_label = tk.Label(self.stats_frame, text=value)
            value_label.pack(side=tk.LEFT, padx=5)

    def download_thread(self, url):
        try:
            gid = self.api.start_download(url)
            self.download_gid = gid
            msg = f"Download started with GID: {gid}"
            self.status_label.config(
                text=msg,
                wraplength=800,
                justify=tk.LEFT,
            )
        except Exception as e:
            self.log_error(f"Error starting download: {e}")

    def start_download(self):
        logger.log("Starting download...")
        url = "https://proof.ovh.net/files/10Mb.dat"
        threading.Thread(target=self.download_thread, args=(url, )).start()

    def show_download_status(self):
        if self.download_gid:
            status = self.api.get_download_status(self.download_gid)
            self.status_label.config(text=f"Status: {status}",
                                     wraplength=200,
                                     justify=tk.LEFT)
        else:
            self.status_label.config(text=f"Status: None",
                                     wraplength=200,
                                     justify=tk.LEFT)

    def monitor_download(self):
        if self.download_gid:
            status = self.api.get_download_status(self.download_gid)
            self.status_label.config(text=f"Status: {status}",
                                     wraplength=200,
                                     justify=tk.LEFT)
            self.after(1000, self.monitor_download)

    def pause_download(self):
        if self.download_gid:
            logger.log("Stopping download...")
            threading.Thread(target=self.api_operations,
                             args=(self.api.pause, self.download_gid)).start()

    def stop_downloads(self):
        logger.log("Stopping download...")
        threading.Thread(target=self.api_operations,
                         args=(self.api.pause_all, )).start()

    def stats_thread(self):
        gstats = self.api.get_stats()
        if gstats is not None:
            self.update_stats_frame(gstats)
            self.after(1000, self.stats_thread)

    def stats(self):
        self._thread(self.stats_thread)

    def stats0(self):
        try:
            gstats = self.api.get_stats()

            if gstats:
                self.update_stats_frame(gstats)

                # Schedule the next update after 1 second
                self.after(1000, self.stats)
        except Exception as e:
            self.log_error(f"Error in get_stats: {e}")

    def update_label(self, operation, result):
        self.status_label.config(text=f"{operation}: {result}",
                                 wraplength=200,
                                 justify=tk.LEFT)

    def _method_thread(self, method: Callable, *args):
        result = method(*args)
        return result

    def show_options(self):
        logger.log("Showing options...")
        self.update_label(operation="Options", result=self.api._options)

    def get_all_downloads_thread(self):
        self._all_downloads = self.api.get_all_downloads()
        self.update_label(operation="All Downloads",
                          result=f"{self._all_downloads} downloads")

    def get_all_downloads(self):
        self._thread(self.get_all_downloads_thread)

    def show_active_downloads(self):
        logger.log("Showing active downloads...")
        active_downloads = self.api.get_active()
        logger.log(active_downloads)
        self.status_label.config(text=f"Active downloads: {active_downloads}",
                                 wraplength=200,
                                 justify=tk.LEFT)

    def show_wait_downloads(self):
        logger.log("Showing waiting downloads...")
        wait_downloads = self.api.get_waiting(0, 100)
        self.status_label.config(text=f"Waiting downloads: {wait_downloads}",
                                 wraplength=200,
                                 justify=tk.LEFT)

    def show_stop_downloads(self):
        logger.log("Showing stopped downloads...")
        stop_downloads = self.api.get_stopped(0, 100)
        self.status_label.config(text=f"Stopped downloads: {stop_downloads}",
                                 wraplength=200,
                                 justify=tk.LEFT)

    def cleanup(self):
        logger.log("Performing cleanup...")
        if self.download_gid:
            self.stop_downloads()
            self.api.updatedb()
            self.api.persistence()

        self.api.save_session()
        self.api.stop_server()

        # Destroy the Tkinter window
        self.debug_window.quit()
        self.destroy()

    def api_operations(self, api_method, *args):
        try:
            api_method(*args)
        except Exception as e:
            self.log_error(f"Error in API operation: {e}")

    def log_error(self, message):
        logger.log(message, level="error")

    def run(self):
        try:
            self.after(1000, self.stats)
            self.mainloop()
        except KeyboardInterrupt:
            self.cleanup()

    def _thread(self, target, *args):
        """Helper method to run the target function in a separate thread."""
        threading.Thread(target=target, args=args).start()

    def download_and_thread(self, url):

        def download_logic():
            try:
                gid = self.api.start_download(url)
                return gid, f"Download started with GID: {gid}"
            except Exception as e:
                self.log_error(f"Error starting download: {e}")
                return None, f"Error starting download: {e}"

        def update_status(result):
            gid, msg = result
            if gid is not None:
                self.download_gid = gid
            self.status_label.config(
                text=msg,
                wraplength=800,
                justify=tk.LEFT,
            )

        self._thread(lambda: update_status(download_logic()))

    def start_download_2(self):
        url = self.url_var.get()
        self.download_and_thread(url)
        self.update_table_rows()  # Call the method to update table rows

    def update_table_rows(self):
        # Check if the Tableview instance exists
        if self.dt:
            print("Updating table rows...")
            data = self.api._downloads
            print(data)
        else:
            print("Tableview not found. Skipping update...")


if __name__ == "__main__":
    app = Aria2Gui()

    try:
        app.run()
    except KeyboardInterrupt:
        # Handle KeyboardInterrupt (Ctrl+C) to ensure proper cleanup
        logger.log("Received KeyboardInterrupt. Cleaning up...",
                   level="warning")
        app.cleanup()
