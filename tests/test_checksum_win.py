import tempfile
import unittest
from pathlib import Path

import ttkbootstrap as ttk

from shusha.views.checksum_win import ChecksumWindow


class TestChecksumWindow(unittest.TestCase):
    def test_checksum_window_computation(self):
        try:
            root = ttk.Window(themename="bootstrap-dark")
            root.withdraw()
        except Exception:
            self.skipTest("Display not available for Tkinter ChecksumWindow test")

        with tempfile.TemporaryDirectory() as tmpdir:
            sample_file = Path(tmpdir) / "sample.txt"
            sample_file.write_text("Hello World Shusha")

            win = ChecksumWindow(
                master=root, initial_file=sample_file, compute_on_open=False
            )
            self.assertIsInstance(win, ttk.Toplevel)

            # Synchronously run compute logic
            win.compute_hashes_sync(sample_file)

            # Check values
            self.assertEqual(
                win.hash_vars["MD5"].get(), "b3c9cba8e007e137110d4d1257a60cc3"
            )
            self.assertTrue(len(win.hash_vars["SHA-256"].get()) > 0)

            # Test compare
            win.expected_hash_var.set("b3c9cba8e007e137110d4d1257a60cc3")
            win._check_match()
            self.assertIn("MATCH", win.status_msg_var.get())

            win.expected_hash_var.set("invalid_hash_value")
            win._check_match()
            self.assertIn("MISMATCH", win.status_msg_var.get())

            root.destroy()


if __name__ == "__main__":
    unittest.main()
