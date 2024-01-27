## Tkinter widgets (practice)

from tkinter import *
from tkinter.ttk import *

window = Tk()
frame_style = Style()
frame_style.configure("TFrame", background="green", borderwidth=5, relief="sunken")
Frame(width=200, height=200, style="TFrame").grid()

if __name__ == "__main__":
    window.mainloop()
