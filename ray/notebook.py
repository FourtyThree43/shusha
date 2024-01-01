#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk


root = tk.Tk()
root.geometry("640x480+50+50")

notebook = ttk.Notebook()
downloads = ttk.PanedWindow(notebook, orient=tk.HORIZONTAL)
add_downloads = ttk.Frame(notebook)
notebook.add(downloads, text="DOWNLOADS")
notebook.add(add_downloads, text="ADD DOWNLOADS")

sidebar = ttk.Frame(downloads, borderwidth=1, width=250)

dt_cols = ("#", "name", "size", "progress", "status", "down_speed")
d_tree = ttk.Treeview(downloads, columns=dt_cols, show="headings")
for h in dt_cols:
    d_tree.heading(h, text=h.replace("_", " ").title())


downloads.add(sidebar)
downloads.add(d_tree)


notebook.pack(fill=tk.BOTH, expand=True)
root.mainloop()
