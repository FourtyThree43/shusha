#!/usr/bin/env python
import tkinter as tk
from tkinter import ttk


root = tk.Tk()
root.geometry("400x300+20+20")
root.resizable(False, False)

textbox = tk.Text(height=8)
scrollbar = ttk.Scrollbar(orient="vertical", command=textbox.yview)
textbox.config(yscrollcommand=scrollbar.set)

for i in range(1, 20):
    textbox.insert(f"{i}.0", f"Line {i}.")
