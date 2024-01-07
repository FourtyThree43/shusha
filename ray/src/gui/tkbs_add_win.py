import pathlib
import tkinter as tk
from tkinter.filedialog import askdirectory

import ttkbootstrap as ttk


class AddWindow(ttk.Toplevel):

    def __init__(self, master):
        super().__init__(master)
        self.title("Add Download")
        self.geometry("720x380")
        self.resizable(False, False)
        self.config(padx=15, pady=15)

        # create notebook
        add_dl_notebook = ttk.Notebook(self)
        add_dl_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # application variables
        _url = "One URL task per line"
        self.url_var = ttk.StringVar(value=_url)
        _path = pathlib.Path().absolute().as_posix()

        self.path_var = ttk.StringVar(value=_path)

        _rename = "Optional"
        self.rename_var = ttk.StringVar(value=_rename)

        self.create_page_frames(add_dl_notebook)
        self.create_url_page(add_dl_notebook)
        self.create_torrent_page(add_dl_notebook)
        self.create_schedule_page(add_dl_notebook)

    def create_page_frames(self, notebook):
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

    def create_path_row(self):
        """Add path row to labelframe"""
        path_row = ttk.Frame(self.option_lf)
        path_row.pack(fill=tk.X, expand=tk.YES)
        path_lbl = ttk.Label(path_row, text="Path", width=8)
        path_lbl.pack(side=tk.LEFT, padx=(15, 0))
        path_ent = ttk.Entry(path_row, textvariable=self.path_var)
        path_ent.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=5)
        browse_btn = ttk.Button(master=path_row,
                                text="Browse",
                                command=self.on_browse,
                                width=8)
        browse_btn.pack(side=tk.LEFT, padx=5)

    def create_url_page(self, notebook):
        """Create URL page"""
        #  header for Url and Options
        url_page = notebook.nametowidget(notebook.tabs()[0])

        url_row = ttk.Frame(url_page)
        url_row.pack(fill=tk.X, expand=tk.YES)
        url_lbl = ttk.Label(url_row, text="URL:", width=8)
        url_lbl.pack(side=tk.LEFT, padx=(15, 0))
        url_ent = ttk.Entry(url_row, textvariable=self.url_var)
        url_ent.pack(side=tk.LEFT,
                     fill=tk.BOTH,
                     expand=tk.YES,
                     padx=5,
                     ipady=20)

        # header and labelframe option container
        option_lf = ttk.Labelframe(url_page, text="File Download Options")
        option_lf.pack(fill=tk.BOTH, expand=tk.YES, pady=20, anchor=tk.N)

        # rename row
        rename_row = ttk.Frame(option_lf)
        rename_row.pack(fill=tk.X, expand=tk.YES)

        rename_lbl = ttk.Label(rename_row, text="Rename:", width=8)
        rename_lbl.pack(side=tk.LEFT, padx=(15, 0))
        rename_ent = ttk.Entry(rename_row, textvariable=self.rename_var)
        rename_ent.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=5)

        splits_lbl = ttk.Label(rename_row, text="Splits", width=8)
        splits_lbl.pack(side=tk.LEFT, padx=(15, 0))
        splits_spinbox = ttk.Spinbox(rename_row, from_=8, to=64, width=3)
        splits_spinbox.pack(side=tk.LEFT, padx=(0, 15))

        # path row
        path_row = ttk.Frame(option_lf)
        path_row.pack(fill=tk.X, expand=tk.YES)
        path_lbl = ttk.Label(path_row, text="Path", width=8)
        path_lbl.pack(side=tk.LEFT, padx=(15, 0))
        path_ent = ttk.Entry(path_row, textvariable=self.path_var)
        path_ent.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=5)
        browse_btn = ttk.Button(master=path_row,
                                text="Browse",
                                command=self.on_browse,
                                width=8)
        browse_btn.pack(side=tk.LEFT, padx=5)

        add_btn = ttk.Button(master=url_row,
                             text="Add",
                             command=lambda: self.on_add_url(),
                             width=8)
        add_btn.pack(side=tk.LEFT, padx=5)

    def create_torrent_page(self, notebook):
        """Create Torrent page"""
        torrent_page = notebook.nametowidget(notebook.tabs()[1])
        torrent_row = ttk.Frame(torrent_page)
        torrent_row.pack(fill=tk.X, expand=tk.YES)
        torrent_lbl = ttk.Label(torrent_row, text="Torrent", width=8)
        torrent_lbl.pack(side=tk.LEFT, padx=(15, 0))
        torrent_ent = ttk.Entry(torrent_row)
        torrent_ent.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=5)
        add_btn = ttk.Button(master=torrent_row,
                             text="Add",
                             command=lambda: print("add torrent"),
                             width=8)
        add_btn.pack(side=tk.LEFT, padx=5)

    def create_schedule_page(self, notebook):
        """Create Schedule page"""
        schedule_page = notebook.nametowidget(notebook.tabs()[2])
        schedule_row = ttk.Frame(schedule_page)
        schedule_row.pack(fill=tk.X, expand=tk.YES)
        schedule_lbl = ttk.Label(schedule_row, text="Schedule", width=8)
        schedule_lbl.pack(side=tk.LEFT, padx=(15, 0))
        schedule_ent = ttk.Entry(schedule_row)
        schedule_ent.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=5)
        add_btn = ttk.Button(master=schedule_row,
                             text="Add",
                             command=lambda: print("add schedule"),
                             width=8)
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


if __name__ == '__main__':
    root = ttk.Window(position=(900, 100))
    app = AddWindow(root)
    root.mainloop()
