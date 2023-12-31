#!/usr/bin/env python3

import tkinter as tk
from tkinter import StringVar, ttk
from tkinter.messagebox import showerror, showinfo

window = tk.Tk()
window.title("Login")
# window.columnconfigure(0, weight=1)
# window.columnconfigure(1, weight=3)
window.resizable(False, False)
window.geometry("240x100")
name_label = ttk.Label(text="Name:")
passwd_label = ttk.Label(text="Password:")
name, passwd = StringVar(), StringVar()
name_field = ttk.Entry(textvariable=name)
passwd_field = ttk.Entry(textvariable=passwd, show="*")


def login():
    lname, lpasswd = name.get(), passwd.get()
    if lname and lpasswd:
        msg = f"Entered name {lname}, and password {lpasswd}."
        showinfo(title="Credentials", message=msg)
    elif lname:
        showerror(title="Error", message="Missing password")
    else:
        showerror(title="Error", message="Missing name")


login_button = ttk.Button(text="Log in", command=login)

name_field.focus()
name_label.grid(sticky=tk.W, row=0, column=0, padx=5, pady=5)
passwd_label.grid(sticky=tk.W, row=1, column=0, padx=5, pady=5)
name_field.grid(row=0, column=1, padx=5, pady=5)
passwd_field.grid(row=1, column=1, padx=5, pady=5)
login_button.grid(row=2, column=1, padx=5, pady=5)

if __name__ == "__main__":
    window.mainloop()
