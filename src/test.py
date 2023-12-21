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
        self.master.geometry("540x540+664+580")
        self.master.minsize(1050, 480)
        self.master.maxsize(1920, 1080)
        self.master.resizable(1, 1)
        self.master.configure(background="wheat")
        self.master.configure(highlightbackground="wheat")
        self.master.configure(highlightcolor="black")
        self.master.title("Download Manager")

        # Mainframe a frame widge that will contain all the widgets
        self.mainframe = ttk.Frame(self.master, padding="3 3 12 12")
        self.mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
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
        menu_bar.grid(column=0, row=0, sticky=(tk.W, tk.E))

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
        file_menu.add_command(label="Exit", command=self.master.quit)

        # Display the menu
        self.master.config(menu=menu)

    def create_task_actions_bar(self):
        # task_actions_bar = ttk.Frame(self.mainframe)
        task_actions_bar = tk.PanedWindow(self.mainframe, orient=tk.HORIZONTAL)
        task_actions_bar.grid(column=1, row=1, sticky=(tk.W, tk.E))

        # Load images
        add_url_icon = tk.PhotoImage(file=relative_to_assets("button_2.png"))
        add_torrent_icon = tk.PhotoImage(
            file=relative_to_assets("button_2.png"))
        refresh_icon = tk.PhotoImage(file=relative_to_assets("button_2.png"))
        start_all_icon = tk.PhotoImage(file=relative_to_assets("button_2.png"))
        resume_all_icon = tk.PhotoImage(
            file=relative_to_assets("button_2.png"))
        pause_all_icon = tk.PhotoImage(file=relative_to_assets("button_2.png"))
        purge_completed_icon = tk.PhotoImage(
            file=relative_to_assets("button_3.png"))

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
        left_pane.grid(column=0, row=2, sticky=(tk.W, tk.E), padx=0, pady=0)

        # Treeview for Categories
        categories_tree = ttk.Treeview(left_pane,
                                       columns=("Categories", ),
                                       show="headings")
        categories_tree.heading("Categories", text="Categories")

        # Add left_pane widget with a specific size
        left_pane.add(categories_tree)

    def create_center_panel(self):
        center_pane = ttk.Panedwindow(self.mainframe, orient=tk.VERTICAL)
        center_pane.grid(column=1,
                         row=2,
                         sticky=(tk.W, tk.E, tk.N, tk.S),
                         padx=5,
                         pady=5)

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
        scrollbar.grid(column=2, row=2, sticky=(tk.N, tk.S))

    def create_right_panel(self):
        # ... (implement your right panel here)
        pass

    def create_bottom_status_bar(self):
        # ... (implement your bottom status bar here)
        pass

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


# Create and run the app
root = tk.Tk()
app = App(root)
root.mainloop()
