import datetime
import tkinter as tk
from pathlib import Path

import ttkbootstrap as ttk
from tkbs_add_win import AddWindow
from ttkbootstrap.tableview import Tableview
from ttkbootstrap.toast import ToastNotification
from ttkbootstrap.tooltip import ToolTip

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path("assets/frame0")


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)


class MyApp(ttk.Frame):

    def __init__(self, master):
        super().__init__(master, padding=10)
        self.pack(fill=tk.BOTH, expand=tk.YES)

        self.colors = ttk.Style().colors

        image_files = {
            'add-download': 'icons8-add-64.png',
            'start-download': 'icons8-circled-play-64.png',
            'pause-download': 'icons8-pause-button-64.png',
            'refresh': 'icons8-refresh-64.png',
            'move-up': 'icons8-arrow-64.png',
            'move-down': 'icons8-scroll-down-64.png',
            'remove-download': 'icons8-remove-64.png',
            'logs': 'icons8-log-64.png',
            'settings': 'icons8-slider_2-64.png',
            'start-queue-': 'icons8-circled-play-64.png',
            'pause-queue': 'icons8-pause-button-64.png',
            'clear-queue': 'icons8-clear-64.png',
            'queue-settings': 'icons8-slider-64.png',
        }

        self.photoimages = []
        for key, val in image_files.items():
            _path = relative_to_assets(val)
            self.photoimages.append(ttk.PhotoImage(name=key, file=_path))

        self.create_buttonbar()
        self.create_table_view()
        self.create_bottom_bar()
        # self.show_toast()
        self.file_add = AddWindow(self.master)

    def create_buttonbar(self):
        # top buttonbar
        # header and labelframe buttonbar container
        self.buttonbar = ttk.Labelframe(self, text="Actions")
        self.buttonbar.pack(fill=tk.X, expand=tk.YES, anchor=tk.N)

        opts_row = ttk.Frame(self.buttonbar)
        opts_row.pack(fill=tk.X, expand=tk.YES)

        add_btn = ttk.Button(master=opts_row,
                             text="Add",
                             image='add-download',
                             command=lambda: self.show_toast(),
                             width=8,
                             bootstyle="outline-dark")
        add_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(add_btn,
                text="Add new download",
                bootstyle=(ttk.WARNING, ttk.INVERSE))

        start_btn = ttk.Button(master=opts_row,
                               text="Start",
                               image='start-download',
                               command=lambda: print("start downloads"),
                               width=8,
                               bootstyle="outline-dark")
        start_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(start_btn,
                text="Start downloads",
                bootstyle=(ttk.WARNING, ttk.INVERSE))

        pause_btn = ttk.Button(master=opts_row,
                               text="Pause",
                               image='pause-download',
                               command=lambda: print("pause downloads"),
                               width=8,
                               bootstyle="outline-dark")
        pause_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(pause_btn,
                text="Pause downloads",
                bootstyle=(ttk.WARNING, ttk.INVERSE))

        refresh_btn = ttk.Button(
            master=opts_row,
            text="Refresh",
            image='refresh',
            command=lambda: print("Refresh downloads list"),
            width=8,
            bootstyle="outline-dark")
        refresh_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(refresh_btn,
                text="Refresh downloads list",
                bootstyle=(ttk.WARNING, ttk.INVERSE))

        mvup_btn = ttk.Button(master=opts_row,
                              text="Move Up",
                              image='move-up',
                              command=lambda: print("Move UP"),
                              width=8,
                              bootstyle="outline-dark")
        mvup_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(mvup_btn,
                text="Move download up",
                bootstyle=(ttk.WARNING, ttk.INVERSE))

        mvdown_btn = ttk.Button(master=opts_row,
                                text="Move Down",
                                image='move-down',
                                command=lambda: print("Move Down"),
                                width=8,
                                bootstyle="outline-dark")
        mvdown_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(mvdown_btn,
                text="Move download down",
                bootstyle=(ttk.WARNING, ttk.INVERSE))

        rem_btn = ttk.Button(master=opts_row,
                             text="Remove",
                             image='remove-download',
                             command=lambda: print("Remove downloads"),
                             width=8,
                             bootstyle="outline-dark")
        rem_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(rem_btn,
                text="Remove downloads",
                bootstyle=(ttk.DANGER, ttk.INVERSE))

        sett_btn = ttk.Button(master=opts_row,
                              text="Settings",
                              image='settings',
                              command=lambda: print("Open Settings"),
                              width=8,
                              bootstyle="outline-dark")
        sett_btn.pack(side=tk.RIGHT, padx=(0, 1), pady=1)
        ToolTip(sett_btn,
                text="Open settings",
                bootstyle=(ttk.WARNING, ttk.INVERSE))

        logs_btn = ttk.Button(master=opts_row,
                              text="Logs",
                              image='logs',
                              command=lambda: print("Open Logs"),
                              width=8,
                              bootstyle="outline-dark")
        logs_btn.pack(side=tk.RIGHT, padx=(0, 1), pady=1)
        ToolTip(logs_btn,
                text="Open logs",
                bootstyle=(ttk.WARNING, ttk.INVERSE))

    def create_table_view(self):
        self.table_lf = ttk.Labelframe(self, text="Downloads List")
        self.table_lf.pack(fill=tk.BOTH, expand=tk.YES, side=tk.TOP)

        _columns = [
            "Filename", "Status", "Size", "Progress", "Speed", "ETA", "Date",
            "Note"
        ]

        _rowdata = []
        # add items to download_list
        for i in range(1, 15):
            for j in range(2, 10):
                x = j + i
                y = x + 2
                _rowdata.append([
                    "Lorem Ipsum dolor sit amet", "Downloading",
                    f"{i}{x}{j} MB", f"{y}.2{i}%", f"{x}{i}{y}.{j}{i} KB/s",
                    f"{j}.13m", f"{datetime.date.today().ctime()}"
                ])

        self.dt = Tableview(master=self.table_lf,
                            coldata=_columns,
                            rowdata=_rowdata,
                            paginated=True,
                            searchable=True,
                            bootstyle="warning",
                            stripecolor=(self.colors.dark, None))
        self.dt.pack(fill=tk.BOTH, expand=tk.YES, padx=10)

    def create_bottom_bar(self):
        # bottom buttonbar
        # header and labelframe buttonbar container
        self.bottom_bar = ttk.Labelframe(self, text="Queue Actions")
        self.bottom_bar.pack(fill=tk.X, expand=tk.YES, anchor=tk.S)

        opts_row = ttk.Frame(self.bottom_bar)
        opts_row.pack(fill=tk.X, expand=tk.YES)

        category = ttk.Combobox(master=opts_row,
                                values=["Category 1", "Category 2"],
                                width=12)
        category.pack(side=ttk.LEFT, padx=10, pady=1)
        ToolTip(category,
                text="Select category",
                bootstyle=(ttk.WARNING, ttk.INVERSE))

        start_btn = ttk.Button(master=opts_row,
                               text="Start",
                               image='start-queue-',
                               command=lambda: print("start queue"),
                               width=8,
                               bootstyle="outline-dark")
        start_btn.pack(side=ttk.LEFT, padx=(1, 0), pady=1)
        ToolTip(start_btn,
                text="Start queue",
                bootstyle=(ttk.WARNING, ttk.INVERSE))

        pause_btn = ttk.Button(master=opts_row,
                               text="Pause",
                               image='pause-queue',
                               command=lambda: print("pause queue"),
                               width=8,
                               bootstyle="outline-dark")
        pause_btn.pack(side=ttk.LEFT, padx=(1, 0), pady=1)
        ToolTip(pause_btn,
                text="Pause queue",
                bootstyle=(ttk.WARNING, ttk.INVERSE))

        refresh_btn = ttk.Button(master=opts_row,
                                 text="Clear",
                                 image='clear-queue',
                                 command=lambda: print("clear queue list"),
                                 width=8,
                                 bootstyle="outline-dark")
        refresh_btn.pack(side=ttk.LEFT, padx=(1, 0), pady=1)
        ToolTip(refresh_btn,
                text="Clear queue list",
                bootstyle=(ttk.DANGER, ttk.INVERSE))

        sett_btn = ttk.Button(master=opts_row,
                              text="Queue Settings",
                              image='queue-settings',
                              command=lambda: print("Open Queue Settings"),
                              width=8,
                              bootstyle="outline-dark")
        sett_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(sett_btn,
                text="Open queue settings",
                bootstyle=(ttk.WARNING, ttk.INVERSE))

    def show_toast(self):
        toast = ToastNotification(
            title="ttkbootstrap toast message",
            message="This is a toast message",
            duration=3000,
        )

        toast.show_toast()


if __name__ == '__main__':
    app = ttk.Window(title="App",
                     themename="darkly",
                     size=(1270, 550),
                     resizable=(0, 0),
                     position=(10, 140))
    MyApp(app)
    app.mainloop()
