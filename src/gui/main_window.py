import tkinter as tk
from tkinter import ttk
from gui.status_window import StatusWindow
from src import Aria2Client

class MainWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Shusha")

        # Instantiate Aria2Client
        self.downloader = Aria2Client()

        # GUI Elements
        self.url_label = ttk.Label(master, text="URL:")
        self.url_entry = ttk.Entry(master, width=50)
        self.url_entry.insert(0, self.downloader.download_config.get("url", ""))

        self.output_label = ttk.Label(master, text="Output Path:")
        self.output_entry = ttk.Entry(master, width=50)
        self.output_entry.insert(0, self.downloader.download_config.get("output_path", ""))
        self.output_button = ttk.Button(master, text="Browse", command=self.browse_output_path)

        self.download_button = ttk.Button(master, text="Download", command=self.download)
        self.status_button = ttk.Button(master, text="Show Status", command=self.show_status)

        # Layout
        self.url_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_entry.grid(row=0, column=1, columnspan=2, pady=5)
        self.output_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_entry.grid(row=1, column=1, pady=5)
        self.output_button.grid(row=1, column=2, pady=5)
        self.download_button.grid(row=2, column=0, columnspan=3, pady=10)
        self.status_button.grid(row=3, column=0, columnspan=3, pady=10)

    def browse_output_path(self):
        output_path = tk.filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("All Files", "*.*")])
        if output_path:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)

    def download(self):
        url = self.url_entry.get()
        output_path = self.output_entry.get()

        if url and output_path:
            self.downloader.download_file(url, output_path)
            # Add status messages or update GUI as needed

    def show_status(self):
        status_window = StatusWindow(self.master, self.downloader, 'your_gid')  # Replace 'your_gid' with the actual GID


if __name__ == "__main__":
    root = tk.Tk()
    main_window = MainWindow(root)
    root.mainloop()
