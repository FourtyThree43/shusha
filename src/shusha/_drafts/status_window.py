import tkinter as tk
from tkinter import ttk

class StatusWindow:
    def __init__(self, master, downloader, gid):
        self.master = master
        self.downloader = downloader
        self.gid = gid

        self.status_var = tk.StringVar()
        self.create_widgets()

    def create_widgets(self):
        self.status_label = ttk.Label(self.master, text="Download Status:")
        self.status_display = ttk.Label(self.master, textvariable=self.status_var)
        self.refresh_button = ttk.Button(self.master, text="Refresh", command=self.refresh_status)

        self.status_label.grid(row=0, column=0, pady=10)
        self.status_display.grid(row=1, column=0, pady=10)
        self.refresh_button.grid(row=2, column=0, pady=10)

        # Initial status display
        self.refresh_status()

    def refresh_status(self):
        status = self.downloader.get_download_status(self.gid)
        if status:
            self.status_var.set(str(status))
        else:
            self.status_var.set("Failed to fetch status")
