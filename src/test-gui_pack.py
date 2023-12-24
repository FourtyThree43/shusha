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
        self.master.iconbitmap(relative_to_assets("shusha.ico"))
        self.master.geometry("1200x550")
        self.master.configure(background="wheat3")
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
        tp_frame = tk.Frame(self.master, bg="wheat4", height=2)
        tp_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        #  load Images
        add_dl_icon = tk.PhotoImage(
            file=relative_to_assets("bt-add.png")).subsample(10, 10)
        resume_dl_icon = tk.PhotoImage(
            file=relative_to_assets("bt-play.png")).subsample(10, 10)
        pause_dl_icon = tk.PhotoImage(
            file=relative_to_assets("bt-pause.png")).subsample(10, 10)
        scheduler_icon = tk.PhotoImage(
            file=relative_to_assets("bt-schedule.png")).subsample(10, 10)
        queue_top_icon = tk.PhotoImage(
            file=relative_to_assets("bt-top.png")).subsample(10, 10)
        queue_botom_icon = tk.PhotoImage(
            file=relative_to_assets("bt-bottom.png")).subsample(10, 10)
        remove_dl_icon = tk.PhotoImage(
            file=relative_to_assets("bt-remove.png")).subsample(10, 10)
        purge_list_icon = tk.PhotoImage(
            file=relative_to_assets("bt-clear.png")).subsample(10, 10)
        refresh_icon = tk.PhotoImage(
            file=relative_to_assets("bt-refresh.png")).subsample(10, 10)
        setting_icon = tk.PhotoImage(
            file=relative_to_assets("bt-setting.png")).subsample(10, 10)

        # Buttons
        add_dl_button = ttk.Button(master=tp_frame,
                                   text="Add",
                                   image=add_dl_icon,
                                   command=self.add_download)
        resume_dl_button = ttk.Button(master=tp_frame,
                                      text="Resume",
                                      image=resume_dl_icon)
        pause_dl_button = ttk.Button(master=tp_frame,
                                     text="Pause",
                                     image=pause_dl_icon)
        scheduler_button = ttk.Button(master=tp_frame,
                                      text="Scheduler",
                                      image=scheduler_icon)
        queue_top_button = ttk.Button(master=tp_frame,
                                      text="Up",
                                      image=queue_top_icon)
        queue_botom_button = ttk.Button(master=tp_frame,
                                        text="Down",
                                        image=queue_botom_icon)
        remove_dl_button = ttk.Button(master=tp_frame,
                                      text="Remove",
                                      image=remove_dl_icon)
        purge_list_button = ttk.Button(master=tp_frame,
                                       text="Clear",
                                       image=purge_list_icon)
        refresh_button = ttk.Button(master=tp_frame,
                                    text="Refresh",
                                    image=refresh_icon)
        setting_button = ttk.Button(master=tp_frame,
                                    text="Settings",
                                    image=setting_icon)

        # Attach icons to buttons
        add_dl_button.image = add_dl_icon
        resume_dl_button.image = resume_dl_icon
        pause_dl_button.image = pause_dl_icon
        scheduler_button.image = scheduler_icon
        queue_top_button.image = queue_top_icon
        queue_botom_button.image = queue_botom_icon
        remove_dl_button.image = remove_dl_icon
        purge_list_button.image = purge_list_icon
        refresh_button.image = refresh_icon
        setting_button.image = setting_icon

        # Button layout
        add_dl_button.pack(fill=tk.BOTH, side=tk.LEFT, ipadx=20)
        resume_dl_button.pack(fill=tk.BOTH, side=tk.LEFT, ipadx=20)
        pause_dl_button.pack(fill=tk.BOTH, side=tk.LEFT, ipadx=20)
        scheduler_button.pack(fill=tk.BOTH, side=tk.LEFT, ipadx=20)
        queue_top_button.pack(fill=tk.BOTH, side=tk.LEFT, ipadx=20)
        queue_botom_button.pack(fill=tk.BOTH, side=tk.LEFT, ipadx=20)
        remove_dl_button.pack(fill=tk.BOTH, side=tk.LEFT, ipadx=20)
        purge_list_button.pack(fill=tk.BOTH, side=tk.LEFT, ipadx=20)
        refresh_button.pack(fill=tk.BOTH, side=tk.LEFT, ipadx=20)
        setting_button.pack(fill=tk.BOTH, side=tk.RIGHT, ipadx=20)

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

        _categories = [
            "All",
            "Active",
            "Completed",
            "Seeding",
            "Inactive",
            "Error",
            "Paused",
            "Queued",
        ]
        # add items to category_list
        for c in _categories:
            category_list.insert(parent="", index=tk.END, values=[c])

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
        bt_frame = tk.Frame(self.master, bg="wheat3", height=10)
        bt_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def add_download(self) -> None:
        add_dl_window = tk.Toplevel(self.master)
        add_dl_window.title("Add Download")
        add_dl_window.iconbitmap(relative_to_assets("shusha.ico"))
        add_dl_window.geometry("500x300")
        add_dl_window.configure(background="wheat3")

        #  Notebook Pages: URL | Torrent | Schedule
        add_dl_notebook = ttk.Notebook(add_dl_window)
        add_dl_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # URL Page
        url_page = ttk.Frame(add_dl_notebook)
        add_dl_notebook.add(url_page, text="URL")

        # Torrent Page
        torrent_page = ttk.Frame(add_dl_notebook)
        add_dl_notebook.add(torrent_page, text="Torrent")

        # Schedule Page
        schedule_page = ttk.Frame(add_dl_notebook)
        add_dl_notebook.add(schedule_page, text="Schedule")

        # URL Page
        url_label = ttk.Label(master=url_page, text="URL:")
        url_label.pack(fill=tk.BOTH, side=tk.TOP, padx=5, pady=5)

        url_entry = ttk.Entry(master=url_page)
        url_entry.pack(fill=tk.BOTH, side=tk.TOP, padx=5, pady=5, ipady=20)

        url_add_button = ttk.Button(master=url_page, text="Add")
        url_add_button.pack(fill=tk.BOTH, side=tk.TOP, padx=5, pady=5, ipady=5)

        # Torrent Page
        torrent_label = ttk.Label(master=torrent_page, text="Torrent:")
        torrent_label.pack(fill=tk.BOTH, side=tk.TOP, padx=5, pady=5)

        torrent_entry = ttk.Entry(master=torrent_page)
        torrent_entry.pack(fill=tk.BOTH, side=tk.TOP, padx=5, pady=5, ipady=20)

        tor_add_button = ttk.Button(master=torrent_page, text="Add")
        tor_add_button.pack(fill=tk.BOTH, side=tk.TOP, padx=5, pady=5, ipady=5)

        # Schedule Page
        schedule_checkbox = ttk.Checkbutton(master=schedule_page,
                                            text="Enable Schedule")
        schedule_checkbox.pack(padx=5, pady=5)

        schedule_m = ttk.Checkbutton(master=schedule_page, text="Monday")
        schedule_t = ttk.Checkbutton(master=schedule_page, text="Tuesday")
        schedule_w = ttk.Checkbutton(master=schedule_page, text="Wednesday")
        schedule_th = ttk.Checkbutton(master=schedule_page, text="Thursday")
        schedule_f = ttk.Checkbutton(master=schedule_page, text="Friday")
        schedule_s = ttk.Checkbutton(master=schedule_page, text="Saturday")
        schedule_su = ttk.Checkbutton(master=schedule_page, text="Sunday")

        schedule_m.pack(fill=tk.X)
        schedule_t.pack(fill=tk.X)
        schedule_w.pack(fill=tk.X)
        schedule_th.pack(fill=tk.X)
        schedule_f.pack(fill=tk.X)
        schedule_s.pack(fill=tk.X)
        schedule_su.pack(fill=tk.X)

        schedule_add_button = ttk.Button(master=schedule_page, text="Add")
        schedule_add_button.pack(fill=tk.BOTH, side=tk.BOTTOM, padx=5, pady=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)

    app.run()
