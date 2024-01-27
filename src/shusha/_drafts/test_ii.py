import tkinter as tk
from tkinter import ttk


class DownloadManagerApp:

    def __init__(self, root):
        self.root = root
        self.root.geometry("540x540+664+580")
        self.root.minsize(1050, 480)
        self.root.maxsize(1920, 1080)
        self.root.resizable(1, 1)
        self.root.title("Download Manager")

        # Top Menu Bar
        self.menu_bar = tk.Menu(root)
        root.config(menu=self.menu_bar)

        menu_options = ["File", "Edit", "View", "Queue", "Options", "Help"]
        for option in menu_options:
            menu = tk.Menu(self.menu_bar, tearoff=0)
            menu.add_command(label=option)
            self.menu_bar.add_cascade(label=option, menu=menu)

        # Task Actions Bar
        self.task_actions_bar = tk.Frame(root)
        self.task_actions_bar.pack(side="top", fill="x")

        action_buttons = [
            "Add URL", "Add Torrent", "Refresh Task List", "Start All",
            "Resume All", "Pause All", "Purge Completed"
        ]
        for action in action_buttons:
            button = tk.Button(self.task_actions_bar,
                               text=action,
                               padx=10,
                               pady=5)
            button.pack(side="left", padx=5)

        # Left Pane
        self.left_pane = ttk.PanedWindow(root, orient="vertical")
        self.left_pane.pack(side="left", fill="y", expand=True)

        # Treeview for Category List
        category_tree = ttk.Treeview(self.left_pane,
                                     columns=("Category"),
                                     show="tree headings")

        category_tree.heading("#0", text="Category")
        category_tree.insert("", "end", text="ALL")
        category_tree.insert("", "end", text="Downloading")
        category_tree.insert("", "end", text="Waiting")
        category_tree.insert("", "end", text="Stopped")
        self.left_pane.add(category_tree)

        # Resizable Border for Left Pane
        sizegrip_left = ttk.Sizegrip(self.left_pane)
        self.left_pane.add(sizegrip_left)

        # Center Pane
        self.center_pane = ttk.PanedWindow(root, orient="vertical")
        self.center_pane.pack(side="left", fill="y", expand=True)

        # Treeview for Download List
        download_tree = ttk.Treeview(self.center_pane,
                                     columns=("GID", "Status", "Progress",
                                              "Action"))
        download_tree.heading("#0", text="Downloads")
        download_tree.heading("#1", text="GID")
        download_tree.heading("#2", text="Status")
        download_tree.heading("#3", text="Progress")
        download_tree.heading("#4", text="Action")
        self.center_pane.add(download_tree)

        # Resizable Border for Center Pane
        sizegrip_center = ttk.Sizegrip(self.center_pane)
        self.center_pane.add(sizegrip_center)

        # Bottom Pane
        self.bottom_pane = ttk.PanedWindow(root, orient="horizontal")
        self.bottom_pane.pack(side="bottom", fill="x")

        # Status Bar
        status_bar = tk.Label(self.bottom_pane, text="Status Bar")
        status_bar.pack(side="bottom", fill="x")

        # Stats
        stats_label = tk.Label(self.bottom_pane,
                               text="Active | D & U speeds | Speed Limiter")
        stats_label.pack(side="bottom", fill="x")

        # Resizable Border for Bottom Pane
        # sizegrip_bottom = ttk.Sizegrip(self.bottom_pane)
        # self.bottom_pane.add(sizegrip_bottom)

        # Window Close Event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = DownloadManagerApp(root)
    root.mainloop()
