import time
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog


class MainWindow:

    def __init__(self, master, aria2_client):
        self.master = master
        self.master.title("Download Manager")
        self.aria2_client = aria2_client

        # GUI Elements
        # URL Entry
        self.url_label = ttk.Label(master, text="URL:")
        self.url_entry = ttk.Entry(self.master, width=50)
        self.url_entry.insert(0, "https://proof.ovh.net/files/10Mb.dat")

        # Output Entry
        self.output_label = ttk.Label(master, text="Output Path:")
        self.output_entry = ttk.Entry(master, width=50)
        self.output_entry.insert(0, "")

        # Status
        self.status_label = ttk.Label(self.master, text="")

        # Buttons
        self.output_button = ttk.Button(self.master,
                                        text="Browse",
                                        command=self.browse_output_path)
        self.download_button = ttk.Button(self.master,
                                          text="Download",
                                          command=self.start_download)
        self.status_button = ttk.Button(self.master,
                                        text="Status",
                                        command=self.status_thread)

        # Layout
        self.url_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_entry.grid(row=0, column=1, columnspan=1, pady=5)
        self.output_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_entry.grid(row=1, column=1, pady=5)
        self.output_button.grid(row=1, column=2, pady=5)
        self.download_button.grid(row=3, column=0, columnspan=2, pady=10)
        self.status_label.grid(row=2, column=0, padx=10, pady=10, columnspan=3)
        self.status_button.grid(row=3, column=1, columnspan=3, pady=10)

    def browse_output_path(self):
        output_path = filedialog.askdirectory()
        if output_path:
            self.aria2_client.change_global_option({"dir": str(output_path)})
            self.status_label.config(
                text=f"Download directory set to: {output_path}")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)

    def start_download(self):
        url = self.url_entry.get()
        if url:
            threading.Thread(target=self.download_thread,
                             args=(url, ),
                             daemon=True).start()

    def download_thread(self, url):
        gid = self.aria2_client.add_uri([url])
        self.status_label.config(text=f"Download started with GID: {gid}")

    def status_thread(self):
        threading.Thread(target=self.status_update_thread, daemon=True).start()

    def status_update_thread(self):
        while True:
            status = self.aria2_client.tell_active()
            if status:
                self.status_label.config(text=f"Active: {status}",
                                         wraplength=200,
                                         justify=tk.LEFT)
            else:
                self.status_label.config(text="No active downloads")
            time.sleep(1)

    def run(self):
        # Start the Tkinter main loop
        self.master.mainloop()


if __name__ == "__main__":
    from Aria2Client import Aria2Client

    aria2_client = Aria2Client(host="localhost",
                               port=6800,
                               aria2_path="aria2c.exe")
    aria2_client.start_aria()

    root = tk.Tk()
    app = MainWindow(root, aria2_client)

    # Start the Tkinter event loop
    app.run()
    aria2_client.shutdown()
