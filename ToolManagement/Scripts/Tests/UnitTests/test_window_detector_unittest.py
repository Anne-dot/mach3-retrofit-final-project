r"""
test_window_detector.py - Unit tests for window_detector module.

This script tests the WindowDetector class, mocking the Windows API
functions to simulate different scenarios.

Place in: C:\Mach3\ToolManagement\Scripts\Tests\UnitTests\
"""

import sys
import unittest

if not sys.platform.startswith("win"):
    raise unittest.SkipTest("Skipping Windows-only test on non-Windows platform")

import os
import tempfile
import win32gui
import win32process
import win32api
from unittest.mock import patch, MagicMock

# Add FileMonitor directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'FileMonitor'))

# Import module to test
from window_detector import WindowDetector

class TestWindowDetector(unittest.TestCase):
    """Test cases for the WindowDetector class."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a detector with debug mode on
        self.detector = WindowDetector(debug_mode=True)
        
        # Create a temporary test file
        self.test_fd, self.test_path = tempfile.mkstemp(suffix='.txt')
        os.write(self.test_fd, b'Test content')
        os.close(self.test_fd)
        
        # Get just the filename
        self.test_filename = os.path.basename(self.test_path)
        
        # Print test file info for debugging
        print(f"Test file created: {self.test_path}")
        print(f"Test filename: {self.test_filename}")
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary file
        if os.path.exists(self.test_path):
            os.unlink(self.test_path)
            print(f"Test file removed: {self.test_path}")
    
    def test_file_not_found(self):
        """Test behavior when file doesn't exist."""
        non_existent_file = os.path.join(tempfile.gettempdir(), "non_existent_file.txt")
        self.assertFalse(self.detector.is_file_open(non_existent_file))
    
    @patch('win32gui.EnumWindows')
    @patch('win32gui.IsWindowVisible')
    @patch('win32gui.GetWindowText')
    @patch('win32process.GetWindowThreadProcessId')
    @patch('win32api.OpenProcess')
    @patch('win32process.GetModuleFileNameEx')
    @patch('win32api.CloseHandle')
    def test_notepad_detection(self, mock_close, mock_get_module, mock_open, 
                              mock_get_thread, mock_get_text, mock_visible, 
                              mock_enum_windows):
        """Test detection of file open in Notepad."""
        # Setup mocks
        mock_visible.return_value = True
        mock_get_text.return_value = f"{self.test_filename} - Notepad"
        mock_get_thread.return_value = (1, 100)
        mock_open.return_value = MagicMock()
        mock_get_module.return_value = "notepad.exe"
        
        # Setup EnumWindows to call callback with dummy window handle
        def enum_windows_side_effect(callback, extra):
            callback(1, extra)
            return True
            
        mock_enum_windows.side_effect = enum_windows_side_effect
        
        # Call the method
        result = self.detector.is_file_open(self.test_path)
        
        # Verify result
        self.assertTrue(result)
        mock_enum_windows.assert_called_once()
    
    @patch('win32gui.EnumWindows')
    @patch('win32gui.IsWindowVisible')
    @patch('win32gui.GetWindowText')
    @patch('win32process.GetWindowThreadProcessId')
    @patch('win32api.OpenProcess')
    @patch('win32process.GetModuleFileNameEx')
    @patch('win32api.CloseHandle')
    def test_wordpad_detection(self, mock_close, mock_get_module, mock_open, 
                              mock_get_thread, mock_get_text, mock_visible, 
                              mock_enum_windows):
        """Test detection of file open in WordPad."""
        # Setup mocks
        mock_visible.return_value = True
        mock_get_text.return_value = f"{self.test_filename} - WordPad"
        mock_get_thread.return_value = (1, 100)
        mock_open.return_value = MagicMock()
        mock_get_module.return_value = "wordpad.exe"
        
        # Setup EnumWindows to call callback with dummy window handle
        def enum_windows_side_effect(callback, extra):
            callback(1, extra)
            return True
            
        mock_enum_windows.side_effect = enum_windows_side_effect
        
        # Call the method
        result = self.detector.is_file_open(self.test_path)
        
        # Verify result
        self.assertTrue(result)
        mock_enum_windows.assert_called_once()
    
    @patch('win32gui.EnumWindows')
    @patch('win32gui.IsWindowVisible')
    @patch('win32gui.GetWindowText')
    @patch('win32process.GetWindowThreadProcessId')
    @patch('win32api.OpenProcess')
    @patch('win32process.GetModuleFileNameEx')
    @patch('win32api.CloseHandle')
    def test_file_not_open(self, mock_close, mock_get_module, mock_open, 
                           mock_get_thread, mock_get_text, mock_visible, 
                           mock_enum_windows):
        """Test when file is not open in any editor."""
        # Setup mocks
        mock_visible.return_value = True
        mock_get_text.return_value = "Different File.txt - Notepad"
        mock_get_thread.return_value = (1, 100)
        mock_open.return_value = MagicMock()
        mock_get_module.return_value = "notepad.exe"
        
        # Setup EnumWindows to call callback with dummy window handle
        def enum_windows_side_effect(callback, extra):
            callback(1, extra)
            return True
            
        mock_enum_windows.side_effect = enum_windows_side_effect
        
        # Call the method
        result = self.detector.is_file_open(self.test_path)
        
        # Verify result
        self.assertFalse(result)
        mock_enum_windows.assert_called_once()
    
    @patch('win32gui.EnumWindows')
    @patch('win32gui.IsWindowVisible')
    @patch('win32gui.GetWindowText')
    @patch('win32process.GetWindowThreadProcessId')
    @patch('win32api.OpenProcess')
    @patch('win32process.GetModuleFileNameEx')
    @patch('win32api.CloseHandle')
    def test_get_application_with_file(self, mock_close, mock_get_module, mock_open, 
                                 mock_get_thread, mock_get_text, mock_visible, 
                                 mock_enum_windows):
        """Test getting the application name."""
        # Setup mocks
        mock_visible.return_value = True
        mock_get_text.return_value = f"{self.test_filename} - Notepad"
        mock_get_thread.return_value = (1, 100)
        mock_open.return_value = MagicMock()
        mock_get_module.return_value = "notepad.exe"
        
        # Setup EnumWindows to call callback with dummy window handle
        def enum_windows_side_effect(callback, extra):
            callback(1, extra)
            return True
            
        mock_enum_windows.side_effect = enum_windows_side_effect
        
        # Call the method
        result = self.detector.get_application_with_file(self.test_path)
        
        # Verify result
        self.assertEqual(result, "Notepad")
        mock_enum_windows.assert_called_once()


if __name__ == '__main__':
    print("Running WindowDetector unit tests...\n")
    unittest.main(verbosity=2)
    
    # Keep console open
    input("\nPress Enter to close...")
