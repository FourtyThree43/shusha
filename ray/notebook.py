#!/usr/bin/env python3
"""
Module
"""
from tkinter import *
from tkinter import ttk

# Initialise main window
root = Tk()
root.geometry("640x480+50+50")

# Define styles
style = ttk.Style()
style.configure("add.TFrame", background="wheat")
style.configure("TNotebook", background="gray")

# Create widgets
notebook = ttk.Notebook()
downloads = ttk.Panedwindow(notebook, orient=HORIZONTAL)
add_downloads = ttk.Frame(notebook)

## downloads tab frames
sidebar = ttk.Frame(downloads, borderwidth=0, width=200)
d_tree_frame = ttk.Frame(downloads, borderwidth=0, style="add.TFrame", width=400)

### sidebar treeview
side_tree = ttk.Treeview(sidebar)
type = side_tree.insert("", END, text="Type")
side_tree.insert(type, END, text="All")
side_tree.insert(type, END, text="Direct Download")
side_tree.insert(type, END, text="Bittorrent")

state = side_tree.insert("", END, text="State")
side_tree.insert(state, END, text="All")
side_tree.insert(state, END, text="Downloading")
side_tree.insert(state, END, text="Completed")

### d_tree_frame treeview
dt_cols = ("#", "name", "size", "progress", "status", "down_speed")
d_tree = ttk.Treeview(d_tree_frame, columns=dt_cols, show="headings", height=10)

for c in dt_cols:
    d_tree.heading(c, text=c.replace("_", " ").title())
    d_tree.column(c, stretch=False)
d_tree.column("#", width=50)
# print("#0:", d_tree.column("#0"))

## Add scrollbar
dt_hscrollbar = ttk.Scrollbar(d_tree_frame, orient=HORIZONTAL, command=d_tree.xview)
dt_vscrollbar = ttk.Scrollbar(d_tree_frame, orient=VERTICAL, command=d_tree.yview)
d_tree.configure(xscrollcommand=dt_hscrollbar.set)
d_tree.configure(yscrollcommand=dt_vscrollbar.set)

# Position widgets
side_tree.pack(expand=True, fill=BOTH)
dt_vscrollbar.pack(fill=Y, side=RIGHT)
dt_hscrollbar.pack(fill=X, side=BOTTOM)
d_tree.pack(expand=True, fill=BOTH)

downloads.add(sidebar)
downloads.add(d_tree_frame)

notebook.add(downloads, text="DOWNLOADS")
notebook.add(add_downloads, text="ADD DOWNLOADS")

notebook.pack(fill=BOTH, expand=True)

# Launch window
root.mainloop()
