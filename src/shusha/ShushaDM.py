# SPDX-FileCopyrightText: 2023-present FourtyThree43 <shaqmwa@outlook.com>
#
# SPDX-License-Identifier: MIT

import time
from pathlib import Path

import ttkbootstrap as ttk

from shusha.models.logger import LoggerService
from shusha.views.app import Aria2Gui

logger = LoggerService(__name__)
OUTPUT_PATH = Path(__file__).parent
ICON_PATH = OUTPUT_PATH / Path("shusha.ico")


def cleanup(api):
    # if guimode or sett.get('persistent'):
    #     setting.save_setting()
    # controller.quit()
    try:
        logger.log("Performing comprehensive cleanup...")
        # For example, save session, close connections, etc.
        # api.save_session()
        # api.stop_server()
        time.sleep(1)  # give time to other threads to quit
    except Exception as e:
        logger.log(f"Error during cleanup: {e}", level="error")
    api.stop_server()


def main(argv: list[str] | None = None):
    """Run the main program.

    Parameters:
        args: Parameters passed from the command line.

    Returns:
        None
    """

    def on_close():
        my_app_instance.cleanup()

        # Destroy the ttk.Window instance
        app.destroy()

    app = ttk.Window(
        title="Shusha",
        themename="darkly",
        size=(1270, 550),
        resizable=(False, False),
        position=(10, 140),
    )

    app.iconbitmap(str(ICON_PATH))
    my_app_instance = Aria2Gui(app)
    app.wm_protocol("WM_DELETE_WINDOW", on_close)
    app.mainloop()


if __name__ == "__main__":
    main()
