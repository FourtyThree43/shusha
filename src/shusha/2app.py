import signal

from app import Aria2Gui


class SignalHandlers:

    def __init__(self, api):
        self.api = api

        # Set up signal handlers
        signal.signal(signal.SIGINT, self.handle_sigint)
        signal.signal(signal.SIGTERM, self.handle_sigterm)
        # Add more signal handlers if needed

    def handle_sigint(self, signum, frame):
        print("Received SIGINT (Ctrl+C). Cleaning up...")
        self.cleanup()
        exit(0)

    def handle_sigterm(self, signum, frame):
        print("Received SIGTERM. Cleaning up...")
        self.cleanup()
        exit(0)

    def cleanup(self):
        try:
            # Additional cleanup steps if needed
            print("Performing comprehensive cleanup...")
            # For example, save session, close connections, etc.
            self.api.save_session()
            self.api.stop_server()
        except Exception as e:
            print(f"Error during cleanup: {e}")


# Example usage:
if __name__ == "__main__":
    app = Aria2Gui()
    signal_handlers = SignalHandlers(app)

    try:
        # Run the Tkinter main loop
        app.mainloop()
    except KeyboardInterrupt:
        # Handle KeyboardInterrupt (Ctrl+C) to ensure proper cleanup
        print("Received KeyboardInterrupt. Cleaning up...")
        SignalHandlers.cleanup(app)
    finally:
        # Call cleanup function for other exit scenarios
        SignalHandlers.cleanup(app)
