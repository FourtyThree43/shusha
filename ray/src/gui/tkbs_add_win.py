import pathlib
import tkinter as tk
import ttkbootstrap as ttk
from tkinter.filedialog import askdirectory

class AddWindow(ttk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("File Add")

        # header and labelframe option container
        option_text = "Complete the form to begin your search"
        self.option_lf = ttk.Labelframe(self, text=option_text, padding=15)
        self.option_lf.pack(fill=tk.X, expand=tk.YES, anchor=tk.N)

        # application variables
        _path = pathlib.Path().absolute().as_posix()
        self.path_var = ttk.StringVar(value=_path)

        self.create_path_row()

    def create_path_row(self):
        """Add path row to labelframe"""
        path_row = ttk.Frame(self.option_lf)
        path_row.pack(fill=tk.X, expand=tk.YES)
        path_lbl = ttk.Label(path_row, text="Path", width=8)
        path_lbl.pack(side=tk.LEFT, padx=(15, 0))
        path_ent = ttk.Entry(path_row, textvariable=self.path_var)
        path_ent.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=5)
        browse_btn = ttk.Button(
            master=path_row,
            text="Browse",
            command=self.on_browse,
            width=8
        )
        browse_btn.pack(side=tk.LEFT, padx=5)

    def on_browse(self):
        """Callback for directory browse"""
        path = askdirectory(title="Browse directory")
        if path:
            self.path_var.set(path)
