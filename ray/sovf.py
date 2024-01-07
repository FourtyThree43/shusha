#!/usr/bin/env python3
import tkinter as tk

root = tk.Tk()
root.geometry("500x500+25+25")
root.config(bg="Teal")
frame1 = tk.Frame(height=300, width=300, bg="RED", borderwidth=1)
# frame2 = tk.Frame(frame1, height=100, width=100, bg="WHITE", borderwidth=0)
# label = tk.Label(frame2, text="Label")  # Receive a callback from button here
# label.pack()
frame1.pack()
button = tk.Button(frame1, text="Button").pack()  # Send some action to Label here
# frame2.pack()
# button.pack()
tk.PhotoImage()
tk.mainloop()
