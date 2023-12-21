import tkinter as tk

root = tk.Tk()
frame = tk.Frame(root)
frame.grid(row=0, column=0, sticky="nsew")

# Create a widget in the frame
widget = tk.Label(frame, text="Resizable Widget")
widget.grid(row=0, column=0, sticky="nsew")
widget1 = tk.Label(frame, text="Resizable Widget 2")
widget1.grid(row=0, column=1, sticky="nsew")
# Make the widget resizable
frame.columnconfigure(0, weight=1)
frame.rowconfigure(0, weight=1)

root.mainloop()
