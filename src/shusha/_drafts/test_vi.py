from tkinter import ttk
import tkinter as tk


class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Tkinter Notebook Example")
        self.geometry("400x400")
        self.resizable(0, 0)
        self.create_widgets()

    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)
        self.tab3 = ttk.Frame(self.notebook)

        self.notebook.add(self.tab1, text="Tab One")
        self.notebook.add(self.tab2, text="Tab Two")
        self.notebook.add(self.tab3, text="Tab Three")

        self.label1 = ttk.Label(self.tab1, text="This is Tab One")
        self.label1.pack(padx=10, pady=10)

        self.label2 = ttk.Label(self.tab2, text="This is Tab Two")
        self.label2.pack(padx=10, pady=10)

        self.label3 = ttk.Label(self.tab3, text="This is Tab Three")
        self.label3.pack(padx=10, pady=10)

        self.button = ttk.Button(self.tab3,
                                 text="Click Me",
                                 command=self.click_me)
        self.button.pack(padx=10, pady=10)

    def click_me(self):
        self.label3.configure(text="Button was clicked!")


if __name__ == "__main__":
    app = App()
    app.mainloop()
