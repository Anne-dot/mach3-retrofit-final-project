"""
window_detector.py - Detects if files are open in Notepad or Wordpad.

This module provides a simple class to detect if a specific file is
currently open in Notepad or Wordpad by checking window titles.

Place in: C:\Mach3\ToolManagement\Scripts\FileMonitor\
"""


import os
import subprocess
import logging

class WindowDetector:
    """Detects if files are open in Notepad or Wordpad."""

    def __init__(self, debug_mode=False):
        self.debug_mode = debug_mode

        logging.basicConfig(
            level=logging.DEBUG if debug_mode else logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def is_file_open(self, file_path):
        """Check if a file is open in Notepad or Wordpad."""
        if not os.path.exists(file_path):
            self.logger.warning(f"File not found: {file_path}")
            return False

        filename = os.path.basename(file_path)
        name_variants = [filename.replace("_", "-"), f"*{filename.replace('_', '-')}"]
        self.logger.debug(f"Checking if any of {name_variants} is open")

        titles = self._get_open_window_titles()

        for title in titles:
            for name in name_variants:
                if name.lower() in title.lower():
                    if "notepad" in title.lower():
                        self.logger.info(f"File '{filename}' is open in Notepad")
                        return True
                    if "wordpad" in title.lower():
                        self.logger.info(f"File '{filename}' is open in WordPad")
                        return True

        self.logger.debug(f"File '{filename}' is not open in Notepad or WordPad")
        return False

    def _get_open_window_titles(self):
        """Use PowerShell to get open window titles."""
        try:
            result = subprocess.run(
                ['powershell', '-Command',
                 'Get-Process | Where-Object {$_.MainWindowTitle -and ($_.ProcessName -eq "notepad" -or $_.ProcessName -eq "wordpad")} | Select-Object -ExpandProperty MainWindowTitle'],
                capture_output=True, text=True
            )
            if self.debug_mode:
                self.logger.debug("Open window titles:\n" + result.stdout)
            return result.stdout.splitlines()
        except Exception as e:
            self.logger.error(f"Failed to retrieve open windows: {e}")
            return []

if __name__ == "__main__":
    detector = WindowDetector(debug_mode=True)
    open_titles = detector._get_open_window_titles()
    print("\nOpen windows:")
    for title in open_titles:
        print(f"- {title}")
