from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path("gui/assets/")


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)


class App:

    def __init__(self, root):
        self.master = root
        self.master.geometry("540x540+664+580")  # “wm geometry... wxh+x+y”)
        self.master.minsize(1050, 320)
        self.master.maxsize(1050, 350)
        self.master.resizable(1, 1)
        self.master.configure(background="wheat")
        self.master.configure(highlightbackground="wheat")
        self.master.configure(highlightcolor="black")
        self.master.title("Download Manager")

        # Mainframe a frame widge that will contain all the widgets
        self.mainframe = ttk.Frame(self.master, padding="3 3 12 12")
        self.mainframe.grid(column=0, row=0, sticky=tk.NSEW)
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)

        self.create_menu_bar()
        self.create_task_actions_bar()
        self.create_left_panel()
        self.create_center_panel()
        self.create_right_panel()
        self.create_bottom_status_bar()

    def create_menu_bar(self):
        menu_bar = ttk.Frame(self.mainframe)
        menu_bar.grid(column=0, row=0, sticky=tk.EW)

        # Create the menu
        menu = tk.Menu(menu_bar)
        file_menu = tk.Menu(menu, tearoff=0)
        edit_menu = tk.Menu(menu, tearoff=0)
        view_menu = tk.Menu(menu, tearoff=0)
        queue_menu = tk.Menu(menu, tearoff=0)
        options_menu = tk.Menu(menu, tearoff=0)
        help_menu = tk.Menu(menu, tearoff=0)

        # Add items to the menus
        menu.add_cascade(label="File", menu=file_menu)
        menu.add_cascade(label="Edit", menu=edit_menu)
        menu.add_cascade(label="View", menu=view_menu)
        menu.add_cascade(label="Queue", menu=queue_menu)
        menu.add_cascade(label="Options", menu=options_menu)
        menu.add_cascade(label="Help", menu=help_menu)

        # Add sub-items to File menu
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save")
        file_menu.add_command(label="Exit", command=self.master.quit)

        # Add sub-items to Edit menu
        edit_menu.add_command(label="Add URL", command=self.add_url)
        edit_menu.add_command(label="Add Torrent", command=self.add_torrent)
        edit_menu.add_command(label="Refresh", command=self.refresh_task_list)
        edit_menu.add_separator()
        edit_menu.add_command(label="Start All", command=self.start_all)
        edit_menu.add_command(label="Resume All", command=self.resume_all)
        edit_menu.add_command(label="Pause All", command=self.pause_all)
        edit_menu.add_command(label="Purge Completed",
                              command=self.purge_completed)

        # Add sub-items to View menu
        view_menu.add_checkbutton(label="Category")
        view_menu.add_checkbutton(label="Name")
        view_menu.add_checkbutton(label="Size")
        view_menu.add_checkbutton(label="Progress")
        view_menu.add_checkbutton(label="Download Speed")
        view_menu.add_checkbutton(label="Upload Speed")
        view_menu.add_checkbutton(label="ETA")
        view_menu.add_checkbutton(label="Status")
        view_menu.add_checkbutton(label="Note")

        # Add sub-items to Queue menu
        queue_menu.add_command(label="Move To Top")
        queue_menu.add_command(label="Move To Bottom")
        queue_menu.add_command(label="Move Up")
        queue_menu.add_command(label="Move Down")
        queue_menu.add_command(label="Remove")

        # Add sub-items to Options menu
        options_menu.add_command(label="Settings")
        options_menu.add_command(label="Scheduler")
        options_menu.add_command(label="Speed Limit")
        options_menu.add_command(label="Connection")
        options_menu.add_command(label="Proxy")
        options_menu.add_command(label="Plugin")

        # Add sub-items to Help menu
        help_menu.add_command(label="About")
        help_menu.add_command(label="Online Help")
        help_menu.add_command(label="Forum")
        help_menu.add_command(label="Discord")
        help_menu.add_command(label="Report Bug")
        help_menu.add_command(label="Donate")

        # Display the menu
        self.master.config(menu=menu)

    def create_task_actions_bar(self):
        # task_actions_bar = ttk.Frame(self.mainframe)
        task_actions_bar = tk.PanedWindow(self.mainframe, orient=tk.HORIZONTAL)
        task_actions_bar.grid(column=0, row=1, sticky=tk.EW, columnspan=3)

        # Load images
        add_url_icon = tk.PhotoImage(
            file=relative_to_assets("add-url-icon.png"))
        add_torrent_icon = tk.PhotoImage(
            file=relative_to_assets("magnetic-icon.png"))
        refresh_icon = tk.PhotoImage(
            file=relative_to_assets("task-sync-icon.png"))
        start_all_icon = tk.PhotoImage(file=relative_to_assets("button_2.png"))
        resume_all_icon = tk.PhotoImage(
            file=relative_to_assets("play-pause-icon.png"))
        pause_all_icon = tk.PhotoImage(
            file=relative_to_assets("pause-icon.png"))
        purge_completed_icon = tk.PhotoImage(
            file=relative_to_assets("remove-files-icon.png"))

        # Create buttons with images
        add_url_button = ttk.Button(task_actions_bar,
                                    image=add_url_icon,
                                    command=self.add_url)
        add_torrent_button = ttk.Button(task_actions_bar,
                                        image=add_torrent_icon,
                                        command=self.add_torrent)
        refresh_button = ttk.Button(task_actions_bar,
                                    image=refresh_icon,
                                    command=self.refresh_task_list)
        start_all_button = ttk.Button(task_actions_bar,
                                      image=start_all_icon,
                                      command=self.start_all)
        resume_all_button = ttk.Button(task_actions_bar,
                                       image=resume_all_icon,
                                       command=self.resume_all)
        pause_all_button = ttk.Button(task_actions_bar,
                                      image=pause_all_icon,
                                      command=self.pause_all)
        purge_completed_button = ttk.Button(task_actions_bar,
                                            image=purge_completed_icon,
                                            command=self.purge_completed)

        # Attach icons to buttons
        add_url_button.image = add_url_icon
        add_torrent_button.image = add_torrent_icon
        refresh_button.image = refresh_icon
        start_all_button.image = start_all_icon
        resume_all_button.image = resume_all_icon
        pause_all_button.image = pause_all_icon
        purge_completed_button.image = purge_completed_icon

        # Arrange buttons
        add_url_button.grid(column=0, row=0, padx=5)
        add_torrent_button.grid(column=1, row=0, padx=5)
        refresh_button.grid(column=2, row=0, padx=5)
        start_all_button.grid(column=3, row=0, padx=5)
        resume_all_button.grid(column=4, row=0, padx=5)
        pause_all_button.grid(column=5, row=0, padx=5)
        purge_completed_button.grid(column=6, row=0, padx=5)

    def create_left_panel(self):
        left_pane = ttk.Panedwindow(self.mainframe, orient=tk.VERTICAL)
        left_pane.grid(column=0,
                       row=2,
                       sticky=tk.EW,
                       padx=0,
                       pady=0,
                       columnspan=1)

        # Treeview for Categories
        categories_tree = ttk.Treeview(left_pane,
                                       columns=("Categories"),
                                       show="headings")
        categories_tree.heading("Categories", text="Categories")
        categories_tree.insert("", "end", text="All", values=["All"])
        categories_tree.insert("", "end", text="Active", values=["Active"])
        categories_tree.insert("", "end", text="Inactive", values=["Inactive"])
        categories_tree.insert("",
                               "end",
                               text="Completed",
                               values=["Completed"])
        categories_tree.insert("",
                               "end",
                               text="Downloading",
                               values=["Downloading"])
        categories_tree.insert("", "end", text="Paused", values=["Paused"])
        categories_tree.insert("", "end", text="Queued", values=["Queued"])
        categories_tree.insert("", "end", text="Seeding", values=["Seeding"])

        # Add left_pane widget with a specific size
        left_pane.add(categories_tree)

    def create_center_panel(self):
        center_pane = ttk.Panedwindow(self.mainframe, orient=tk.VERTICAL)
        center_pane.grid(column=1,
                         row=2,
                         sticky=tk.NSEW,
                         padx=5,
                         pady=5,
                         columnspan=2)

        # Treeview for Download List
        _columns = ("GID", "Status", "Progress", "Action")
        download_list_tree = ttk.Treeview(center_pane,
                                          columns=_columns,
                                          show="headings")
        download_list_tree.heading("GID", text="GID")
        download_list_tree.heading("Status", text="Status")
        download_list_tree.heading("Progress", text="Progress")
        download_list_tree.heading("Action", text="Action")
        center_pane.add(download_list_tree)

        # Add a vertical scrollbar
        scrollbar = ttk.Scrollbar(self.mainframe,
                                  orient="vertical",
                                  command=download_list_tree.yview)
        download_list_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(column=5, row=2, sticky=tk.NS)

        # Add a horizontal scrollbar
        scrollbar = ttk.Scrollbar(self.mainframe,
                                  orient="horizontal",
                                  command=download_list_tree.xview)
        download_list_tree.configure(xscrollcommand=scrollbar.set)
        scrollbar.grid(column=1, row=3, sticky=tk.EW, columnspan=4)

        # add sample values to the center_panel
        for i in range(21):
            download_list_tree.insert("",
                                      "end",
                                      text="Sample",
                                      values=[
                                          f"Lorem_a{i}", f"Lorem_b{i}",
                                          f"Lorem_c{i}", f"Lorem_d{i}"
                                      ])

    def create_right_panel(self):
        # ... (implement your right panel here)
        pass

    def create_bottom_status_bar(self):
        satus_bar = ttk.Panedwindow(self.mainframe)
        satus_bar.grid(column=0, row=3, sticky=tk.EW, columnspan=5)

        # Create a label
        status_label = ttk.Label(satus_bar, text="Status: ")
        status_label.grid(column=0, row=1, sticky=tk.EW)

        # Create a progress bar
        progress_bar = ttk.Progressbar(satus_bar, orient=tk.HORIZONTAL)
        progress_bar.grid(column=0, row=0, sticky=tk.EW)

        # Create a label
        download_speed_label = ttk.Label(satus_bar, text="Download Speed: ")
        download_speed_label.grid(column=2, row=1, sticky=tk.EW, padx=10)

        # sample dl_speed
        dl_speed = ttk.Label(satus_bar, text="0.00 KiB/s" + " ↓")
        dl_speed.grid(column=2, row=0, sticky=tk.S, padx=5)

        # Create a label
        upload_speed_label = ttk.Label(satus_bar, text="Upload Speed: ")
        upload_speed_label.grid(column=3, row=1, sticky=tk.EW, padx=10)

        # sample ul_speed
        ul_speed = ttk.Label(satus_bar, text="0.00 KiB/s" + " ↑")
        ul_speed.grid(column=3, row=0, sticky=tk.S, padx=5)

        # Create a label
        time_elapsed_label = ttk.Label(satus_bar, text="Time Elapsed: ")
        time_elapsed_label.grid(column=4, row=1, sticky=tk.EW, padx=10)

        # sample time_elapsed
        time_elapsed = ttk.Label(satus_bar, text="00:00:00")
        time_elapsed.grid(column=4, row=0, sticky=tk.S, padx=5)

        # Create a label
        time_remaining_label = ttk.Label(satus_bar, text="Time Remaining: ")
        time_remaining_label.grid(column=5, row=1, sticky=tk.EW, padx=10)

        # sample time_remaining
        time_remaining = ttk.Label(satus_bar, text="00:00:00")
        time_remaining.grid(column=5, row=0, sticky=tk.S, padx=5)

        # Create a label
        active_downloads_label = ttk.Label(satus_bar, text="Active: ")
        active_downloads_label.grid(column=6, row=1, sticky=tk.EW, padx=10)

        # sample num_of_active_downloads
        active_downloads = ttk.Label(satus_bar, text="0/21")
        active_downloads.grid(column=6, row=0, sticky=tk.S, padx=5)

        # Create a label
        waiting_downloads_label = ttk.Label(satus_bar, text="Waiting: ")
        waiting_downloads_label.grid(column=7, row=1, sticky=tk.EW, padx=10)

        # sample num_of_waiting_downloads
        waiting_downloads = ttk.Label(satus_bar, text="0/21")
        waiting_downloads.grid(column=7, row=0, sticky=tk.S, padx=5)

        # Create a label
        stopped_downloads_label = ttk.Label(satus_bar, text="Stopped: ")
        stopped_downloads_label.grid(column=8, row=1, sticky=tk.EW, padx=10)

        # sample num_of_stopped_downloads
        stopped_downloads = ttk.Label(satus_bar, text="21/21")
        stopped_downloads.grid(column=8, row=0, sticky=tk.S, padx=5)

        # Create a label
        speed_limit_label = ttk.Label(satus_bar, text="Speed Limiter ")
        speed_limit_label.grid(column=9, row=1, sticky=tk.EW, padx=10)

        # load speed_limit_icons (Low, Medium, High)
        self.low_speed_limit_icon = tk.PhotoImage(
            file=relative_to_assets("sp_low-icon.png"))
        self.medium_speed_limit_icon = tk.PhotoImage(
            file=relative_to_assets("sp_mid-icon.png"))
        self.high_speed_limit_icon = tk.PhotoImage(
            file=relative_to_assets("sp_high-icon.png"))

        # Initialize speed limit state
        self.speed_limit_state = 1

        # sample speed_limit button with icon changes to Low/Medium/High on press
        self.speed_limit_button = ttk.Button(
            satus_bar,
            image=self.medium_speed_limit_icon,
            command=self.change_speed_limit)

        self.speed_limit_button.image = self.medium_speed_limit_icon
        self.speed_limit_button.grid(column=9, row=0, sticky=tk.NS, padx=5)

    def open_file(self):
        # Implement the open file functionality
        pass

    def add_url(self):
        # Implement the add URL functionality
        pass

    def add_torrent(self):
        # Implement the add torrent functionality
        pass

    def refresh_task_list(self):
        # Implement the refresh task list functionality
        pass

    def start_all(self):
        # Implement the start all functionality
        pass

    def resume_all(self):
        # Implement the resume all functionality
        pass

    def pause_all(self):
        # Implement the pause all functionality
        pass

    def purge_completed(self):
        # Implement the purge completed functionality

        pass

    def change_speed_limit(self):
        # changes the speed limit icon to Low/Medium/High
        # depending on the number of clicks
        self.speed_limit_state = (self.speed_limit_state + 1) % 3
        if self.speed_limit_state == 0:
            self.speed_limit_button.config(image=self.low_speed_limit_icon)
            self.speed_limit_button.image = self.low_speed_limit_icon
        elif self.speed_limit_state == 1:
            self.speed_limit_button.config(image=self.medium_speed_limit_icon)
            self.speed_limit_button.image = self.medium_speed_limit_icon
        elif self.speed_limit_state == 2:
            self.speed_limit_button.config(image=self.high_speed_limit_icon)
            self.speed_limit_button.image = self.high_speed_limit_icon


# Create and run the app
root = tk.Tk()
app = App(root)
root.mainloop()
