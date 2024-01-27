#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showinfo

# create the root window
root = tk.Tk()
root.title("Listbox")
root.geometry("400x200+20+20")
root.config(bg="wheat")

# ttk.Style().theme_use("classic")

# create a list box
langs = ("Java", "C#", "C", "C++", "Python", "Go", "JavaScript", "PHP", "Swift")

var = tk.Variable(value=langs)

pw = ttk.PanedWindow(orient=tk.HORIZONTAL)
listbox1 = tk.Listbox(pw, listvariable=var, height=6, selectmode=tk.EXTENDED)
listbox2 = tk.Listbox(pw, listvariable=var, height=6, selectmode=tk.EXTENDED)
pw.add(listbox1, weight=1)
pw.add(listbox2, weight=2)

pw.pack(fill=tk.BOTH, expand=True)
# listbox1.pack(side=tk.LEFT)
# listbox2.pack(side=tk.LEFT)


def items_selected(_):
    pass


listbox1.bind("<<ListboxSelect>>", items_selected)

root.mainloop()
