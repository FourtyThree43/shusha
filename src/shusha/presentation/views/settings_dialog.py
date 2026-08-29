"""
Settings and Preferences Dialog for Shusha 2.
Multi-tab configuration: General, Connection, Downloads, Categories.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from typing import ClassVar

import ttkbootstrap as tb

from shusha.application.use_cases.category_use_cases import CategoryDTO
from shusha.domain.identifiers import CategoryId
from shusha.infrastructure.configuration.settings_store import AppSettings
from shusha.presentation.app_context import AppContext
from shusha.presentation.components.base import BaseDialog, BaseFrame


class SettingsDialog(BaseDialog):
    """Application preferences and settings modal."""

    THEMES: ClassVar[list[str]] = [
        "darkly",
        "cosmo",
        "flatly",
        "journal",
        "litera",
        "lumen",
        "minty",
        "pulse",
        "sandstone",
        "united",
        "yeti",
        "cyborg",
        "solar",
        "superhero",
    ]

    def __init__(self, parent: tk.Tk | tk.Toplevel, ctx: AppContext) -> None:
        self.ctx = ctx
        self.settings = ctx.settings_store.load_settings()

        super().__init__(
            parent=parent,
            title="Settings — Shusha",
            min_width=650,
            min_height=480,
        )

        self._setup_ui()

    def _setup_ui(self) -> None:
        main_frame = BaseFrame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        self.notebook = tb.Notebook(main_frame, bootstyle="primary")
        self.notebook.pack(fill="both", expand=True, pady=(0, 10))

        # 1. General Tab
        tab_gen = BaseFrame(self.notebook, padding=12)
        self.notebook.add(tab_gen, text="General")
        self._setup_general_tab(tab_gen)

        # 2. Connection Tab
        tab_conn = BaseFrame(self.notebook, padding=12)
        self.notebook.add(tab_conn, text="Daemon & RPC")
        self._setup_connection_tab(tab_conn)

        # 3. Downloads Tab
        tab_dl = BaseFrame(self.notebook, padding=12)
        self.notebook.add(tab_dl, text="Downloads & Limits")
        self._setup_downloads_tab(tab_dl)

        # 4. Categories Tab
        tab_cat = BaseFrame(self.notebook, padding=12)
        self.notebook.add(tab_cat, text="Categories")
        self._setup_categories_tab(tab_cat)

        # Action Buttons
        btn_box = BaseFrame(main_frame)
        btn_box.pack(fill="x")

        btn_save = tb.Button(
            btn_box,
            text="Save Settings",
            bootstyle="success",
            command=self._on_save,
        )
        btn_save.pack(side="right", padx=(4, 0))

        btn_cancel = tb.Button(
            btn_box,
            text="Cancel",
            bootstyle="secondary-outline",
            command=self.destroy,
        )
        btn_cancel.pack(side="right")

    def _setup_general_tab(self, parent: BaseFrame) -> None:
        parent.columnconfigure(1, weight=1)

        # Theme selection
        lbl_theme = tb.Label(parent, text="UI Theme:")
        lbl_theme.grid(row=0, column=0, sticky="w", pady=6)

        self.cmb_theme = tb.Combobox(parent, values=self.THEMES, state="readonly")
        cur_theme = (
            self.settings.theme if self.settings.theme in self.THEMES else "darkly"
        )
        self.cmb_theme.set(cur_theme)
        self.cmb_theme.grid(row=0, column=1, sticky="w", padx=6, pady=6)

        # Checkboxes
        self.var_clipboard = tk.BooleanVar(value=self.settings.clipboard_watch)
        chk_clip = tb.Checkbutton(
            parent,
            text="Monitor clipboard for downloadable links",
            variable=self.var_clipboard,
            bootstyle="round-toggle",
        )
        chk_clip.grid(row=1, column=0, columnspan=2, sticky="w", pady=6)

        self.var_sound = tk.BooleanVar(value=self.settings.sound_notifications)
        chk_sound = tb.Checkbutton(
            parent,
            text="Play audio cues on download completion",
            variable=self.var_sound,
            bootstyle="round-toggle",
        )
        chk_sound.grid(row=2, column=0, columnspan=2, sticky="w", pady=6)

        self.var_tray = tk.BooleanVar(value=self.settings.close_to_tray)
        chk_tray = tb.Checkbutton(
            parent,
            text="Minimize to system tray on close",
            variable=self.var_tray,
            bootstyle="round-toggle",
        )
        chk_tray.grid(row=3, column=0, columnspan=2, sticky="w", pady=6)

    def _setup_connection_tab(self, parent: BaseFrame) -> None:
        parent.columnconfigure(1, weight=1)

        self.var_autostart = tk.BooleanVar(value=self.settings.auto_start_daemon)
        chk_auto = tb.Checkbutton(
            parent,
            text="Automatically start and manage local aria2c daemon",
            variable=self.var_autostart,
            bootstyle="round-toggle",
        )
        chk_auto.grid(row=0, column=0, columnspan=3, sticky="w", pady=6)

        lbl_host = tb.Label(parent, text="RPC Host:")
        lbl_host.grid(row=1, column=0, sticky="w", pady=4)
        self.txt_host = tb.Entry(parent)
        self.txt_host.insert(0, self.settings.aria2_host)
        self.txt_host.grid(row=1, column=1, sticky="ew", padx=6, pady=4)

        lbl_port = tb.Label(parent, text="RPC Port:")
        lbl_port.grid(row=2, column=0, sticky="w", pady=4)
        self.txt_port = tb.Entry(parent)
        self.txt_port.insert(0, str(self.settings.aria2_port))
        self.txt_port.grid(row=2, column=1, sticky="w", padx=6, pady=4)

        lbl_exe = tb.Label(parent, text="aria2c Executable:")
        lbl_exe.grid(row=3, column=0, sticky="w", pady=4)
        self.txt_exe = tb.Entry(parent)
        if self.settings.custom_aria2_path:
            self.txt_exe.insert(0, self.settings.custom_aria2_path)
        self.txt_exe.grid(row=3, column=1, sticky="ew", padx=6, pady=4)

        btn_browse_exe = tb.Button(
            parent,
            text="Browse...",
            bootstyle="secondary",
            command=self._on_browse_exe,
        )
        btn_browse_exe.grid(row=3, column=2, pady=4)

    def _setup_downloads_tab(self, parent: BaseFrame) -> None:
        parent.columnconfigure(1, weight=1)

        lbl_dir = tb.Label(parent, text="Default Download Folder:")
        lbl_dir.grid(row=0, column=0, sticky="w", pady=4)
        self.txt_dir = tb.Entry(parent)
        self.txt_dir.insert(0, self.settings.download_dir)
        self.txt_dir.grid(row=0, column=1, sticky="ew", padx=6, pady=4)

        btn_browse_dir = tb.Button(
            parent,
            text="Browse...",
            bootstyle="secondary",
            command=self._on_browse_dir,
        )
        btn_browse_dir.grid(row=0, column=2, pady=4)

        lbl_max_act = tb.Label(parent, text="Max Concurrent Downloads:")
        lbl_max_act.grid(row=1, column=0, sticky="w", pady=4)
        self.txt_max_act = tb.Entry(parent, width=10)
        self.txt_max_act.insert(0, str(self.settings.max_active_downloads))
        self.txt_max_act.grid(row=1, column=1, sticky="w", padx=6, pady=4)

        lbl_dl_limit = tb.Label(parent, text="Download Speed Limit (0=unlimited):")
        lbl_dl_limit.grid(row=2, column=0, sticky="w", pady=4)
        self.txt_dl_limit = tb.Entry(parent, width=10)
        self.txt_dl_limit.insert(0, str(self.settings.speed_limit_download))
        self.txt_dl_limit.grid(row=2, column=1, sticky="w", padx=6, pady=4)

        lbl_ul_limit = tb.Label(parent, text="Upload Speed Limit (0=unlimited):")
        lbl_ul_limit.grid(row=3, column=0, sticky="w", pady=4)
        self.txt_ul_limit = tb.Entry(parent, width=10)
        self.txt_ul_limit.insert(0, str(self.settings.speed_limit_upload))
        self.txt_ul_limit.grid(row=3, column=1, sticky="w", padx=6, pady=4)

    def _setup_categories_tab(self, parent: BaseFrame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        self.tree_cats = tb.Treeview(
            parent,
            columns=("name", "dir", "exts"),
            show="headings",
            bootstyle="secondary",
        )
        self.tree_cats.heading("name", text="Category")
        self.tree_cats.heading("dir", text="Folder")
        self.tree_cats.heading("exts", text="Extensions")
        self.tree_cats.grid(row=0, column=0, sticky="nsew", pady=(0, 6))

        # Load categories
        self._refresh_categories_tree()

        btn_row = BaseFrame(parent)
        btn_row.grid(row=1, column=0, sticky="w")

        btn_add_cat = tb.Button(
            btn_row,
            text="+ Add Category",
            bootstyle="primary",
            command=self._on_add_category,
        )
        btn_add_cat.pack(side="left", padx=(0, 4))

        btn_del_cat = tb.Button(
            btn_row,
            text="Delete",
            bootstyle="danger-outline",
            command=self._on_delete_category,
        )
        btn_del_cat.pack(side="left")

    def _refresh_categories_tree(self) -> None:
        for child in self.tree_cats.get_children():
            self.tree_cats.delete(child)

        for cat in self.ctx.category_repo.list_all():
            self.tree_cats.insert(
                "",
                "end",
                iid=str(cat.id),
                values=(cat.name, cat.download_dir, ", ".join(cat.rule.extensions)),
            )

    def _on_add_category(self) -> None:
        name = tb.dialogs.Querybox.get_string(
            title="Category Name", prompt="Enter category name:", parent=self
        )
        if name and name.strip():
            exts = tb.dialogs.Querybox.get_string(
                title="File Extensions",
                prompt="Enter comma-separated extensions (e.g. mp4, mkv):",
                parent=self,
            )
            ext_list = [
                e.strip().lstrip(".") for e in (exts or "").split(",") if e.strip()
            ]
            self.ctx.create_category_uc.execute(
                CategoryDTO(
                    name=name.strip(),
                    download_dir=self.txt_dir.get().strip(),
                    extensions=ext_list,
                    host_patterns=[],
                )
            )
            self._refresh_categories_tree()

    def _on_delete_category(self) -> None:
        selected = self.tree_cats.selection()
        if selected:
            cat_id = CategoryId(selected[0])
            self.ctx.delete_category_uc.execute(cat_id)
            self._refresh_categories_tree()

    def _on_browse_exe(self) -> None:
        path = filedialog.askopenfilename(title="Select aria2c Binary", parent=self)
        if path:
            self.txt_exe.delete(0, "end")
            self.txt_exe.insert(0, path)

    def _on_browse_dir(self) -> None:
        path = filedialog.askdirectory(
            title="Select Default Download Folder", parent=self
        )
        if path:
            self.txt_dir.delete(0, "end")
            self.txt_dir.insert(0, path)

    def _on_save(self) -> None:
        try:
            port = int(self.txt_port.get().strip())
            max_act = int(self.txt_max_act.get().strip())
            dl_lim = int(self.txt_dl_limit.get().strip())
            ul_lim = int(self.txt_ul_limit.get().strip())
        except ValueError:
            messagebox.showerror(
                "Validation Error",
                "Ports and limit values must be valid integers",
                parent=self,
            )
            return

        new_settings = AppSettings(
            theme=self.cmb_theme.get(),
            download_dir=self.txt_dir.get().strip(),
            aria2_host=self.txt_host.get().strip(),
            aria2_port=port,
            auto_start_daemon=self.var_autostart.get(),
            custom_aria2_path=self.txt_exe.get().strip() or None,
            max_active_downloads=max_act,
            speed_limit_download=dl_lim,
            speed_limit_upload=ul_lim,
            clipboard_watch=self.var_clipboard.get(),
            sound_notifications=self.var_sound.get(),
            close_to_tray=self.var_tray.get(),
        )

        self.ctx.settings_store.save_settings(new_settings)

        # Update runtime limits on daemon
        self.ctx.set_queue_limits_uc.execute(
            max_concurrent_downloads=max_act,
            max_download_speed=f"{dl_lim}" if dl_lim > 0 else "0",
            max_upload_speed=f"{ul_lim}" if ul_lim > 0 else "0",
        )

        self.destroy()
