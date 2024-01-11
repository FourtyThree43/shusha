import pathlib
import tkinter as tk
from tkinter.filedialog import askdirectory

import ttkbootstrap as ttk


class AddWindow(ttk.Toplevel):

    def __init__(self, callback):
        super().__init__(callback)
        self.title("Add Download")
        self.geometry("720x380")
        self.resizable(False, False)
        self.config(padx=15, pady=15)

        self.callback = callback
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
        self.checkbox_var = tk.BooleanVar(value=False)
        self.rename_var = ttk.StringVar(value=_rename)
        self.split_var = ttk.IntVar(value=_split)

        self.create_page_frames(add_dl_notebook)
        self.create_url_page(add_dl_notebook)
        self.create_torrent_page(add_dl_notebook)
        self.create_schedule_page(add_dl_notebook)

    def parse_lines_to_stringvars(self):
        content = self.urls.get("1.0", tk.END).strip()
        lines = content.split("\n")
        var_list = [ttk.StringVar(value=line) for line in lines]
        return var_list

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

    def create_url_page(self, notebook):
        """Create URL page"""
        #  header for Url and Options
        url_page = notebook.nametowidget(notebook.tabs()[0])

        url_row = ttk.Frame(url_page)
        url_row.pack(fill=tk.X, expand=tk.YES)
        url_lbl = ttk.Label(url_row, text="URLs:", width=5)
        url_lbl.pack(side=tk.LEFT, padx=(15, 0))
        self.urls = ttk.ScrolledText(
            url_row,
            wrap=tk.WORD,
            width=97,
            height=6,
        )
        self.urls.pack(side=tk.LEFT, expand=True, padx=5, pady=5)

        # header and labelframe option container
        option_lf = ttk.Labelframe(url_page, text="File Download Options")
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

        checkbox = ttk.Checkbutton(
            rename_row,
            variable=self.checkbox_var,
            command=lambda: self.on_checkbox_click(
                self.checkbox_var,
                self.rename_ent1,
            ),
            bootstyle=ttk.WARNING,
        )
        checkbox.pack(side=tk.LEFT, padx=(15, 0))

        rename_lbl = ttk.Label(rename_row, text="Rename:", width=8)
        rename_lbl.pack(side=tk.LEFT, padx=(15, 0))
        self.rename_ent1 = ttk.Entry(
            rename_row,
            textvariable=self.rename_var,
            bootstyle=ttk.WARNING,
        )
        self.rename_ent1.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=5)

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
        submit_row = ttk.Frame(url_page)
        submit_row.pack(fill=tk.X, expand=tk.YES, pady=(20, 0))

        submit_btn = ttk.Button(
            master=submit_row,
            text="Submit",
            command=lambda: self.submit(),
            width=8,
            bootstyle=ttk.SUCCESS,
        )
        submit_btn.pack(side=tk.RIGHT, padx=5)

        cancel_btn = ttk.Button(
            master=submit_row,
            text="Cancel",
            command=lambda: self.destroy(),
            width=8,
            bootstyle=ttk.DANGER,
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

    def create_torrent_page(self, notebook):
        """Create Torrent page"""
        torrent_page = notebook.nametowidget(notebook.tabs()[1])

        torrent_row = ttk.Frame(torrent_page)
        torrent_row.pack(fill=tk.X, expand=tk.YES)

        torrent_lbl = ttk.Label(torrent_row, text="Torrent", width=8)
        torrent_lbl.pack(side=tk.LEFT, padx=(15, 0))
        torrent_ent = ttk.Entry(
            torrent_row,
            bootstyle=ttk.WARNING,
        )
        torrent_ent.configure(state="readonly")
        torrent_ent.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=tk.YES,
            padx=5,
            pady=5,
            ipady=30,
        )

        # header and labelframe option container
        option_lf = ttk.Labelframe(torrent_page, text="File Download Options")
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

        checkbox = ttk.Checkbutton(
            rename_row,
            variable=self.checkbox_var,
            command=lambda: self.on_checkbox_click(
                self.checkbox_var,
                self.rename_ent,
            ),
            bootstyle=ttk.WARNING,
        )
        checkbox.pack(side=tk.LEFT, padx=(15, 0))

        rename_lbl = ttk.Label(rename_row, text="Rename:", width=8)
        rename_lbl.pack(side=tk.LEFT, padx=(15, 0))
        self.rename_ent = ttk.Entry(
            rename_row,
            textvariable=self.rename_var,
            bootstyle=ttk.WARNING,
        )
        self.rename_ent.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=5)
        self.rename_ent.configure(state=tk.DISABLED)

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
        submit_row = ttk.Frame(torrent_page)
        submit_row.pack(fill=tk.X, expand=tk.YES, pady=(20, 0))

        submit_btn = ttk.Button(
            master=submit_row,
            text="Submit",
            command=lambda: self.submit(),
            width=8,
            bootstyle=ttk.SUCCESS,
        )
        submit_btn.pack(side=tk.RIGHT, padx=5)

        cancel_btn = ttk.Button(
            master=submit_row,
            text="Cancel",
            command=lambda: self.destroy(),
            width=8,
            bootstyle=ttk.DANGER,
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

    def create_schedule_page(self, notebook):
        """Create Schedule page"""
        schedule_page = notebook.nametowidget(notebook.tabs()[2])
        schedule_row = ttk.Frame(schedule_page)
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

    def submit(self):
        """Callback for submit button"""
        uris = self.parse_lines_to_stringvars()
        dpath = pathlib.Path(self.path_var.get())

        self.callback(uris, dpath)

        # self.destroy()
        # return uris, dpath

    def on_checkbox_click(self, checkbox_var, entry_box):
        if checkbox_var.get():
            entry_box.config(state=tk.NORMAL)
        else:
            entry_box.config(state=tk.DISABLED)


if __name__ == '__main__':
    root = ttk.Window(themename="darkly", position=(900, 100))
    app = AddWindow(root)
    root.mainloop()