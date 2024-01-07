#!/usr/bin/env python3

import tkinter as tk

win = tk.Tk()
win.geometry("960x540+50+50")

frame1 = tk.Frame(height=360, width=640, bg="cyan")
frame2 = tk.Frame(frame1, height=240, width=320, bg="orange")
label = tk.Label(frame2, text="Hello World", bg="orange")

frame1.pack_propagate(False)
frame2.pack_propagate(False)

frame1.pack(expand=True)
frame2.pack(expand=True)
label.pack(expand=True)

win.mainloop()
