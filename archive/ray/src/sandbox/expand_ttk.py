import tkinter as tk
from tkinter import ttk

win = tk.Tk()
win.geometry("960x540+50+50")

style = ttk.Style()
style.configure("frame1.TFrame", background="cyan")
style.configure("frame2.TFrame", background="orange")
style.configure("label.TLabel", background="orange")

frame1 = ttk.Frame(win, height=360, width=640, style="frame1.TFrame")
frame2 = ttk.Frame(frame1, height=240, width=320, style="frame2.TFrame")
label = ttk.Label(frame2, text="Hello World", style="label.TLabel")

frame1.pack_propagate(False)
frame2.pack_propagate(False)

frame1.pack(expand=True)
frame2.pack(expand=True)
label.pack(expand=True)

win.mainloop()
