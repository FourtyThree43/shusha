import pathlib
import tkinter as tk
from tkinter.filedialog import askdirectory

import ttkbootstrap as ttk


class AddWindow(ttk.Toplevel):

    def __init__(self):
        super().__init__()
        self.title("Add Download")
        self.geometry("720x380+50+50")
        self.resizable(False, False)
        self.config(padx=15, pady=15)

        # create notebook
        add_dl_notebook = ttk.Notebook(self)
        add_dl_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # application variables
        _url = ""
        _path = pathlib.Path().absolute().as_posix()
        _rename = ""
        _split = 8

        self.url_var = ttk.StringVar(value=_url)
        self.path_var = ttk.StringVar(value=_path)
        self.rename_var = ttk.StringVar(value=_rename)
        self.split_var = ttk.IntVar(value=_split)

        self.create_page_frames(add_dl_notebook)
        self.create_url_page()
        self.create_torrent_page()
        self.create_schedule_page()

    def create_page_frames(self, notebook: ttk.Notebook):
        """Create notebook pages"""
        # URL Page
        self.url_page = ttk.Frame(notebook)
        notebook.add(self.url_page, text="URL")

        # Torrent Page
        self.torrent_page = ttk.Frame(notebook)
        notebook.add(self.torrent_page, text="Torrent")

        # Schedule Page
        self.schedule_page = ttk.Frame(notebook)
        notebook.add(self.schedule_page, text="Schedule")

    def create_page(self, master, torrent=False):
        """Create URL page"""

        #  header for Url and Options
        url_row = ttk.Frame(master)
        url_row.pack(fill=tk.X, expand=tk.YES)
        url_lbl = ttk.Label(url_row, text="URL:", width=5)
        url_lbl.pack(side=tk.LEFT, padx=(15, 0))
        main_ent = ttk.Entry(url_row,
                             textvariable=self.url_var,
                             bootstyle=ttk.WARNING)
        if torrent:
            main_ent.configure(state="readonly")
        main_ent.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=tk.YES,
            padx=5,
            pady=5,
        )

        # header and labelframe option container
        option_lf = ttk.Labelframe(master, text="File Download Options")
        option_lf.pack(
            fill=tk.BOTH,
            expand=tk.YES,
            padx=5,
            ipady=30,
            anchor=tk.N,
        )

        # rename row
        rename_row = ttk.Frame(option_lf)
        rename_row.pack(fill=tk.X, expand=tk.YES)

        rename_lbl = ttk.Label(rename_row, text="Rename:", width=8)
        rename_lbl.pack(side=tk.LEFT, padx=(15, 0))
        rename_ent = ttk.Entry(rename_row,
                               textvariable=self.rename_var,
                               bootstyle=ttk.WARNING)
        rename_ent.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=5)

        splits_lbl = ttk.Label(rename_row, text="Splits:", width=8)
        splits_lbl.pack(side=tk.LEFT, padx=(15, 0))
        splits_spinbox = ttk.Spinbox(
            rename_row,
            textvariable=self.split_var,
            from_=1,
            to=64,
            width=3,
            bootstyle=ttk.WARNING,
        )
        splits_spinbox.pack(side=tk.LEFT, padx=(0, 15))

        # path row
        path_row = ttk.Frame(option_lf)
        path_row.pack(fill=tk.X, expand=tk.YES)
        path_lbl = ttk.Label(path_row, text="Save to:", width=8)
        path_lbl.pack(side=tk.LEFT, padx=(15, 0))
        path_ent = ttk.Entry(
            path_row,
            textvariable=self.path_var,
            bootstyle=ttk.WARNING,
        )
        path_ent.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=5)

        browse_btn = ttk.Button(
            master=path_row,
            text="Browse",
            command=self.on_browse,
            width=8,
            bootstyle=ttk.WARNING,
        )
        browse_btn.pack(side=tk.LEFT, padx=5)

        # submit row
        submit_row = ttk.Frame(master)
        submit_row.pack(fill=tk.X, expand=tk.YES, pady=(20, 0))

        submit_btn = ttk.Button(
            master=submit_row,
            text="Submit",
            command=self.on_add_url,
            width=8,
            bootstyle=ttk.SUCCESS,
        )
        submit_btn.pack(side=tk.RIGHT, padx=5)

        cancel_btn = ttk.Button(
            master=submit_row,
            text="Cancel",
            command=self.destroy,
            width=8,
            bootstyle=ttk.DANGER,
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

    def create_url_page(self):
        self.create_page(self.url_page)

    def create_torrent_page(self):
        """Create Torrent page"""
        self.create_page(self.torrent_page, torrent=True)

    def create_schedule_page(self):
        """Create Schedule page"""
        # schedule_page = notebook.nametowidget(notebook.tabs()[2])
        schedule_row = ttk.Frame(self.schedule_page)
        schedule_row.pack(fill=tk.X, expand=tk.YES)
        schedule_lbl = ttk.Label(schedule_row, text="Schedule", width=8)
        schedule_lbl.pack(side=tk.LEFT, padx=(15, 0))
        schedule_ent = ttk.Entry(schedule_row)
        schedule_ent.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=5)

        add_btn = ttk.Button(
            master=schedule_row,
            text="Add",
            command=lambda: print("add schedule"),
            width=8,
        )
        add_btn.pack(side=tk.LEFT, padx=5)

    def on_add_url(self):
        """Callback for add url button"""
        if self.url_var.get():
            print(f"add url: {self.url_var.get()}")

    def on_add_torrent(self):
        """Callback for add torrent button"""
        print("add torrent")

    def on_browse(self):
        """Callback for directory browse"""
        path = askdirectory(title="Browse directory")
        if path:
            self.path_var.set(path)
            print(self.path_var.get())


if __name__ == "__main__":
    root = ttk.Window(themename="darkly", position=(900, 100))
    AddWindow()
    root.mainloop()
