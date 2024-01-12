import ttkbootstrap as ttk
import tkinter as tk
from tkinter.messagebox import showinfo


# root window
root = ttk.Window(themename="darkly")
root.geometry("300x120")
root.title("Progressbar Demo")
value = tk.StringVar()


def update_progress_label():
    return f"Current Progress: {pb['value']}%"


def progress():
    if pb["value"] < 100:
        pb["value"] += 20
        value.set(update_progress_label())
    else:
        showinfo(message="The progress completed!")


def stop():
    pb.stop()
    value.set(update_progress_label())


# progressbar
pb = ttk.Progressbar(root, orient="horizontal", mode="determinate", length=280)
# place the progressbar
pb.grid(column=0, row=0, columnspan=2, padx=10, pady=20)

# label
value.set(update_progress_label())
value_label = ttk.Label(root, textvariable=value)
value_label.grid(column=0, row=1, columnspan=2)

# start button
start_button = ttk.Button(root, text="Progress", command=progress)
start_button.grid(column=0, row=2, padx=10, pady=10, sticky=tk.E)

stop_button = ttk.Button(root, text="Stop", command=stop)
stop_button.grid(column=1, row=2, padx=10, pady=10, sticky=tk.W)


root.mainloop()
