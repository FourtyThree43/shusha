import threading
import time

import ttkbootstrap as ttk
from models.utilities import format_size, format_speed
from PIL import Image
from ttkbootstrap.constants import NO, YES

from shusha.controller.api import ShushaAPI as Api
from shusha.models.structs_downloads import Download

Image.CUBIC = Image.BICUBIC  # ttkbootstrap uses an attribute Image.CUBIC which
# was replaced by Image.BICUBIC in Pillow v10.0.0


class DownloadMeter(ttk.Meter):
    def __init__(self, master, **kwargs):
        super().__init__(master=master, **kwargs)
        self.paused = ttk.BooleanVar(self, NO)

    def start(self):
        self.paused.set(NO)
        while self.amountusedvar.get() <= self.amounttotalvar.get():
            if self.paused.get():
                break
            if self.amountusedvar.get() == self.amounttotalvar.get():
                self.configure(subtext="Download complete")
                break
            self.step()
            time.sleep(0.25)
            self.master.update_idletasks()

    def pause(self):
        self.paused.set(YES)

    def reset(self):
        self.amountusedvar.set(0)


class DownloadWindow(ttk.Toplevel):
    def __init__(self, api, **kwargs):
        super().__init__(
            title="File Download",
            size=(720, 400),
            position=(50, 50),
            resizable=(NO, NO),
            **kwargs,
        )
        self.config(padx=15, pady=15)
        self.api: Api = api
        self.download_gid = None

        status_lf = ttk.Labelframe(self, text="File Download Status")
        status_lf.pack(fill=ttk.BOTH, expand=NO, padx=5, ipady=30, anchor=ttk.N)

        self.stats_f = ttk.Frame(status_lf)
        self.stats_f.pack(side="left", expand=NO)

        meter_f = ttk.Frame(status_lf)
        meter_f.pack(side=ttk.RIGHT, fill=ttk.X, expand=YES)
        self.meter = DownloadMeter(
            meter_f,
            metersize=210,
            padding=5,
            amounttotal=100,
            metertype="semi",
            textright="%",
            subtext="downloaded",
            interactive=False,
            stripethickness=5,
        )
        self.meter.pack(side=ttk.RIGHT, fill=ttk.X, expand=YES)

        self.controls = ttk.Frame(self, borderwidth=1, padding=10)
        self.controls.pack(side=ttk.BOTTOM, fill=ttk.X)

        self.start_btn = ttk.Button(
            self.controls, text="Start", command=self.start, bootstyle=ttk.INFO
        )
        self.start_btn.pack(side=ttk.LEFT, padx=5)

        self.pause_btn = ttk.Button(
            self.controls,
            text="Pause",
            command=self.pause,
            bootstyle=ttk.WARNING,
        )
        self.pause_btn.pack(side=ttk.LEFT, padx=5)

        self.resume_btn = ttk.Button(
            self.controls,
            text="Resume",
            command=self.un_pause,
            bootstyle=ttk.SUCCESS,
        )
        self.resume_btn.pack(side=ttk.LEFT, padx=5)
        self.resume_btn.state(["disabled"])

        self.cancel_btn = ttk.Button(
            self.controls,
            text="Cancel",
            command=self.cancel,
            bootstyle=ttk.DANGER,
        )
        self.cancel_btn.pack(side=ttk.LEFT, padx=5)

        self.dtstats_var = ttk.StringVar(self, "")

        self.after(1000, self.update_stats_periodically)

    def update_stats_frame(self, download: Download):
        self.download_gid = download.gid

        for widget in self.stats_f.winfo_children():
            widget.destroy()

        # Update the meter with the calculated percentage
        self.meter.amountusedvar.set(int(download.progress))

        dl_info = {
            "File": download.name,
            "Link": download.files[0].uris[0].get("uri"),
            "Status": download.status,
            "Downloaded": download.completed_length_string(),
            "Total Size": download.total_length_string(),
            "Transfer Rate": download.download_speed_string(),
            "ETA": download.eta_string(),
            "Connections": download.connections,
        }

        for key, value in dl_info.items():
            label_text = f"{key} : {value}"
            label = ttk.Label(self.stats_f, text=label_text, wraplength=300)
            label.pack(side="top", anchor="w", padx=8, pady=2)

    def update_stats_periodically(self):
        if not self.download_gid:
            self.pause_btn.state(["disabled"])
            self.resume_btn.state(["disabled"])
            self.start_btn.state(["disabled"])
            self.cancel_btn.configure(text="Close")
            return

        st_struct = self.api.get_download(self.download_gid)

        self.update_stats_frame(st_struct)

        # Check if the download is complete
        if st_struct.is_active:
            self.pause_btn.state(["!disabled"])
            self.resume_btn.state(["disabled"])
            self.start_btn.state(["disabled"])
            self.cancel_btn.configure(text="Cancel")
        if st_struct.has_failed:
            self.pause_btn.state(["disabled"])
            self.resume_btn.state(["disabled"])
            self.start_btn.state(["!disabled"])
            self.start_btn.configure(text="Restart")
            self.cancel_btn.configure(text="Close")
            self.meter.configure(subtext="Download failed")
            self.meter.reset()
        if st_struct.is_complete:
            self.pause_btn.state(["disabled"])
            self.resume_btn.state(["disabled"])
            self.start_btn.state(["!disabled"])
            self.start_btn.configure(text="Restart")
            self.cancel_btn.configure(text="Close")
        else:
            # If not complete, continue updating periodically
            self.after(1000, self.update_stats_periodically)

    def start(self):
        if self.download_gid:
            if self.start_btn.cget("text") == "Restart":
                self.meter.reset()
                self.start_btn.configure(text="Start")
                self.cancel_btn.configure(text="Cancel")
                self.pause_btn.state(["!disabled"])
                self.resume_btn.state(["disabled"])
                self.start_btn.state(["!disabled"])
                # self.api.
                return

            self.start_btn.state(["disabled"])
            self.update_stats_periodically()
            threading.Thread(target=self.meter.start).start()
        else:
            return

    def pause(self):
        if self.download_gid:
            self.api.pause(self.download_gid)
            self.meter.pause()
            self.pause_btn.state(["disabled"])
            self.resume_btn.state(["!disabled"])

    def un_pause(self):
        if self.download_gid:
            self.api.resume(self.download_gid)
            self.update_stats_periodically_v2()
            self.resume_btn.state(["disabled"])
            self.pause_btn.state(["!disabled"])

    def cancel(self):
        if (
            self.cancel_btn.cget("text") == "Cancel"
            and self.download_gid is not None
        ):
            self.api.remove(self.download_gid)
            self.meter.configure(subtext="downloaded")
            self.meter.reset()
            self.resume_btn.state(["disabled"])
            self.pause_btn.state(["disabled"])
            self.start_btn.state(["!disabled"])
            self.start_btn.configure(text="Start")
            self.download_gid = None
        else:
            self.close_window()

    def close_window(self):
        self.destroy()
