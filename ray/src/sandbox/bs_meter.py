import ttkbootstrap as ttk
from PIL import Image
import threading
import time
from ttkbootstrap.constants import NO, YES

Image.CUBIC = Image.BICUBIC  # ttkbootstrap uses an attribute Image.CUBIC which
# was replaced by Image.BICUBIC in Pillow v10.0.0


class DownloadMeter(ttk.Meter):

    def __init__(self, master, **kwargs):
        super().__init__(master=master, **kwargs)
        self.paused = ttk.BooleanVar(self, NO)

    def start(self):
        self.paused.set(NO)
        i = self.amountusedvar.get()
        while i <= 100:
            if self.paused.get():
                break
            if i == 100:
                self.configure(subtext="Download complete")
                break
            self.step()
            time.sleep(1)
            i = self.amountusedvar.get()
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

        self.meter = DownloadMeter(self,
                                   metersize=180,
                                   padding=5,
                                   amounttotal=100,
                                   metertype="semi",
                                   textright="%",
                                   subtext="downloaded",
                                   interactive=False,
                                   stripethickness=5)
        self.meter.pack(expand=YES)

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

    def start(self):
        self.start_btn.state(["disabled"])
        threading.Thread(target=self.meter.start).start()

    def pause(self):
        self.meter.pause()
        self.start_btn.state(["!disabled"])

    def reset(self):
        self.pause()
        self.meter.configure(subtext="downloaded")
        self.meter.reset()


ttk.Window(themename="darkly")
DownloadWindow().mainloop()
