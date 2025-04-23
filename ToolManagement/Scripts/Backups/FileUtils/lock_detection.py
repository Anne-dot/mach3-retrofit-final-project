"""
Lock detection utilities for checking if files are locked by other applications.

This module provides functions to detect if files are currently locked
or in use by other applications, using various methods optimized for
Windows environments.
"""

import os
import logging
import subprocess


def check_file_locked(file_path):
    """
    Check if a file is locked by another application using multiple detection methods.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        bool: True if file is locked, False otherwise
        str: Information about what's locking the file, or empty string
    """
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    # Try multiple detection methods in order of reliability
    
    # Method 1: Rename test - most reliable way to detect Windows locks
    is_locked, info = check_rename_lock(file_path)
    if is_locked:
        return True, info
        
    # Method 2: Write test - try to open and modify the file
    is_locked, info = check_write_lock(file_path)
    if is_locked:
        return True, info
    
    # Method 3: Windows command line tools (if available)
    is_locked, info = check_windows_handles(file_path)
    if is_locked:
        return True, info
    
    # All tests passed, file is not locked
    return False, ""


def check_rename_lock(file_path):
    """
    Check if a file is locked by attempting to rename it.
    
    This is the most reliable method for detecting locks in Windows,
    as even applications that allow file sharing will prevent renaming.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        bool: True if file is locked, False otherwise
        str: Error message if locked
    """
    try:
        # Only attempt if file exists
        if not os.path.exists(file_path):
            return False, "File does not exist"
            
        # Try to rename the file temporarily
        temp_name = file_path + ".tmp"
        os.rename(file_path, temp_name)
        os.rename(temp_name, file_path)
        return False, ""
    except (IOError, OSError) as e:
        return True, f"File is locked (rename test): {str(e)}"
    except Exception as e:
        logging.warning(f"Error in rename lock check: {str(e)}")
        return False, ""


def check_write_lock(file_path):
    """
    Check if a file is locked by attempting to open and modify it.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        bool: True if file is locked, False otherwise
        str: Error message if locked
    """
    try:
        # Only attempt if file exists and has content
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return False, ""
            
        # Try to open the file for reading and writing
        with open(file_path, 'r+b') as f:
            # Save current position
            pos = f.tell()
            
            # Read first byte
            data = f.read(1)
            
            # Go back to position
            f.seek(pos)
            
            # Write the same data back (no actual change)
            if data:
                f.write(data)
                
        return False, ""
    except (IOError, OSError) as e:
        return True, f"File is locked (write test): {str(e)}"
    except Exception as e:
        logging.warning(f"Error in write lock check: {str(e)}")
        return False, ""


def check_windows_handles(file_path):
    """
    Check if a file has open handles using Windows command line tools.
    
    Note: This may require admin privileges to work correctly.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        bool: True if file has open handles, False otherwise
        str: Process information if available
    """
    try:
        # Absolute path is needed for command line tools
        abs_path = os.path.abspath(file_path)
        
        # Try with openfiles command (requires admin)
        cmd = f'openfiles /query /fo csv | findstr /i "{abs_path}"'
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
            if output.strip():
                return True, f"File has open handles: {output.strip()}"
        except subprocess.CalledProcessError:
            # Command failed - either no open files or not running as admin
            pass
            
        return False, ""
    except Exception as e:
        logging.warning(f"Error in Windows handle check: {str(e)}")
        return False, ""
