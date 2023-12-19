import tkinter as tk
from tkinter import ttk
from Aria2Client import Aria2Client

class DownloadManagerGUI:
    def __init__(self, aria2_client):
        self.aria2_client = aria2_client

        # Create the main window
        self.root = tk.Tk()
        self.root.title("Download Manager")

        # Add GUI components and configure layout
        # GUI Elements
        self.url_label = ttk.Label(master, text="URL:")
        self.url_entry = ttk.Entry(master, width=50)
        self.url_entry.insert(0, self.aria2_client.download_config.get("url", ""))

        self.output_label = ttk.Label(master, text="Output Path:")
        self.output_entry = ttk.Entry(master, width=50)
        self.output_entry.insert(0, self.aria2_client.download_config.get("output_path", ""))
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


        # Example: Add a button to start downloads
        start_button = ttk.Button(self.root, text="Start Downloads", command=self.start_downloads)
        start_button.pack(pady=10)

    def start_downloads(self):
        # Implement the functionality to start downloads
        # You can interact with the Aria2Client class here
        pass

    def browse_output_path(self):
        output_path = tk.filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("All Files", "*.*")])
        if output_path:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)

    def download(self):
        url = self.url_entry.get()
        output_path = self.output_entry.get()

        if url and output_path:
            self.aria2_client.download_file(url, output_path)
            # Add status messages or update GUI as needed

    def run(self):
        # Start the GUI main loop
        self.root.mainloop()

if __name__ == "__main__":
    # Assuming you already have an instance of Aria2Client
    aria2_client = Aria2Client(host='localhost', port=6800, aria2_path='aria2c.exe')
    download_manager_gui = DownloadManagerGUI(aria2_client)
    download_manager_gui.run()
