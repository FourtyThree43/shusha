import threading
import time

import ttkbootstrap as ttk
from PIL import Image
from ttkbootstrap.constants import NO, YES

Image.CUBIC = Image.BICUBIC  # ttkbootstrap uses an attribute Image.CUBIC which
# was replaced by Image.BICUBIC in Pillow v10.0.0


def sizeof_fmt(num, delim=" ", suffix="B"):
    for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{delim}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}{delim}Yi{suffix}"


def format_speed(speed):
    return sizeof_fmt(speed, suffix="B/s")


def format_size(size):
    return sizeof_fmt(size, suffix="B")


class DownloadMeter(ttk.Meter):

    def __init__(self, master, **kwargs):
        super().__init__(master=master, **kwargs)
        self.paused = ttk.BooleanVar(self, NO)

    def start(self):
        self.paused.set(NO)
        # i = self.amountusedvar.get()
        while self.amountusedvar.get() <= self.amounttotalvar.get():
            if self.paused.get():
                break
            if self.amountusedvar.get() == self.amounttotalvar.get():
                self.configure(subtext="Download complete")
                break
            self.step()
            time.sleep(0.25)
            # i = self.amountusedvar.get()
            self.master.update_idletasks()

    def pause(self):
        self.paused.set(YES)
        # self.master.update_idletasks()

    def reset(self):
        self.amountusedvar.set(0)


class DownloadWindow(ttk.Toplevel):

    def __init__(self, **kwargs):
        super().__init__(title="File Download",
                         size=(720, 380),
                         position=(50, 50),
                         resizable=(NO, NO),
                         **kwargs)
        self.config(padx=15, pady=15)

        status_lf = ttk.Labelframe(self, text="File Download Status")
        status_lf.pack(
            fill=ttk.BOTH,
            expand=YES,
            padx=5,
            ipady=30,
            anchor=ttk.N,
        )

        self.stats_f = ttk.Frame(status_lf)
        self.stats_f.pack(side="left", fill=ttk.X, expand=NO)

        meter_f = ttk.Frame(status_lf)
        meter_f.pack(side=ttk.RIGHT, fill=ttk.X, expand=YES)
        self.meter = DownloadMeter(meter_f,
                                   metersize=210,
                                   padding=5,
                                   amounttotal=100,
                                   metertype="semi",
                                   textright="%",
                                   subtext="downloaded",
                                   interactive=False,
                                   stripethickness=5)
        self.meter.pack(side=ttk.RIGHT, fill=ttk.X, expand=YES)

        self.controls = ttk.Frame(self, borderwidth=1, padding=10)
        self.controls.pack(side=ttk.BOTTOM, fill=ttk.X)

        self.start_btn = ttk.Button(self.controls,
                                    text="Start",
                                    command=self.start,
                                    bootstyle=ttk.INFO)
        self.start_btn.pack(side=ttk.LEFT, padx=5)

        self.pause_btn = ttk.Button(self.controls,
                                    text="Pause",
                                    command=self.pause,
                                    bootstyle=ttk.WARNING)
        self.pause_btn.pack(side=ttk.LEFT, padx=5)

        self.reset_btn = ttk.Button(self.controls,
                                    text="Reset",
                                    command=self.reset,
                                    bootstyle=ttk.DANGER)
        self.reset_btn.pack(side=ttk.LEFT, padx=5)

    def modify_stats_keys(self, gstats):
        # Mapping of keys to display names
        key_mapping = {
            "uri": "Link",
            "status": "Status",
            "completedLength": "Downloaded",
            "totalLength": "Total Size",
            "downloadSpeed": "Transfer Rate",
            "connections": "Connections",
        }

        # Modify keys as needed
        modified_gstats = {
            f"{key_mapping.get(key, key)}": value
            for key, value in gstats.items()
        }
        return modified_gstats

    def update_stats_frame(self, gstats):
        modified_gstats = self.modify_stats_keys(gstats)

        for key, value in modified_gstats.items():
            # Format the value using sizeof_fmt
            if key in ['Transfer Rate', 'Upload Speed']:
                value = format_speed(float(value))
            elif key in ['Downloaded', 'Total Size']:
                value = format_size(float(value))

            # Create label for key and value on the same row
            label_text = f"{key} : {value}"
            label = ttk.Label(self.stats_f, text=label_text)
            label.pack(side="top", anchor="w", padx=8, pady=8)

    def start(self):
        self.start_btn.state(["disabled"])
        threading.Thread(target=self.meter.start).start()

    def pause(self):
        self.meter.pause()
        self.start_btn.state(["!disabled"])

        if self.meter.amountusedvar.get() < self.meter.amounttotalvar.get():
            self.start_btn.configure(text="Resume")

    def reset(self):
        self.pause()
        self.meter.configure(subtext="downloaded")
        self.meter.reset()
        self.start_btn.configure(text="Start")


ttk.Window(themename="darkly")
sample_stats = {
    "uri": "https://proof.ovh.net/files/10Mb.dat",
    "status": "Active",
    "completedLength": "6942000",
    "totalLength": "15000000",
    "downloadSpeed": "3000000",
    "connections": "3",
}
download_window = DownloadWindow()
download_window.update_stats_frame(sample_stats)
DownloadWindow().mainloop()
