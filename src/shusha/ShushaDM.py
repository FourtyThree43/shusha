# SPDX-FileCopyrightText: 2023-present FourtyThree43 <shaqmwa@outlook.com>
#
# SPDX-License-Identifier: MIT

import time

import ttkbootstrap as ttk
from models.logger import LoggerService
from view.app import Aria2Gui

logger = LoggerService(__name__)


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

    app = ttk.Window(title="App",
                     themename="darkly",
                     size=(1270, 550),
                     resizable=(False, False),
                     position=(10, 140))

    my_app_instance = Aria2Gui(app)
    app.wm_protocol("WM_DELETE_WINDOW", on_close)
    app.mainloop()


if __name__ == "__main__":
    main()
