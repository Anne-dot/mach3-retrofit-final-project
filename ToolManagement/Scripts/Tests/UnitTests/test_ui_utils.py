"""
Unit tests for the ui_utils module.

These tests verify that the UI utilities work correctly across platforms
by mocking dialog functionality instead of showing actual UI elements.
"""

import unittest
import os
import sys
import tempfile
import platform
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add parent directory to path to import the module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the modules to test
from Utils.ui_utils import UIUtils
from Utils.error_utils import FileError


class TestUIUtils(unittest.TestCase):
    """Tests for the UIUtils class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_file.txt")
        
        # Create a test file
        with open(self.test_file, 'w') as f:
            f.write("Test content")
    
    def tearDown(self):
        """Clean up after tests."""
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('tkinter.filedialog.askopenfilename')
    @patch('tkinter.Tk')
    def test_select_file_tkinter_open_success(self, mock_tk, mock_open):
        """Test successful file selection dialog using tkinter (open mode)."""
        # Configure mock to return a file path
        mock_open.return_value = self.test_file
        
        # Call select_file
        success, file_path, details = UIUtils.select_file(
            title="Test Open",
            initial_dir=self.temp_dir
        )
        
        # Verify result
        self.assertTrue(success)
        self.assertEqual(file_path, self.test_file)
        self.assertIn("file_path", details)
        
        # Verify mock was called with correct arguments
        mock_open.assert_called_once()
        self.assertIn("initialdir", mock_open.call_args[1])
        self.assertEqual(mock_open.call_args[1]["initialdir"], self.temp_dir)
    
    @patch('tkinter.filedialog.askopenfilename')
    @patch('tkinter.Tk')
    def test_select_file_tkinter_open_cancel(self, mock_tk, mock_open):
        """Test canceled file selection dialog using tkinter (open mode)."""
        # Configure mock to return empty string (dialog canceled)
        mock_open.return_value = ""
        
        # Call select_file
        success, file_path, details = UIUtils.select_file(
            title="Test Open",
            initial_dir=self.temp_dir
        )
        
        # Verify result
        self.assertFalse(success)
        self.assertIn("canceled", file_path.lower())
    
    @patch('tkinter.filedialog.asksaveasfilename')
    @patch('tkinter.Tk')
    def test_select_file_tkinter_save_success(self, mock_tk, mock_save):
        """Test successful file selection dialog using tkinter (save mode)."""
        # Configure mock to return a file path
        save_path = os.path.join(self.temp_dir, "save_file.txt")
        mock_save.return_value = save_path
        
        # Call select_file with save_dialog=True
        success, file_path, details = UIUtils.select_file(
            title="Test Save",
            initial_dir=self.temp_dir,
            save_dialog=True
        )
        
        # Verify result
        self.assertTrue(success)
        self.assertEqual(file_path, save_path)
        self.assertIn("file_path", details)
        
        # Verify mock was called with correct arguments
        mock_save.assert_called_once()
        self.assertIn("initialdir", mock_save.call_args[1])
        self.assertEqual(mock_save.call_args[1]["initialdir"], self.temp_dir)
    
    @patch('tkinter.filedialog.askopenfilename', side_effect=ImportError("No tkinter"))
    def test_select_file_tkinter_fallback_to_cli(self, mock_open):
        """Test fallback to CLI when tkinter is not available."""
        # Mock input function to simulate user input
        with patch('builtins.input', return_value=self.test_file):
            # Call select_file
            success, file_path, details = UIUtils.select_file(
                title="Test Open",
                initial_dir=self.temp_dir
            )
            
            # Verify result
            self.assertTrue(success)
            self.assertEqual(file_path, self.test_file)
            self.assertIn("file_path", details)
    
    @patch('builtins.input')
    def test_select_file_cli_success(self, mock_input):
        """Test CLI file selection success."""
        # Configure mock to return a file path
        mock_input.return_value = self.test_file
        
        # Monkey patch UIUtils to directly use CLI version
        original_select_file = UIUtils.select_file
        UIUtils.select_file = UIUtils._select_file_cli
        
        try:
            # Call select_file
            success, file_path, details = UIUtils.select_file(
                title="Test Open",
                initial_dir=self.temp_dir,
                file_types=[("Text Files", "*.txt")]
            )
            
            # Verify result
            self.assertTrue(success)
            self.assertEqual(file_path, self.test_file)
            self.assertIn("file_path", details)
        finally:
            # Restore original method
            UIUtils.select_file = original_select_file
    
    @patch('builtins.input')
    def test_select_file_cli_nonexistent_file(self, mock_input):
        """Test CLI file selection with non-existent file."""
        # Configure mock to return a non-existent file path
        nonexistent = os.path.join(self.temp_dir, "nonexistent.txt")
        mock_input.return_value = nonexistent
        
        # Monkey patch UIUtils to directly use CLI version
        original_select_file = UIUtils.select_file
        UIUtils.select_file = UIUtils._select_file_cli
        
        try:
            # Call select_file
            success, file_path, details = UIUtils.select_file(
                title="Test Open",
                initial_dir=self.temp_dir
            )
            
            # Verify result - should fail since file doesn't exist
            self.assertFalse(success)
            self.assertIn("not found", file_path)
        finally:
            # Restore original method
            UIUtils.select_file = original_select_file
    
    @patch('tkinter.messagebox.showinfo')
    @patch('tkinter.Tk')
    def test_message_dialog_info(self, mock_tk, mock_info):
        """Test information message dialog."""
        # Call message_dialog
        success, _, details = UIUtils.message_dialog(
            title="Test Info",
            message="This is a test message",
            message_type="info"
        )
        
        # Verify result
        self.assertTrue(success)
        self.assertEqual(details["message_type"], "info")
        
        # Verify mock was called with correct arguments
        mock_info.assert_called_once_with("Test Info", "This is a test message")
    
    @patch('tkinter.messagebox.showwarning')
    @patch('tkinter.Tk')
    def test_message_dialog_warning(self, mock_tk, mock_warning):
        """Test warning message dialog."""
        # Call message_dialog
        success, _, details = UIUtils.message_dialog(
            title="Test Warning",
            message="This is a warning",
            message_type="warning"
        )
        
        # Verify result
        self.assertTrue(success)
        self.assertEqual(details["message_type"], "warning")
        
        # Verify mock was called with correct arguments
        mock_warning.assert_called_once_with("Test Warning", "This is a warning")
    
    @patch('tkinter.messagebox.showerror')
    @patch('tkinter.Tk')
    def test_message_dialog_error(self, mock_tk, mock_error):
        """Test error message dialog."""
        # Call message_dialog
        success, _, details = UIUtils.message_dialog(
            title="Test Error",
            message="This is an error",
            message_type="error"
        )
        
        # Verify result
        self.assertTrue(success)
        self.assertEqual(details["message_type"], "error")
        
        # Verify mock was called with correct arguments
        mock_error.assert_called_once_with("Test Error", "This is an error")
    
    @patch('tkinter.messagebox.showinfo', side_effect=ImportError("No tkinter"))
    @patch('builtins.print')
    @patch('builtins.input')
    def test_message_dialog_fallback_to_console(self, mock_input, mock_print, mock_info):
        """Test fallback to console when tkinter is not available."""
        # Mock input to simulate user pressing Enter
        mock_input.return_value = ""
        
        # Call message_dialog
        success, _, details = UIUtils.message_dialog(
            title="Console Test",
            message="Console message",
            message_type="info"
        )
        
        # Verify result
        self.assertTrue(success)
        self.assertEqual(details["message_type"], "info")
        
        # Verify print was called with the message
        found_message = False
        for call in mock_print.call_args_list:
            args = call[0]
            if len(args) > 0 and "Console message" in str(args[0]):
                found_message = True
                break
        
        self.assertTrue(found_message, "Message not printed to console")


if __name__ == '__main__':
    unittest.main()
