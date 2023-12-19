import threading
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog


class MainWindow:

    def __init__(self, master, aria2_client):
        self.master = master
        self.master.title("Download Manager")
        self.aria2_client = aria2_client

        # URL Entry
        self.url_label = ttk.Label(master, text="URL:")
        self.url_entry = ttk.Entry(self.master, width=50)
        self.url_entry.grid(row=0, column=0, padx=10, pady=10, columnspan=2)

        # Browse Button
        self.browse_button = ttk.Button(self.master,
                                        text="Browse",
                                        command=self.browse_output_path)
        self.browse_button.grid(row=0, column=2, padx=10, pady=10)

        # Download Button
        self.download_button = ttk.Button(self.master,
                                          text="Download",
                                          command=self.start_download)
        self.download_button.grid(row=1,
                                  column=0,
                                  padx=10,
                                  pady=10,
                                  columnspan=3)

        # Status Label
        self.status_label = ttk.Label(self.master, text="")
        self.status_label.grid(row=2, column=0, padx=10, pady=10, columnspan=3)

    def browse_output_path(self):
        output_path = filedialog.askdirectory()
        if output_path:
            self.aria2_client.change_global_option({"dir": str(output_path)})
            self.status_label.config(
                text=f"Download directory set to: {output_path}")

    def start_download(self):
        url = self.url_entry.get()
        if url:
            threading.Thread(target=self.download_thread,
                             args=(url, ),
                             daemon=True).start()

    def download_thread(self, url):
        gid = self.aria2_client.add_uri([url])
        self.status_label.config(text=f"Download started with GID: {gid}")

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
