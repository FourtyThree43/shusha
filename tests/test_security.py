import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from shusha.controller.api import ShushaAPI


class TestSecurity(unittest.TestCase):
    def test_incomplete_download_file_protection(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "incomplete.bin"
            file_path.write_bytes(b"data")

            mock_dl = MagicMock()
            mock_dl.is_complete = False
            mock_dl.root_files_paths = [file_path]

            # Without force=True, incomplete downloads must not be moved or copied
            res_move = ShushaAPI.move_files([mock_dl], tmp_dir + "/dest", force=False)
            self.assertEqual(res_move, [False])

            res_copy = ShushaAPI.copy_files([mock_dl], tmp_dir + "/dest", force=False)
            self.assertEqual(res_copy, [False])

            res_remove = ShushaAPI.remove_files([mock_dl], force=False)
            self.assertEqual(res_remove, [False])
            self.assertTrue(file_path.exists())

    def test_nonexistent_file_removal_safety(self):
        nonexistent = Path("/path/that/does/not/exist/at/all.bin")
        mock_dl = MagicMock()
        mock_dl.is_complete = True
        mock_dl.root_files_paths = [nonexistent]

        # Should not raise exception
        res = ShushaAPI.remove_files([mock_dl], force=True)
        self.assertEqual(res, [True])


if __name__ == "__main__":
    unittest.main()
