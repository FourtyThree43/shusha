#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.geometry("300x300+25+25")
s = ttk.Style()
s.theme_use("classic")
s.configure("TButton", relief="raised")

lframe = ttk.LabelFrame(text="Important controls", height=100, width=200, borderwidth=1)
panic = ttk.Button(lframe, text="PANIC!")
relax = ttk.Button(lframe, text="Relax.")
lframe.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
panic.pack(side=tk.LEFT, pady=3, padx=3, expand=True)
relax.pack(side=tk.LEFT, pady=3, padx=3, expand=True)

root.mainloop()
