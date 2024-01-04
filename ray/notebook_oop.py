from tkinter import *
from tkinter import ttk


class DownloadManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("640x480+50+50")
        self.root.title("Download Manager")

        # Initialize styles
        self.style = ttk.Style()
        self.style.configure("add.TFrame", background="wheat")
        self.style.configure("TNotebook", background="gray")

        # Create main notebook
        self.notebook = ttk.Notebook(root)
        self.downloads_tab = self.create_downloads_tab()
        self.add_downloads_tab = self.create_add_downloads_tab()

        # Add tabs to notebook
        self.notebook.add(self.downloads_tab, text="DOWNLOADS")
        self.notebook.add(self.add_downloads_tab, text="ADD DOWNLOADS")

        # Pack and start the main loop
        self.notebook.pack(fill=BOTH, expand=True)
        root.mainloop()

    def create_downloads_tab(self):
        downloads_tab = ttk.Frame(self.notebook)

        # Create and configure PanedWindow for downloads
        downloads_paned = ttk.Panedwindow(downloads_tab, orient=HORIZONTAL)
        sidebar = self.create_sidebar(downloads_paned)
        d_tree_frame = self.create_d_tree_frame(downloads_paned)

        # Add frames to PanedWindow
        downloads_paned.add(sidebar)
        downloads_paned.add(d_tree_frame)

        # Add PanedWindow to the downloads tab
        downloads_paned.pack(expand=True, fill=BOTH)

        return downloads_tab

    def create_sidebar(self, parent):
        sidebar = ttk.Frame(parent, borderwidth=0, width=200)

        # Create and configure Treeview for sidebar
        side_tree = ttk.Treeview(sidebar)
        type_node = side_tree.insert("", END, text="Type")
        side_tree.insert(type_node, END, text="All")
        side_tree.insert(type_node, END, text="Direct Download")
        side_tree.insert(type_node, END, text="Bittorrent")

        state_node = side_tree.insert("", END, text="State")
        side_tree.insert(state_node, END, text="All")
        side_tree.insert(state_node, END, text="Downloading")
        side_tree.insert(state_node, END, text="Completed")

        # Pack and return the sidebar
        side_tree.pack(expand=True, fill=BOTH)
        return sidebar

    def create_d_tree_frame(self, parent):
        d_tree_frame = ttk.Frame(parent, borderwidth=0, style="add.TFrame", width=400)

        # Create and configure Treeview for download information
        dt_cols = ("#", "name", "size", "progress", "status", "down_speed")
        d_tree = ttk.Treeview(d_tree_frame, columns=dt_cols, show="headings", height=10)

        for c in dt_cols:
            d_tree.heading(c, text=c.replace("_", " ").title())
            d_tree.column(c, stretch=False)
        d_tree.column("#", width=50)

        # Add horizontal and vertical scrollbars
        dt_hscrollbar = ttk.Scrollbar(
            d_tree_frame, orient=HORIZONTAL, command=d_tree.xview
        )
        dt_vscrollbar = ttk.Scrollbar(
            d_tree_frame, orient=VERTICAL, command=d_tree.yview
        )
        d_tree.configure(
            xscrollcommand=dt_hscrollbar.set, yscrollcommand=dt_vscrollbar.set
        )

        # Pack the components
        dt_hscrollbar.pack(fill=X, side=BOTTOM)
        dt_vscrollbar.pack(fill=Y, side=RIGHT)
        d_tree.pack(expand=True, fill=BOTH)

        return d_tree_frame

    def create_add_downloads_tab(self):
        # You can implement the creation of the "ADD DOWNLOADS" tab here
        # if you have specific widgets or functionality for that tab.
        return ttk.Frame(self.notebook)


# Instantiate the Tkinter root window and the application
root = Tk()
app = DownloadManagerApp(root)
