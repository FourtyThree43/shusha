import logging
import threading
import time
import tkinter as tk
from tkinter import filedialog, ttk

from status_window_2 import StatusWindow

logging.basicConfig(level=logging.INFO)


class MainWindow:

    def __init__(self, master, aria2_client):
        self.master = master
        self.master.geometry("840x420+664+580")  # “wm geometry... wxh+x+y”)
        self.master.minsize(840, 420)
        self.master.maxsize(1000, 1000)
        self.master.resizable(1, 1)
        self.master.configure(background="wheat")
        self.master.configure(highlightbackground="wheat")
        self.master.configure(highlightcolor="black")
        self.master.title("Download Manager")

        self.downloader = aria2_client

        # Mainframe a frame widge that will contain all the widgets
        mainframe = ttk.Frame(self.master, padding="3 3 12 12")
        mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)

        # GUI Elements
        # URL Entry
        self.url = tk.StringVar()
        self.url_label = ttk.Label(mainframe, text="URL:")
        self.url_entry = ttk.Entry(mainframe, width=50, textvariable=self.url)
        self.url_entry.insert(0, "https://proof.ovh.net/files/10Mb.dat")

        # Output Entry
        self.output_path = tk.StringVar()
        self.output_label = ttk.Label(mainframe, text="Output Path:")
        self.output_entry = ttk.Entry(mainframe,
                                      width=50,
                                      textvariable=self.output_path)
        self.output_entry.insert(0, "C:/Users/username/Downloads")

        # Status
        self.status_label = ttk.Label(mainframe, text="")

        # Buttons
        self.output_button = ttk.Button(mainframe,
                                        text="Browse",
                                        command=self.browse_output_path)
        self.download_button = ttk.Button(mainframe,
                                          text="Download",
                                          command=self.start_download)
        self.status_button = ttk.Button(mainframe,
                                        text="Status",
                                        command=self.show_status)

        # Layout
        self.menu()
        # self.task_actions_bar(mainframe=mainframe)
        self.url_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_entry.grid(row=0, column=1, columnspan=1, pady=5)
        self.output_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_entry.grid(row=1, column=1, pady=5)
        self.output_button.grid(row=1, column=2, pady=5)
        self.download_button.grid(row=3, column=0, columnspan=2, pady=10)
        self.status_label.grid(row=2, column=0, padx=10, pady=10, columnspan=3)
        self.status_button.grid(row=3, column=1, columnspan=3, pady=10)

        # Treeview widget to display download list
        columns = ("GID", "Status", "Progress", "Action")
        self.download_tree = ttk.Treeview(mainframe,
                                          columns=columns,
                                          show="headings")

        # Define column headings
        for col in columns:
            self.download_tree.heading(col, text=col)

        # Populate the treeview with initial download data
        self.update_download_list()

        # Add a vertical scrollbar
        scrollbar = ttk.Scrollbar(mainframe,
                                  orient="vertical",
                                  command=self.download_tree.yview)
        self.download_tree.configure(yscrollcommand=scrollbar.set)

        # Layout for the Treeview and scrollbar
        self.download_tree.grid(row=4,
                                column=0,
                                columnspan=3,
                                pady=10,
                                sticky=(tk.W, tk.E))
        scrollbar.grid(row=4, column=3, sticky=(tk.N, tk.S))

        # Padding for all child widgets of mainframe
        for child in mainframe.winfo_children():
            child.grid_configure(padx=5, pady=5)

        self.url_entry.focus()
        self.master.bind("<Return>", self.start_download)

        # Close event handler
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.downloader.shutdown()
        self.master.destroy()

    def menu(self):
        # Create a menu bar
        menu_bar = tk.Menu(self.master)

        # Create a pull-down menu for File
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Start All")
        file_menu.add_command(label="Pause All")
        file_menu.add_command(label="Resume All")
        file_menu.add_command(label="Purge Completed")
        file_menu.add_command(label="Exit", command=self.on_close)
        menu_bar.add_cascade(label="File", menu=file_menu)

        # Create a pull-down menu for Edit
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="Downloads List",
                              command=self.open_downloads_list)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)

        # Create a pull-down menu for Help
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About")
        menu_bar.add_cascade(label="Help", menu=help_menu)

        # Display the menu bar
        self.master.config(menu=menu_bar)

    def task_actions_bar(self, mainframe):
        # Create a frame widget to hold the task action buttons
        task_actions_bar = ttk.Frame(mainframe)
        task_actions_bar.grid(row=3, column=0, columnspan=3, pady=10)

        # Create task action buttons
        start_all_button = ttk.Button(task_actions_bar, text="Start All")
        pause_all_button = ttk.Button(task_actions_bar, text="Pause All")
        resume_all_button = ttk.Button(task_actions_bar, text="Resume All")
        purge_completed_button = ttk.Button(task_actions_bar,
                                            text="Purge Completed")

        # Layout for task action buttons
        start_all_button.grid(row=0, column=0, padx=10, pady=5)
        pause_all_button.grid(row=0, column=1, padx=10, pady=5)
        resume_all_button.grid(row=0, column=2, padx=10, pady=5)
        purge_completed_button.grid(row=0, column=3, padx=10, pady=5)

    def about(self):
        # Open About Window
        pass

    def browse_output_path(self):
        output_path = filedialog.askdirectory()
        if output_path:
            self.downloader.change_global_option({"dir": str(output_path)})
            self.status_label.config(
                text=f"Download directory set to: {output_path}")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)

    def start_download(self):
        url = self.url.get()
        if url:
            threading.Thread(target=self.download_thread,
                             args=(url, ),
                             daemon=True).start()

    def download_thread(self, url):
        try:
            gid = self.downloader.add_uri([url])
            self.status_label.config(text=f"Download started with GID: {gid}")
        except Exception as e:
            logging.error(f"Error starting download: {e}")

    def show_status(self):
        status = self.downloader.tell_active()
        if status:
            status_window = tk.Toplevel(self.master)
            StatusWindow(master=status_window,
                         aria2_client=self.downloader,
                         gid=f"{status[0]['gid']}")

    def status_update(self):
        try:
            status = self.downloader.tell_active()
            if status:
                self.status_label.config(text=f"Active: {status}",
                                         wraplength=200,
                                         justify=tk.LEFT)
            else:
                self.status_label.config(text="No active downloads")
        except Exception as e:
            logging.error(f"Error in status_update: {e}")

        # Schedule the next update after 1 second
        self.master.after(1000, self.status_update)

    def open_downloads_list(self):
        # Open Downloads List Window
        downloads_list_window = tk.Toplevel(self.master)
        DownloadsListWindow(master=downloads_list_window,
                            aria2_client=self.downloader)

    def update_download_list(self):
        # Update the download list in the Treeview widget
        downloads = self.downloader.get_all_downloads()
        for download in downloads:
            gid = download.get("gid", "")
            status = download.get("status", "")
            completedLength = int(download.get("completedLength", 0))
            totalLength = int(download.get("totalLength", 1))
            # progress = completedLength / totalLength * 100
            print(
                f"gid: {gid}, status: {status}, completedLength: {completedLength}, totalLength: {totalLength}"
            )

            # action_button = ttk.Button(
            #     self.download_tree,
            #     text="Action",
            #     command=lambda g=gid: self.perform_action(g))
        #     self.download_tree.insert("",
        #                               tk.END,
        #                               values=(gid, status, f"{progress:.2f}%",
        #                                       action_button))
        self.master.after(1000, self.update_download_list)

    def perform_action(self, gid):
        # Handle the action button click for a specific download
        # You may implement pausing, resuming, or canceling the download based on GID
        pass

    def run(self):
        # Start the Tkinter main loop
        #  Schedule the first status update
        self.master.after(1000, self.status_update)
        self.master.mainloop()


if __name__ == "__main__":
    from aria2_client import Aria2Client

    ariaC = Aria2Client(host="localhost", port=6800, aria2_path="aria2c.exe")
    ariaC.start_aria()

    root = tk.Tk()
    app = MainWindow(master=root, aria2_client=ariaC)

    # Start the Tkinter event loop
    app.run()