#!/usr/bin/env python3
from tkinter import *
from tkinter import ttk


class MainW(ttk.Notebook):
    def __init__(self, root: Tk = Tk()):
        super().__init__(root)
        self.root = root
        self.style = ttk.Style(root)

    def run(self):
        self.root.mainloop()


class Downloads(ttk.Panedwindow):
    def __init__(self, master=MainW()) -> None:
        super().__init__(mas)
