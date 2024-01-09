# SPDX-FileCopyrightText: 2023-present FourtyThree43 <shaqmwa@outlook.com>
#
# SPDX-License-Identifier: MIT

import signal
import time

from app import Aria2Gui
from models.logger import LoggerService

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

    app = Aria2Gui()

    try:
        app.run()
    except KeyboardInterrupt:
        # Handle KeyboardInterrupt (Ctrl+C) to ensure proper cleanup
        logger.log("Received KeyboardInterrupt. Cleaning up...",
                   level="warning")
        app.cleanup()


if __name__ == "__main__":
    main()
