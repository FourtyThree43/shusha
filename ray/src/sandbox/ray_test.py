from tkinter import *
from tkinter.ttk import *
from pathlib import Path

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path("../src/gui/assets")


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)


class App:
    def __init__(self, root: Tk):
        self.root = root
        self.root.geometry("540x540+10+10")  # “wm geometry... wxh+x+y”)
        self.root.minsize(1050, 320)
        # self.root.resizable(False, False)
        # self.root.maxsize(1050, 390)
        # for i in range(3):
        #     self.root.rowconfigure(i, weight=1)
        # for j in range(10):
        #     self.root.columnconfigure(j, weight=1)
        self.root.iconbitmap("../src/gui/assets/internet_download_symbol.ico")
        self.root.configure(
            background="wheat", highlightbackground="wheat", highlightcolor="black"
        )
        self.root.title("Download Manager")

        # Mainframe a frame widge that will contain all the widgets
        self.mainframe = Frame(master=self.root, borderwidth=1)
        # self.mainframe.grid(column=0, row=0, sticky=NSEW)
        self.mainframe.pack(fill=BOTH, expand=True, side=BOTTOM)

        self.create_menu_bar(self.mainframe)
        self.create_task_actions_bar(self.mainframe)
        self.create_left_panel(self.mainframe)
        self.create_center_panel(self.mainframe)
        self.create_right_panel()
        self.create_bottom_status_bar(self.mainframe)

    def create_menu_bar(self, frame):
        menu_bar = Frame(frame)
        menu_bar.grid(column=0, row=0, sticky=EW)

        # Create the menu
        menu = Menu(menu_bar)
        file_menu = Menu(menu, tearoff=0)
        edit_menu = Menu(menu, tearoff=0)
        view_menu = Menu(menu, tearoff=0)
        queue_menu = Menu(menu, tearoff=0)
        options_menu = Menu(menu, tearoff=0)
        help_menu = Menu(menu, tearoff=0)

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
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Add sub-items to Edit menu
        edit_menu.add_command(label="Add URL", command=self.add_url)
        edit_menu.add_command(label="Add Torrent", command=self.add_torrent)
        edit_menu.add_command(label="Refresh Task List", command=self.refresh_task_list)
        edit_menu.add_separator()
        edit_menu.add_command(label="Resume All Task", command=self.resume_all)
        edit_menu.add_command(label="Pause All Task", command=self.pause_all)
        edit_menu.add_command(
            label="Purge Task Record", command=self.purge_task_records
        )

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
        self.root.config(menu=menu)

    def create_task_actions_bar(self, frame):
        # task_actions_bar = Frame(self.mainframe)
        task_actions_bar = PanedWindow(frame, orient=HORIZONTAL)
        task_actions_bar.grid(column=0, row=1, sticky=EW, columnspan=3)

        # Load images
        add_url_icon = PhotoImage(
            file=relative_to_assets("add-url-icon.png")
        ).subsample(15, 15)
        add_torrent_icon = PhotoImage(
            file=relative_to_assets("magnetic-icon.png")
        ).subsample(15, 15)
        refresh_icon = PhotoImage(
            file=relative_to_assets("task-sync-icon.png")
        ).subsample(15, 15)
        resume_all_icon = PhotoImage(file=relative_to_assets("bt-DL4.png")).subsample(
            15, 15
        )
        pause_all_icon = PhotoImage(file=relative_to_assets("bt-DL5.png")).subsample(
            15, 15
        )
        purge_records_icon = PhotoImage(
            file=relative_to_assets("remove-files-icon.png")
        ).subsample(15, 15)
        self.start_all_icon = PhotoImage(
            file=relative_to_assets("bt-tON.png")
        ).subsample(15, 15)
        self.stop_all_icon = PhotoImage(
            file=relative_to_assets("bt-tOFF.png")
        ).subsample(15, 15)

        # Create buttons with images
        add_url_button = Button(
            task_actions_bar, image=add_url_icon, command=self.add_url
        )
        add_torrent_button = Button(
            task_actions_bar, image=add_torrent_icon, command=self.add_torrent
        )
        refresh_button = Button(
            task_actions_bar, image=refresh_icon, command=self.refresh_task_list
        )
        resume_all_button = Button(
            task_actions_bar, image=resume_all_icon, command=self.resume_all
        )
        pause_all_button = Button(
            task_actions_bar, image=pause_all_icon, command=self.pause_all
        )
        purge_records_button = Button(
            task_actions_bar, image=purge_records_icon, command=self.purge_task_records
        )

        self.start_all_button = Button(
            task_actions_bar, image=self.start_all_icon, command=self.start_all
        )

        # Attach icons to buttons
        add_url_button.image = add_url_icon
        add_torrent_button.image = add_torrent_icon
        refresh_button.image = refresh_icon
        resume_all_button.image = resume_all_icon
        pause_all_button.image = pause_all_icon
        purge_records_button.image = purge_records_icon
        self.start_all_button.image = self.start_all_icon

        # initialize the buttons state
        self.start_all_state = 0

        # Add tooltips
        add_url_button.tooltip = "Add URL"
        add_torrent_button.tooltip = "Add Torrent"
        refresh_button.tooltip = "Refresh Task List"
        resume_all_button.tooltip = "Resume All"
        pause_all_button.tooltip = "Pause All"
        purge_records_button.tooltip = "Purge Records"
        self.start_all_button.tooltip = "Start/Stop"

        # Arrange buttons
        add_url_button.grid(column=0, row=0, padx=5)
        add_torrent_button.grid(column=1, row=0, padx=5)
        refresh_button.grid(column=2, row=0, padx=5)
        resume_all_button.grid(column=4, row=0, padx=5)
        pause_all_button.grid(column=5, row=0, padx=5)
        purge_records_button.grid(column=6, row=0, padx=5)
        self.start_all_button.grid(column=7, row=0, padx=5)

        # Create a labels
        add_url_label = Label(task_actions_bar, text="Add URL")
        add_torrent_label = Label(task_actions_bar, text="Torrent")
        refresh_label = Label(task_actions_bar, text="Refresh")
        resume_all_label = Label(task_actions_bar, text="Resume")
        pause_all_label = Label(task_actions_bar, text="Pause")
        purge_records_label = Label(task_actions_bar, text="Clear")
        start_all_label = Label(task_actions_bar, text="Start")

        # Arrange labels
        add_url_label.grid(column=0, row=1, padx=5)
        add_torrent_label.grid(column=1, row=1, padx=5)
        refresh_label.grid(column=2, row=1, padx=5)
        resume_all_label.grid(column=4, row=1, padx=5)
        pause_all_label.grid(column=5, row=1, padx=5)
        purge_records_label.grid(column=6, row=1, padx=5)
        start_all_label.grid(column=7, row=1, padx=5)

    def create_left_panel(self, frame):
        left_pane = Panedwindow(frame, orient=VERTICAL)
        left_pane.grid(column=0, row=2, sticky=EW, padx=0, pady=0, columnspan=1)

        # Treeview for Categories
        categories_tree = Treeview(left_pane, columns=("Categories"), show="headings")
        categories_tree.heading("Categories", text="Categories")
        categories_tree.insert("", "end", text="All", values=["All"])
        categories_tree.insert("", "end", text="Active", values=["Active"])
        categories_tree.insert("", "end", text="Inactive", values=["Inactive"])
        categories_tree.insert("", "end", text="Completed", values=["Completed"])
        categories_tree.insert("", "end", text="Downloading", values=["Downloading"])
        categories_tree.insert("", "end", text="Paused", values=["Paused"])
        categories_tree.insert("", "end", text="Queued", values=["Queued"])
        categories_tree.insert("", "end", text="Seeding", values=["Seeding"])

        # Add left_pane widget with a specific size
        left_pane.add(categories_tree)

    def create_center_panel(self, frame):
        center_pane = Panedwindow(frame, orient=VERTICAL)
        center_pane.grid(column=1, row=2, sticky=NSEW, padx=5, pady=5, columnspan=2)

        # Treeview for Download List
        _columns = ("GID", "Status", "Progress", "Action")
        download_list_tree = Treeview(center_pane, columns=_columns, show="headings")
        download_list_tree.heading("GID", text="GID")
        download_list_tree.heading("Status", text="Status")
        download_list_tree.heading("Progress", text="Progress")
        download_list_tree.heading("Action", text="Action")
        center_pane.add(download_list_tree)

        # Add a vertical scrollbar
        scrollbar = Scrollbar(
            self.mainframe, orient="vertical", command=download_list_tree.yview
        )
        download_list_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(column=5, row=2, sticky=NS)

        # Add a horizontal scrollbar
        scrollbar = Scrollbar(
            self.mainframe, orient="horizontal", command=download_list_tree.xview
        )
        download_list_tree.configure(xscrollcommand=scrollbar.set)
        scrollbar.grid(column=1, row=3, sticky=EW, columnspan=4)

        # add sample values to the center_panel
        for i in range(21):
            download_list_tree.insert(
                "",
                "end",
                text="Sample",
                values=[f"Lorem_a{i}", f"Lorem_b{i}", f"Lorem_c{i}", f"Lorem_d{i}"],
            )

    def create_right_panel(self):
        # ... (implement your right panel here)
        pass

    def create_bottom_status_bar(self, frame):
        satus_bar = Panedwindow(frame)
        satus_bar.grid(column=0, row=3, sticky=EW, columnspan=5)

        #  Load images & Resize the image
        #  speed_limit button icons
        self.low_speed_limit_icon = PhotoImage(
            file=relative_to_assets("bt-sp1.png")
        ).subsample(15, 15)
        self.medium_speed_limit_icon = PhotoImage(
            file=relative_to_assets("bt-sp2.png")
        ).subsample(15, 15)
        self.high_speed_limit_icon = PhotoImage(
            file=relative_to_assets("bt-sp3.png")
        ).subsample(15, 15)
        # sample status_info button icons
        self.status_info1_icon = PhotoImage(
            file=relative_to_assets("bt-1.png")
        ).subsample(15, 15)
        self.status_info2_icon = PhotoImage(
            file=relative_to_assets("bt-2.png")
        ).subsample(15, 15)
        self.status_info3_icon = PhotoImage(
            file=relative_to_assets("bt-3.png")
        ).subsample(15, 15)
        self.status_info4_icon = PhotoImage(
            file=relative_to_assets("bt-4.png")
        ).subsample(15, 15)
        self.status_info5_icon = PhotoImage(
            file=relative_to_assets("bt-5.png")
        ).subsample(15, 15)

        # sample status elements Row 0
        progress_bar = Progressbar(
            satus_bar, orient=HORIZONTAL, mode="indeterminate", length=100
        )
        dl_speed = Label(satus_bar, text="0.00 KiB/s" + " ↓")
        ul_speed = Label(satus_bar, text="0.00 KiB/s" + " ↑")
        time_remaining = Label(satus_bar, text="00:00:00")
        time_elapsed = Label(satus_bar, text="00:00:00")
        active_downloads = Label(satus_bar, text="0/21")
        waiting_downloads = Label(satus_bar, text="0/21")
        stopped_downloads = Label(satus_bar, text="21/21")
        self.speed_limit_button = Button(
            satus_bar,
            image=self.medium_speed_limit_icon,
            command=self.change_speed_limit,
        )
        self.status_info_button = Button(
            satus_bar, image=self.status_info1_icon, command=self.change_status_info
        )

        # sample status labels Row 1
        status_label = Label(satus_bar, text="Status: ")
        download_speed_label = Label(satus_bar, text="Download Speed: ")
        upload_speed_label = Label(satus_bar, text="Upload Speed: ")
        time_elapsed_label = Label(satus_bar, text="Time Elapsed: ")
        time_remaining_label = Label(satus_bar, text="Time Remaining: ")
        active_downloads_label = Label(satus_bar, text="Active: ")
        waiting_downloads_label = Label(satus_bar, text="Waiting: ")
        stopped_downloads_label = Label(satus_bar, text="Stopped: ")
        speed_limit_label = Label(satus_bar, text="Speed Limiter ")
        status_info_label = Label(satus_bar, text="Status Info: ")

        # Initialize the progress bar & buttons
        progress_bar.start(10)
        self.speed_limit_state = 1
        self.status_info_state = 1

        # Attach icons to buttons
        self.status_info_button.image = self.status_info1_icon
        self.speed_limit_button.image = self.medium_speed_limit_icon

        # Arrange layout
        # Row 0
        progress_bar.grid(column=0, row=0, sticky=EW)
        dl_speed.grid(column=2, row=0, sticky=S, padx=5)
        ul_speed.grid(column=3, row=0, sticky=S, padx=5)
        time_elapsed.grid(column=4, row=0, sticky=S, padx=5)
        time_remaining.grid(column=5, row=0, sticky=S, padx=5)
        active_downloads.grid(column=6, row=0, sticky=S, padx=5)
        waiting_downloads.grid(column=7, row=0, sticky=S, padx=5)
        stopped_downloads.grid(column=8, row=0, sticky=S, padx=5)
        self.speed_limit_button.grid(column=9, row=0, sticky=NS, padx=5)
        self.status_info_button.grid(column=10, row=0, sticky=NS, padx=5)
        # Row 1
        status_label.grid(column=0, row=1, sticky=EW)
        download_speed_label.grid(column=2, row=1, sticky=EW, padx=10)
        upload_speed_label.grid(column=3, row=1, sticky=EW, padx=10)
        time_elapsed_label.grid(column=4, row=1, sticky=EW, padx=10)
        time_remaining_label.grid(column=5, row=1, sticky=EW, padx=10)
        active_downloads_label.grid(column=6, row=1, sticky=EW, padx=10)
        waiting_downloads_label.grid(column=7, row=1, sticky=EW, padx=10)
        stopped_downloads_label.grid(column=8, row=1, sticky=EW, padx=10)
        speed_limit_label.grid(column=9, row=1, sticky=EW, padx=10)
        status_info_label.grid(column=10, row=1, sticky=EW, padx=10)

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
        self.start_all_state = (self.start_all_state + 1) % 2
        if self.start_all_state == 1:
            self.start_all_button.config(image=self.stop_all_icon)
            self.start_all_button.image = self.stop_all_icon
        else:
            self.start_all_button.config(image=self.start_all_icon)
            self.start_all_button.image = self.start_all_icon

    def resume_all(self):
        # Implement the resume all functionality
        pass

    def pause_all(self):
        # Implement the pause all functionality
        pass

    def purge_task_records(self):
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

    def change_status_info(self):
        # changes the status_info button icon on click
        # depending on the number of clicks
        self.status_info_state = (self.status_info_state + 1) % 5
        if self.status_info_state == 0:
            self.status_info_button.config(image=self.status_info1_icon)
            self.status_info_button.image = self.status_info1_icon
        elif self.status_info_state == 1:
            self.status_info_button.config(image=self.status_info2_icon)
            self.status_info_button.image = self.status_info2_icon
        elif self.status_info_state == 2:
            self.status_info_button.config(image=self.status_info3_icon)
            self.status_info_button.image = self.status_info3_icon
        elif self.status_info_state == 3:
            self.status_info_button.config(image=self.status_info4_icon)
            self.status_info_button.image = self.status_info4_icon
        elif self.status_info_state == 4:
            self.status_info_button.config(image=self.status_info5_icon)
            self.status_info_button.image = self.status_info5_icon


# Create and run the app
root = Tk()
app = App(root)
root.mainloop()
