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
        tp_frame = tk.Frame(self.master)
        tp_frame.pack(fill=tk.X, expand=False)

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
        queue_btm_icon = tk.PhotoImage(
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
        queue_btm_button = ttk.Button(master=tp_frame,
                                      text="Down",
                                      image=queue_btm_icon)
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
        add_dl_button.image = add_dl_icon  # type: ignore[attr-defined]
        resume_dl_button.image = resume_dl_icon  # type: ignore[attr-defined]
        pause_dl_button.image = pause_dl_icon  # type: ignore[attr-defined]
        scheduler_button.image = scheduler_icon  # type: ignore[attr-defined]
        queue_top_button.image = queue_top_icon  # type: ignore[attr-defined]
        queue_btm_button.image = queue_btm_icon  # type: ignore[attr-defined]
        remove_dl_button.image = remove_dl_icon  # type: ignore[attr-defined]
        purge_list_button.image = purge_list_icon  # type: ignore[attr-defined]
        refresh_button.image = refresh_icon  # type: ignore[attr-defined]
        setting_button.image = setting_icon  # type: ignore[attr-defined]

        # Button layout
        add_dl_button.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)
        resume_dl_button.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)
        pause_dl_button.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)
        scheduler_button.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)
        queue_top_button.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)
        queue_btm_button.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)
        remove_dl_button.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)
        purge_list_button.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)
        refresh_button.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)
        setting_button.pack(fill=tk.BOTH, side=tk.RIGHT, padx=5, pady=5)

    def create_center_frame(self) -> None:
        ct_frame = ttk.PanedWindow(self.master, orient=tk.HORIZONTAL)
        ct_frame.pack(fill=tk.BOTH, expand=True)

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
        for i in range(1, 15):
            download_list.insert(parent="",
                                 index=tk.END,
                                 values=[
                                     f"Lorem Ipsum dolor sit amet {i}",
                                     f"Downloading", f"690 MB", f"4.20%",
                                     f"666.33 KB/s", f"20.13m",
                                     f"Dec 24 08:36:59 2023"
                                 ])

        # Scrollbars
        download_scrollbar = ttk.Scrollbar(master=ct_frame,
                                           orient=tk.VERTICAL,
                                           command=download_list.yview)
        download_list.configure(yscrollcommand=download_scrollbar.set)
        download_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_bottom_frame(self) -> None:
        bt_frame = tk.Frame(self.master, height=10)
        bt_frame.pack(fill=tk.X, expand=False)

        # Sample download statistics
        speed_up_label = ttk.Label(bt_frame, text="↑ 666.33 KB/s")
        speed_up_label.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)

        speed_dn_label = ttk.Label(bt_frame, text="↓ 2.45 MB/s")
        speed_dn_label.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)

        # Number of active and inactive downloads
        active_dl_label = ttk.Label(bt_frame, text="Active Downloads: 5")
        active_dl_label.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)

        inactive_dl_label = ttk.Label(bt_frame, text="Inactive Downloads: 3")
        inactive_dl_label.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)

        # Sample status icons
        sp_limit_icon = tk.PhotoImage(
            file=relative_to_assets("bt-speed2.png")).subsample(10, 10)
        status_icon_ok = tk.PhotoImage(
            file=relative_to_assets("bt-1.png")).subsample(10, 10)
        # status_icon_online = tk.PhotoImage(
        #     file=relative_to_assets("bt-2.png")).subsample(10, 10)
        # status_icon_offline = tk.PhotoImage(
        #     file=relative_to_assets("bt-3.png")).subsample(10, 10)
        # status_icon_warning = tk.PhotoImage(
        #     file=relative_to_assets("bt-4.png")).subsample(10, 10)
        # status_icon_danger = tk.PhotoImage(
        #     file=relative_to_assets("bt-5.png")).subsample(10, 10)

        status_info = ttk.Label(bt_frame, image=status_icon_ok)
        status_info.image = status_icon_ok  # type: ignore[attr-defined]
        status_info.pack(fill=tk.BOTH, side=tk.RIGHT, padx=5, pady=5)

        # Speed limiter button
        speed_limiter_button = ttk.Button(
            bt_frame,
            text="Speed Limiter:",
            image=sp_limit_icon,
            command=self.toggle_speed_limiter,
        )
        speed_limiter_button.image = sp_limit_icon  # type: ignore[attr-defined]
        speed_limiter_button.pack(fill=tk.X, side=tk.RIGHT, padx=5, pady=5)

    def toggle_speed_limiter(self) -> None:
        # Implement speed limiter toggle logic here
        print("Toggle Speed Limiter")

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
        u_frame0 = tk.Frame(master=url_page)
        u_frame1 = tk.Frame(master=url_page)
        u_frame2 = tk.Frame(master=url_page)
        u_frame3 = tk.Frame(master=url_page)
        u_frame0.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        u_frame1.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        u_frame2.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        u_frame3.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        url_entry = ttk.Entry(master=u_frame0)
        url_entry.pack(fill=tk.BOTH, side=tk.TOP, padx=5, pady=5, ipady=15)

        rename_label = ttk.Label(master=u_frame1, text="Rename:")
        rename_entry = ttk.Entry(master=u_frame1, width=30)
        rename_entry.insert(0, "Filename")
        rename_label.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)
        rename_entry.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)

        split_label = ttk.Label(master=u_frame1, text="Split:")
        split_entry = ttk.Entry(master=u_frame1, width=10)
        split_entry.insert(0, "0-64")
        split_label.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)
        split_entry.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)

        save_to_label = ttk.Label(master=u_frame2, text="Save To:")
        save_to_entry = ttk.Entry(master=u_frame2, width=50)
        save_to_entry.insert(0, "C:/Users/username/Downloads")
        save_to_label.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)
        save_to_entry.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)

        save_to_button = ttk.Button(master=u_frame2, text="Browse")
        save_to_button.pack(fill=tk.BOTH,
                            side=tk.LEFT,
                            padx=5,
                            pady=5,
                            ipady=5)

        url_add_button = ttk.Button(master=u_frame3, text="Add")
        url_add_button.pack(fill=tk.BOTH, side=tk.TOP, padx=5, pady=5, ipady=5)

        # Torrent Page
        t_frame0 = tk.Frame(master=torrent_page)
        t_frame1 = tk.Frame(master=torrent_page)
        t_frame2 = tk.Frame(master=torrent_page)
        t_frame3 = tk.Frame(master=torrent_page)
        t_frame0.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        t_frame1.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        t_frame2.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        t_frame3.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        torrent_entry = ttk.Entry(master=t_frame0, width=65)
        torrent_entry.insert(0, "Drag and drop torrent file here")
        torrent_entry.configure(state="readonly", justify="center")
        tor_open_button = ttk.Button(master=t_frame0, text="Open")
        torrent_entry.pack(fill=tk.BOTH,
                           side=tk.LEFT,
                           padx=5,
                           pady=5,
                           ipady=20)
        tor_open_button.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)

        magnet_label = ttk.Label(master=t_frame1, text="Magnet:")
        magnet_entry = ttk.Entry(master=t_frame1, width=80)
        magnet_label.pack(fill=tk.BOTH, side=tk.TOP, padx=5, pady=5)
        magnet_entry.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5, ipady=20)

        tor_add_button = ttk.Button(master=t_frame3, text="Add")
        tor_add_button.pack(fill=tk.BOTH, side=tk.TOP, padx=5, pady=5, ipady=5)

        # Schedule Page
        s_frame1 = tk.Frame(master=schedule_page, height=10, bg="wheat4")
        s_frame1.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        sched_checkbox = ttk.Checkbutton(master=s_frame1,
                                         text="Enable Schedule")
        sched_checkbox.pack(fill=tk.BOTH, side=tk.TOP, padx=5, pady=5)

        sched_m = ttk.Checkbutton(master=s_frame1, text="Monday")
        sched_t = ttk.Checkbutton(master=s_frame1, text="Tuesday")
        sched_w = ttk.Checkbutton(master=s_frame1, text="Wednesday")
        sched_th = ttk.Checkbutton(master=s_frame1, text="Thursday")
        sched_f = ttk.Checkbutton(master=s_frame1, text="Friday")
        sched_s = ttk.Checkbutton(master=s_frame1, text="Saturday")
        sched_su = ttk.Checkbutton(master=s_frame1, text="Sunday")

        sched_m.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)
        sched_t.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)
        sched_w.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)
        sched_th.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)
        sched_f.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)
        sched_s.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)
        sched_su.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)

        sched_button = ttk.Button(master=schedule_page, text="Add")
        sched_button.pack(fill=tk.BOTH,
                          side=tk.BOTTOM,
                          padx=5,
                          pady=5,
                          ipady=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)

    app.run()
