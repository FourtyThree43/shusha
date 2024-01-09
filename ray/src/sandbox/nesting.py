import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.lift
root.geometry("500x500+25+25")
root.config(bg="teal")

frame = tk.Frame(bg="red", width=300, height=300)
subframe = tk.Frame(frame, bg="green", width=200, height=200)
# label = tk.Label(frame, text="Hello")
# sublabel = tk.Label(subframe, text="World")
# frame.pack_propagate(False)
frame.pack(expand=True, padx=100, pady=100)
subframe.pack(padx=50, pady=50)
# label.pack()
# sublabel.pack()

root.mainloop()
