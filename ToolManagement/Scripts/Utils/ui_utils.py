"""
User interface utilities for the CNC milling project.

This module provides platform-specific file selection dialogs and other
UI functionality that works consistently across Windows and Linux.

Classes:
    UIUtils: Main class for UI operations across platforms
"""

import os
import sys
import platform
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any, Union

# Import project utilities
try:
    from Utils.error_utils import FileError, ErrorSeverity, ErrorHandler
    from Utils.path_utils import PathUtils
except ImportError:
    # Add parent directory to path for standalone testing
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from error_utils import FileError, ErrorSeverity, ErrorHandler
    from path_utils import PathUtils


class UIUtils:
    """
    Provides cross-platform UI utilities with fallbacks.
    
    This class implements file dialogs and other UI functionality that
    works consistently on both Windows and Linux development environments.
    """
    
    @staticmethod
    def print_separator(title: Optional[str] = None) -> None:
        """
        Print a separator line with optional title.
        
        Args:
            title: Optional title to display in the separator
        """
        width = 80
        if title:
            padding_left = (width - len(title) - 2) // 2
            padding_right = width - len(title) - 2 - padding_left
            print(f"\n{'=' * padding_left} {title} {'=' * padding_right}")
        else:
            print("\n" + "=" * width)
    
    @staticmethod
    def keep_terminal_open(message: str = "All operations have been completed.") -> None:
        """
        Keep the terminal window open until user presses a key.
        Works on both Windows and Linux/macOS.
        
        Args:
            message: Message to display before waiting (default: generic completion message)
        """
        UIUtils.print_separator("Operation Complete")
        print(message)
        
        if platform.system() == "Windows":
            print("\nPress any key to exit...")
            os.system('pause >nul')
        else:  # Linux/macOS
            print("\nPress Enter to exit...")
            input()
    
    @staticmethod
    def select_dxf_file(dxf_dir: str) -> Optional[str]:
        """
        Display a simple selection menu for DXF files.
        
        Args:
            dxf_dir: Directory containing DXF files
        
        Returns:
            Optional[str]: Path to the selected DXF file, or None if no file selected
        """
        # List DXF files
        dxf_files = [f for f in os.listdir(dxf_dir) if f.lower().endswith('.dxf')]
        
        if not dxf_files:
            print("No DXF files found in the specified directory.")
            return None
        
        print("\nAvailable DXF files:")
        for i, file in enumerate(dxf_files):
            print(f"{i+1}. {file}")
        
        while True:
            try:
                choice = input("\nSelect a file number (or press Enter for default): ")
                if choice.strip() == "":
                    # Default to first file
                    selected_index = 0
                    break
                else:
                    selected_index = int(choice) - 1
                    if 0 <= selected_index < len(dxf_files):
                        break
                    else:
                        print(f"Please enter a number between 1 and {len(dxf_files)}")
            except ValueError:
                print("Please enter a valid number")
        
        selected_file = dxf_files[selected_index]
        return os.path.join(dxf_dir, selected_file)
    
    @staticmethod
    def select_file(
        title: str = "Select File",
        initial_dir: Optional[Union[str, Path]] = None,
        file_types: Optional[List[Tuple[str, str]]] = None,
        save_dialog: bool = False
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Display a file selection dialog appropriate for the platform.
        
        This method attempts to use tkinter file dialogs when available,
        with graceful fallbacks to command-line interfaces.
        
        Args:
            title: Dialog title (default: "Select File")
            initial_dir: Starting directory (default: user's home)
            file_types: List of (description, extension pattern) tuples
            save_dialog: Whether this is a save dialog (default: False)
            
        Returns:
            Tuple: (success, file_path, details) where:
                success: True if a file was selected, False if canceled or error
                file_path: Selected file path if successful, error message otherwise
                details: Dictionary with operation details or error information
        """
        try:
            # Set default initial directory if not specified
            if initial_dir is None:
                initial_dir = str(Path.home())
            
            # Default file types if not specified
            if file_types is None:
                file_types = [
                    ("All Files", "*.*"),
                    ("DXF Files", "*.dxf"),
                    ("CSV Files", "*.csv")
                ]
            
            # Try tkinter first
            try:
                import tkinter as tk
                from tkinter import filedialog
                
                # Format file types for tkinter
                tk_file_types = []
                for desc, pattern in file_types:
                    # Handle multiple extensions in a pattern
                    if ";" in pattern:
                        pattern = pattern.split(";")[0]
                    
                    # Strip asterisk if present
                    if pattern.startswith("*"):
                        pattern = pattern[1:]
                    
                    tk_file_types.append((desc, pattern))
                
                # Create root window (will be hidden)
                root = tk.Tk()
                root.withdraw()
                
                # Show appropriate dialog
                if save_dialog:
                    file_path = filedialog.asksaveasfilename(
                        title=title,
                        initialdir=initial_dir,
                        filetypes=tk_file_types
                    )
                else:
                    file_path = filedialog.askopenfilename(
                        title=title,
                        initialdir=initial_dir,
                        filetypes=tk_file_types
                    )
                
                # Clean up
                root.destroy()
                
                # Check result
                if file_path:
                    # Return the file path directly in the second position
                    return True, file_path, {"file_path": file_path}
                else:
                    return False, "File selection canceled", {"dialog_result": "canceled"}
            
            except ImportError:
                # Tkinter not available, fall back to CLI
                return UIUtils._select_file_cli(title, initial_dir, file_types, save_dialog)
                
        except Exception as e:
            # Fall back to CLI if all GUI methods fail
            return UIUtils._select_file_cli(title, initial_dir, file_types, save_dialog)
    
    @staticmethod
    def _select_file_cli(
        title: str,
        initial_dir: Optional[Union[str, Path]] = None,
        file_types: Optional[List[Tuple[str, str]]] = None,
        save_dialog: bool = False
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Display a simple command-line file selection prompt.
        
        This is the fallback method when GUI options fail.
        
        Args:
            title: Dialog title (shown in prompt)
            initial_dir: Starting directory (suggested in prompt)
            file_types: List of (description, extension pattern) tuples
            save_dialog: Whether this is a save dialog
            
        Returns:
            Tuple: (success, file_path, details)
        """
        try:
            # Set default initial directory if not specified
            if initial_dir is None:
                initial_dir = str(Path.home())
            
            # Default file types if not specified
            if file_types is None:
                file_types = [
                    ("All Files", "*.*"),
                    ("DXF Files", "*.dxf"),
                    ("CSV Files", "*.csv")
                ]
                
            # Print header
            UIUtils.print_separator(title)
            
            # Show file type information
            print("Supported file types:")
            for desc, pattern in file_types:
                print(f"  - {desc} ({pattern})")
            
            # Show operation type
            op_type = "save to" if save_dialog else "open from"
            
            # Main prompt
            file_path = input(f"\nPlease enter path to {op_type} [{initial_dir}]: ")
            
            # Use initial_dir if no input provided
            if not file_path:
                return False, "No file specified", {"error": "No input provided"}
            
            # Handle relative paths
            if not os.path.isabs(file_path):
                file_path = os.path.join(initial_dir, file_path)
            
            # For open dialogs, verify file exists
            if not save_dialog and not os.path.exists(file_path):
                return False, f"File not found: {file_path}", {"error": "File not found", "file_path": file_path}
            
            # Return the file path directly in the second position
            return True, file_path, {"file_path": file_path}
                
        except Exception as e:
            return False, f"CLI file selection failed: {str(e)}", {"error": str(e)}
    
    @staticmethod
    def message_dialog(
        message: str,
        title: str = "Information",
        message_type: str = "info"
    ) -> Tuple[bool, None, Dict[str, Any]]:
        """
        Display an information, warning, or error message dialog.
        
        This method attempts to use tkinter dialog when available
        with fallbacks to console output.
        
        Args:
            message: Dialog message
            title: Dialog title (default: "Information")
            message_type: Type of message ("info", "warning", "error")
            
        Returns:
            Tuple: (success, None, details) where:
                success: True if dialog was shown, False on error
                details: Dictionary with operation details or error information
        """
        try:
            # Try tkinter first
            import tkinter as tk
            from tkinter import messagebox
            
            # Create root window (will be hidden)
            root = tk.Tk()
            root.withdraw()
            
            # Show appropriate dialog type
            if message_type == "warning":
                messagebox.showwarning(title, message)
            elif message_type == "error":
                messagebox.showerror(title, message)
            else:  # info is default
                messagebox.showinfo(title, message)
            
            # Clean up
            root.destroy()
            
            return ErrorHandler.create_success_response(
                message="Dialog shown",
                data={"message_type": message_type}
            )
            
        except ImportError:
            # Fall back to console output
            UIUtils.print_separator(title)
            
            # Format message based on type
            if message_type == "warning":
                print(f"WARNING: {message}")
            elif message_type == "error":
                print(f"ERROR: {message}")
            else:
                print(f"INFO: {message}")
            
            # For non-error messages, prompt to continue
            if message_type != "error":
                input("Press Enter to continue...")
            
            return ErrorHandler.create_success_response(
                message="Dialog shown",
                data={"message_type": message_type}
            )
        except Exception as e:
            # If even the console fallback fails, return error
            return ErrorHandler.from_exception(
                FileError(
                    message="Message dialog failed",
                    severity=ErrorSeverity.ERROR,
                    details={"error": str(e)}
                )
            )