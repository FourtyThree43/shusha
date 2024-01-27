class DownloadsListWindow:
    def __init__(self, master, aria2_client):
        self.master = master
        self.master.title("Downloads List")
        self.downloader = aria2_client

        # Create a listbox or table to display downloads
        # Include columns for GID, status, progress, and action buttons

        # Populate the list/table with download details using self.downloader.get_all_downloads()

        # Add buttons for actions like pause, resume, and cancel

    # Implement methods to handle actions like pausing, resuming, and canceling downloads

    def run(self):
        # Start the Tkinter main loop for the Downloads List Window
        self.master.mainloop()
