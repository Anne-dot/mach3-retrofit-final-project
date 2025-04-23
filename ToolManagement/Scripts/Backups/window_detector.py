"""
Window title detector for identifying open files in Notepad and Wordpad.

This module provides functionality to detect if a specific file is open
in Notepad or Wordpad by examining window titles.
"""

import os
import win32gui
import win32process
import win32api
import logging
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WindowDetector:
    """
    Detects if files are open in specific applications by checking window titles.
    
    This class uses the Windows API to enumerate window titles and
    check if they contain a specific filename.
    """
    
    def __init__(self, debug_mode: bool = False):
        """
        Initialize the WindowDetector.
        
        Args:
            debug_mode: If True, enables debug logging
        """
        self.debug_mode = debug_mode
        if self.debug_mode:
            logger.setLevel(logging.DEBUG)
        
        # Window title patterns for different applications
        self.application_patterns = {
            'notepad': [' - Notepad', 'Notepad - '],
            'wordpad': [' - WordPad', 'WordPad - ']
        }
        
        self.windows = []
    
    def is_file_open(self, file_path: str) -> bool:
        """
        Check if a file is open in Notepad or Wordpad.
        
        Args:
            file_path: The full path to the file to check
            
        Returns:
            True if the file is open in Notepad or Wordpad, False otherwise
        """
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return False
            
        # Get filename from path
        filename = os.path.basename(file_path)
        
        # Update window list
        self._enumerate_windows()
        
        # Check if file is open in any supported application
        return self._check_file_in_windows(filename)
    
    def _enumerate_windows(self) -> None:
        """
        Enumerate all open windows and store their information.
        """
        self.windows = []
        
        def enum_windows_callback(hwnd, _):
            """Callback function for EnumWindows."""
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                
                if window_title:
                    # Get process info
                    try:
                        _, process_id = win32process.GetWindowThreadProcessId(hwnd)
                        process_name = os.path.basename(
                            win32process.GetModuleFileNameEx(
                                win32api.OpenProcess(0x1000, False, process_id),
                                0
                            )
                        ).lower()
                    except Exception as e:
                        if self.debug_mode:
                            logger.debug(f"Error getting process info: {e}")
                        process_name = "unknown"
                    
                    self.windows.append((hwnd, window_title, process_name))
                    
                    if self.debug_mode:
                        logger.debug(f"Window: '{window_title}' Process: '{process_name}'")
            
            return True
        
        # Enumerate windows
        win32gui.EnumWindows(enum_windows_callback, None)
    
    def _check_file_in_windows(self, filename: str) -> bool:
        """
        Check if a filename appears in window titles of supported applications.
        
        Args:
            filename: The filename to look for
            
        Returns:
            True if the file appears to be open, False otherwise
        """
        # Check each window
        for _, title, process_name in self.windows:
            # Check Notepad
            if "notepad.exe" in process_name:
                if self._check_title_contains_file(title, filename, 'notepad'):
                    logger.info(f"File '{filename}' detected open in Notepad")
                    return True
            
            # Check WordPad
            elif "wordpad.exe" in process_name:
                if self._check_title_contains_file(title, filename, 'wordpad'):
                    logger.info(f"File '{filename}' detected open in WordPad")
                    return True
        
        logger.info(f"File '{filename}' not detected in any supported editor")
        return False
    
    def _check_title_contains_file(self, title: str, filename: str, app_type: str) -> bool:
        """
        Check if a window title indicates that it has a specific file open.
        
        Args:
            title: The window title
            filename: The filename to check for
            app_type: The application type (notepad or wordpad)
            
        Returns:
            True if the title indicates the file is open, False otherwise
        """
        # Check if filename is in title
        if filename in title:
            # Check if title matches application pattern
            for pattern in self.application_patterns.get(app_type, []):
                if pattern in title:
                    if self.debug_mode:
                        logger.debug(f"Match found: '{filename}' in '{title}'")
                    return True
        
        return False
    
    def get_application_with_file(self, file_path: str) -> Optional[str]:
        """
        Determine which application has the file open.
        
        Args:
            file_path: The full path to the file to check
            
        Returns:
            Application name if the file is open, None otherwise
        """
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return None
            
        # Get filename from path
        filename = os.path.basename(file_path)
        
        # Update window list
        self._enumerate_windows()
        
        # Check each window
        for _, title, process_name in self.windows:
            # Check Notepad
            if "notepad.exe" in process_name:
                if self._check_title_contains_file(title, filename, 'notepad'):
                    return "Notepad"
            
            # Check WordPad
            elif "wordpad.exe" in process_name:
                if self._check_title_contains_file(title, filename, 'wordpad'):
                    return "WordPad"
        
        return None
