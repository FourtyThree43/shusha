from tkinter import *
from tkinter import ttk, messagebox

root = Tk()
ttk.Entry(root).grid()

n = ttk.Notebook(root)
f1 = ttk.Frame(n)  # first page, which would get widgets gridded into it
f2 = ttk.Frame(n)  # second page
n.add(f1, text='One')
n.add(f2, text='Two')

m = Menu(root)
m_edit = Menu(m)
m.add_cascade(menu=m_edit, label="Edit")
m_edit.add_command(
    label="Paste",
    command=lambda: root.focus_get().event_generate("<<Paste>>"))
m_edit.add_command(label="Find...",
                   command=lambda: root.event_generate("<<OpenFindDialog>>"))
m_edit.entryconfigure('Paste', accelerator='Command+V')
m_edit.entryconfigure("Find...", accelerator="Command+F")
# m.add_command(label='Path Browser', underline=5)

root['menu'] = m

win = Toplevel(root)
menubar = Menu(win)
# appmenu = Menu(menubar, name='apple')
# menubar.add_cascade(menu=appmenu)
# appmenu.add_command(label='About My Application')
# appmenu.add_separator()

sysmenu = Menu(menubar, name='system')
menubar.add_cascade(menu=sysmenu)
sysmenu.add_command(label='System in')
sysmenu.add_separator()

win['menu'] = menubar


def launchPaste(*args):
    messagebox.showinfo(title='Paste', message="paste somthing")


def launchFindDialog(*args):
    messagebox.showinfo(message="I hope you find what you're looking for!")


root.bind("<<Paste>>", launchPaste)
root.bind("<<OpenFindDialog>>", launchFindDialog)
root.mainloop()
