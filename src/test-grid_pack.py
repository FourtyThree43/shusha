from pathlib import Path
import tkinter as tk
from tkinter import ttk

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path("gui/assets/")


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)


class App:

    def __init__(self, root) -> None:
        self.master = root

        self.master.title("Pack Demo: Shusha")
        self.master.iconbitmap(relative_to_assets("beanonymous.ico"))
        self.master.geometry("850x550")
        self.master.configure(background="wheat1")
        self.master.configure(highlightbackground="thistle3")
        self.master.configure(highlightcolor="thistle4")
        # self.master.state(newstate="zoomed")

        self.create_menu_bar()
        self.create_top_frame()
        self.create_center_frame()
        self.create_bottom_frame()

        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

    def run(self) -> None:
        self.master.mainloop()

    def on_close(self) -> None:
        self.master.destroy()

    def create_menu_bar(self) -> None:
        menu_bar = tk.Menu(self.master)
        self.master.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        task_menu = tk.Menu(menu_bar, tearoff=0)
        view_menu = tk.Menu(menu_bar, tearoff=0)
        sort_menu = tk.Menu(view_menu, tearoff=0)  # Create a submenu
        options_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu = tk.Menu(menu_bar, tearoff=0)

        # Add items to the submenu
        menu_bar.add_cascade(label="File", menu=file_menu)
        menu_bar.add_cascade(label="Tasks", menu=task_menu)
        menu_bar.add_cascade(label="View", menu=view_menu)
        menu_bar.add_cascade(label="Options", menu=options_menu)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        # Add sub-items to menu items
        file_menu.add_command(label="Open")
        file_menu.add_command(label="Save")
        file_menu.add_command(label="Rename")
        file_menu.add_separator()
        file_menu.add_command(label="Add Urls")
        file_menu.add_command(label="Add Batch")
        file_menu.add_command(label="Add Torrent")
        file_menu.add_command(label="Refresh Task List")
        file_menu.add_separator()
        file_menu.add_command(label="Import")
        file_menu.add_command(label="Export")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)

        task_menu.add_command(label="Resume")
        task_menu.add_command(label="Pause")
        task_menu.add_command(label="Cancel")
        task_menu.add_command(label="Remove")
        task_menu.add_command(label="Remove Completed")
        task_menu.add_separator()
        task_menu.add_command(label="Move Top")
        task_menu.add_command(label="Move Up")
        task_menu.add_command(label="Move Down")
        task_menu.add_command(label="Move Bottom")

        view_menu.add_checkbutton(label="Category")
        sort_menu.add_checkbutton(label="Sort Ascending")
        sort_menu.add_checkbutton(label="Sort Descending")
        view_menu.add_cascade(label="Sort: Filename", menu=sort_menu)
        view_menu.add_checkbutton(label="Filename")
        view_menu.add_checkbutton(label="Size")
        view_menu.add_checkbutton(label="Progress")
        view_menu.add_checkbutton(label="Download Speed")
        view_menu.add_checkbutton(label="Upload Speed")
        view_menu.add_checkbutton(label="ETA")
        view_menu.add_checkbutton(label="Status")
        view_menu.add_checkbutton(label="Note")

        options_menu.add_command(label="Settings")
        options_menu.add_command(label="Scheduler")
        options_menu.add_command(label="Speed Limit")
        options_menu.add_command(label="Plugin")

        help_menu.add_command(label="About")
        help_menu.add_command(label="Online Help")
        help_menu.add_command(label="Forum")
        help_menu.add_command(label="Discord")
        help_menu.add_command(label="Report Bug")
        help_menu.add_command(label="Donate")

    def create_top_frame(self) -> None:
        tp_frame = tk.Frame(self.master, bg="seagreen1", height=20)
        tp_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        #  load Images
        add_dl_icon = tk.PhotoImage().subsample(1, 1)
        resume_dl_icon = tk.PhotoImage().subsample(1, 1)
        pause_dl_icon = tk.PhotoImage().subsample(1, 1)
        scheduler_icon = tk.PhotoImage().subsample(1, 1)
        queue_top_icon = tk.PhotoImage().subsample(1, 1)
        queue_botom_icon = tk.PhotoImage().subsample(1, 1)
        remove_dl_icon = tk.PhotoImage().subsample(1, 1)
        purge_list_icon = tk.PhotoImage().subsample(1, 1)
        refresh_icon = tk.PhotoImage().subsample(1, 1)
        setting_icon = tk.PhotoImage().subsample(1, 1)

        # Buttons
        add_dl_button = ttk.Button(master=tp_frame, text="Add")
        resume_dl_button = ttk.Button(master=tp_frame, text="Resume")
        pause_dl_button = ttk.Button(master=tp_frame, text="Pause")
        scheduler_button = ttk.Button(master=tp_frame, text="Scheduler")
        queue_top_button = ttk.Button(master=tp_frame, text="Up")
        queue_botom_button = ttk.Button(master=tp_frame, text="Down")
        remove_dl_button = ttk.Button(master=tp_frame, text="Remove")
        purge_list_button = ttk.Button(master=tp_frame, text="Clear")
        refresh_button = ttk.Button(master=tp_frame, text="Refresh")
        setting_button = ttk.Button(master=tp_frame, text="Settings")

        # Button layout
        add_dl_button.pack(fill=tk.BOTH, side=tk.LEFT)
        resume_dl_button.pack(fill=tk.BOTH, side=tk.LEFT)
        pause_dl_button.pack(fill=tk.BOTH, side=tk.LEFT)
        scheduler_button.pack(fill=tk.BOTH, side=tk.LEFT)
        queue_top_button.pack(fill=tk.BOTH, side=tk.LEFT)
        queue_botom_button.pack(fill=tk.BOTH, side=tk.LEFT)
        remove_dl_button.pack(fill=tk.BOTH, side=tk.LEFT)
        purge_list_button.pack(fill=tk.BOTH, side=tk.LEFT)
        refresh_button.pack(fill=tk.BOTH, side=tk.LEFT)
        setting_button.pack(fill=tk.BOTH, side=tk.RIGHT)

    def create_center_frame(self) -> None:
        ct_frame = ttk.PanedWindow(self.master, orient=tk.HORIZONTAL)
        ct_frame.pack(fill=tk.BOTH, expand=True, padx=5)

        category_list = ttk.Treeview(master=ct_frame,
                                     columns="Categories",
                                     show="headings")
        category_list.heading("Categories", text="Categories")
        ct_frame.add(category_list)

        _columns = [
            "Filename", "Status", "Size", "Progress", "Speed", "ETA", "Date",
            "Note"
        ]
        download_list = ttk.Treeview(master=ct_frame,
                                     columns=_columns,
                                     show="headings")
        download_list.heading("Filename", text="Filename")
        download_list.heading("Status", text="Status")
        download_list.heading("Size", text="Size")
        download_list.heading("Progress", text="Progress")
        download_list.heading("Speed", text="Speed")
        download_list.heading("ETA", text="ETA")
        download_list.heading("Date", text="Date Added")
        download_list.heading("Note", text="Note")
        ct_frame.add(download_list)

        # add items to category_list
        for i in range(1, 10):
            category_list.insert(parent="",
                                 index=tk.END,
                                 values=[f"Lorem {i}"])

        # add items to download_list
        for i in range(1, 5):
            download_list.insert(parent="",
                                 index=tk.END,
                                 values=[
                                     f"Lorem Ipsum dolor sit amet {i}",
                                     f"Downloading", f"690 MB", f"4.20%",
                                     f"666.33 KB/s", f"20.13m",
                                     f"Dec 24 08:36:59 2023"
                                 ])

    def create_bottom_frame(self) -> None:
        bt_frame = tk.Frame(self.master, bg="palegreen4", height=50)
        bt_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)

    app.run()
