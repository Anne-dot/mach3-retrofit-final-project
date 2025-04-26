import subprocess
import time
import unittest
from pathlib import Path
import os
import sys
import unittest

from window_detector import is_tool_data_open  # assumes your function is in this file

@unittest.skipUnless(sys.platform.startswith("win"), "Windows-only test")
class TestToolDataWindow(unittest.TestCase):
    def setUp(self):
        self.test_file = Path("tool-data.txt")
        self.test_file.write_text("Test content.")

    def test_tool_data_open_close(self):
        # Open file in Notepad
        proc = subprocess.Popen(["notepad.exe", str(self.test_file)])
        time.sleep(2)  # Give it time to fully open

        # Check that it's detected as open
        self.assertTrue(is_tool_data_open())

        # Close Notepad
        subprocess.run(["taskkill", "/IM", "notepad.exe", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)  # Give it time to close

        # Check that it's detected as closed
        self.assertFalse(is_tool_data_open())

    def tearDown(self):
        if self.test_file.exists():
            self.test_file.unlink()

if __name__ == "__main__":
    unittest.main()

