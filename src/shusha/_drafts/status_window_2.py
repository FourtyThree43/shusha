import tkinter as tk
from tkinter import ttk
import threading
import time
import logging

logging.basicConfig(level=logging.INFO)


class StatusWindow:

    def __init__(self, master, aria2_client, gid):
        self.master = master
        self.aria2_client = aria2_client
        self.gid = gid

        # Create widgets
        self.create_widgets()

        # Start the status update thread
        self.status_thread()

        # Close event handler
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        if self.master:
            self.master.destroy()

    def create_widgets(self):
        # Create a label to display status
        self.status_label = ttk.Label(self.master, text="")
        self.status_label.pack(padx=10, pady=10)

        # Create a button to close the window
        close_button = ttk.Button(self.master,
                                  text="Close",
                                  command=self.master.destroy)
        close_button.pack(pady=10)

    def status_thread(self):
        threading.Thread(target=self.status_update_thread, daemon=True).start()

    def status_update_thread(self):
        while True:
            try:
                if not self.master:
                    break

                status = self.aria2_client.tell_status(self.gid)
                if status:
                    self.status_label.config(text=f"Status: {status}",
                                             wraplength=200,
                                             justify=tk.LEFT)
                else:
                    self.status_label.config(text="Download not found")
                    break  # Break the loop if the download is not found
                time.sleep(1)
            except Exception as e:
                logging.error(f"Error in status_update_thread: {e}")
                time.sleep(1)
