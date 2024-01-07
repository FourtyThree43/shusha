from tkinter import *
from tkinter.messagebox import showinfo
from tkinter.ttk import *


def login():
    msg = f"You entered name: {name.get()} and password: {passwd.get()}"
    showinfo(title="Credentials", message=msg)


window = Tk()
width, height = window.winfo_screenheight(), window.winfo_screenwidth()
window.geometry("320x240")
window.resizable(False, False)
window.eval("tk::PlaceWindow . center")
window.title("Sign In")

sign_in = Frame()
name_label = Label(sign_in, text="Enter name:")
name, passwd = StringVar(), StringVar()
name_field = Entry(sign_in, textvariable=name)
name_field.focus()
passwd_label = Label(sign_in, text="Enter password:")
passwd_field = Entry(sign_in, textvariable=passwd, show="*")
login_button = Button(sign_in, text="Log in", command=login)

elements = (sign_in, name_label, name_field, passwd_label, passwd_field, login_button)
for elem in elements:
    elem.pack(fill=BOTH, padx=5, pady=5)


if __name__ == "__main__":
    window.mainloop()
