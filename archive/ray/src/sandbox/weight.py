import tkinter as tk
from tkinter import ttk

window = tk.Tk()
window.geometry("400x400+20+20")
window.columnconfigure((0, 1), weight=1)
window.rowconfigure(0, weight=1)
style = ttk.Style()
style.configure("TFrame", background="cyan")
style.configure("f2.TFrame", background="orange")
f1 = ttk.Frame()
f2 = ttk.Frame(style="f2.TFrame")
f1.grid(row=0, column=0, sticky="nsew")
f2.grid(row=0, column=1, sticky="nsew")

window.mainloop()
