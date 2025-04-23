"""
File lock detection test script for tool-data.csv

This script attempts to detect if a file is locked by another program
using multiple detection methods. Specifically designed to detect
when Notepad, Wordpad, or other text editors have a file open.

Usage:
    python file_lock_detection.py [path_to_csv_file]
"""

import os
import sys
import ctypes
from ctypes import wintypes
import time

# Default file path - can be overridden by command line argument
DEFAULT_FILE_PATH = r"C:\Mach3\ToolManagement\Data\tool-data.csv"

def debug_print(message, level="INFO"):
    """
    Print debug message with timestamp and level
    
    Levels:
    - INFO: Normal information
    - DEBUG: Detailed debugging information
    - ERROR: Error messages
    - SUCCESS: Success messages
    """
    level_colors = {
        "INFO": "",
        "DEBUG": "\033[36m",  # Cyan
        "ERROR": "\033[91m",  # Red
        "SUCCESS": "\033[92m", # Green
        "WARNING": "\033[93m"  # Yellow
    }
    reset = "\033[0m"
    
    # Format: [Time] [LEVEL] Message
    color = level_colors.get(level, "")
    print(f"[{time.strftime('%H:%M:%S')}] {color}[{level}]{reset} {message}")

def method1_rename_test(file_path):
    """
    Method 1: Test if file is locked by trying to rename it
    
    This works because most Windows applications put a lock on files
    that prevents renaming while the file is open.
    """
    debug_print("Testing Method 1: Rename test", "DEBUG")
    debug_print(f"Attempting to rename {file_path} temporarily", "DEBUG")
    
    try:
        temp_path = file_path + ".tmp"
        debug_print(f"Renaming {file_path} -> {temp_path}", "DEBUG")
        os.rename(file_path, temp_path)
        
        debug_print(f"Renaming back {temp_path} -> {file_path}", "DEBUG")
        os.rename(temp_path, file_path)
        
        debug_print("Rename operation completed successfully", "SUCCESS")
        debug_print("RESULT: File is NOT locked (rename succeeded)", "SUCCESS")
        return False  # File is not locked
    except PermissionError as e:
        debug_print(f"PermissionError occurred: {e}", "ERROR")
        debug_print("RESULT: File IS locked (rename failed with PermissionError)", "WARNING")
        return True  # File is locked
    except OSError as e:
        debug_print(f"OSError occurred: {e}", "ERROR")
        debug_print("RESULT: File might be locked (rename failed with OSError)", "WARNING")
        return True  # Assume locked on any OS error
    except Exception as e:
        debug_print(f"Unexpected exception: {str(e)}", "ERROR")
        debug_print("RESULT: Status unclear due to unexpected error", "ERROR")
        return False  # Unclear if locked

def method2_exclusive_open(file_path):
    """
    Method 2: Try to open file with exclusive access
    
    This attempts to open the file in a mode that would fail
    if another program has the file open.
    """
    debug_print("Testing Method 2: Exclusive open test", "DEBUG")
    debug_print(f"Attempting to open {file_path} with exclusive access", "DEBUG")
    
    try:
        # Try to open the file in read+ mode
        debug_print("Opening file in r+ mode (read/write)", "DEBUG")
        with open(file_path, 'r+') as f:
            debug_print("Successfully opened file in r+ mode", "SUCCESS")
            
            # Check if we can get exclusive access
            try:
                debug_print("Attempting to use Windows API for exclusive lock", "DEBUG")
                # Get the file handle
                msvcrt = ctypes.cdll.msvcrt
                file_handle = msvcrt._get_osfhandle(f.fileno())
                debug_print(f"Got file handle: {file_handle}", "DEBUG")
                
                # Constants for LockFileEx
                LOCKFILE_EXCLUSIVE_LOCK = 0x00000002
                LOCKFILE_FAIL_IMMEDIATELY = 0x00000001
                
                # Try to lock the file
                debug_print("Calling LockFileEx Windows API", "DEBUG")
                LockFileEx = ctypes.windll.kernel32.LockFileEx
                overlapped = wintypes.OVERLAPPED()
                result = LockFileEx(
                    file_handle, 
                    LOCKFILE_EXCLUSIVE_LOCK | LOCKFILE_FAIL_IMMEDIATELY, 
                    0, 0xFFFFFFFF, 0, 
                    ctypes.byref(overlapped)
                )
                
                debug_print(f"LockFileEx result: {result}", "DEBUG")
                if result == 0:
                    debug_print("Windows API reported file is locked", "WARNING")
                    debug_print("RESULT: File IS locked (Windows LockFileEx failed)", "WARNING")
                    return True
                else:
                    debug_print("Windows API lock succeeded", "SUCCESS")
                    debug_print("RESULT: File is NOT locked (Windows LockFileEx succeeded)", "SUCCESS")
                    return False
                    
            except Exception as e:
                debug_print(f"Error during Windows API call: {str(e)}", "ERROR")
                debug_print("RESULT: Assuming file is locked due to API error", "WARNING")
                return True  # Assume locked on any exception
    except PermissionError as e:
        debug_print(f"PermissionError occurred: {e}", "ERROR")
        debug_print("RESULT: File IS locked (exclusive open failed with PermissionError)", "WARNING")
        return True
    except IOError as e:
        debug_print(f"IOError occurred: {e}", "ERROR")
        debug_print("RESULT: File might be locked (open failed with IOError)", "WARNING")
        return True
    except Exception as e:
        debug_print(f"Unexpected exception: {str(e)}", "ERROR")
        debug_print("RESULT: Status unclear due to unexpected error", "ERROR")
        return False

def method3_write_test(file_path):
    """
    Method 3: Try to create a temporary file in the same directory
    
    Some applications lock the entire directory or prevent other writes.
    """
    debug_print("Testing Method 3: Write test in directory", "DEBUG")
    
    dir_path = os.path.dirname(file_path)
    test_path = os.path.join(dir_path, "_lock_test_temp.txt")
    
    debug_print(f"Checking directory: {dir_path}", "DEBUG")
    debug_print(f"Will attempt to create temporary file: {test_path}", "DEBUG")
    
    try:
        debug_print("Attempting to create and write to temporary file", "DEBUG")
        with open(test_path, 'w') as f:
            f.write("Lock test")
            debug_print("Successfully wrote to temporary file", "SUCCESS")
        
        debug_print("Attempting to remove temporary file", "DEBUG")
        os.remove(test_path)
        debug_print("Successfully removed temporary file", "SUCCESS")
        
        debug_print("RESULT: Directory is writable, file might not be locked", "SUCCESS")
        return False
    except PermissionError as e:
        debug_print(f"PermissionError occurred: {e}", "ERROR")
        debug_print("RESULT: Directory has write protection, file might be locked", "WARNING")
        return True
    except OSError as e:
        debug_print(f"OSError occurred: {e}", "ERROR")
        debug_print("RESULT: Could not create temp file, directory might be locked", "WARNING")
        return True
    except Exception as e:
        debug_print(f"Unexpected exception: {str(e)}", "ERROR")
        debug_print("RESULT: Status unclear due to unexpected error", "ERROR")
        return False

def is_file_locked(file_path):
    """
    Check if a file is locked using multiple detection methods
    
    Returns:
        bool: True if file appears to be locked, False otherwise
    """
    debug_print("=" * 40, "INFO")
    debug_print(f"STARTING LOCK DETECTION FOR: {file_path}", "INFO")
    debug_print("=" * 40, "INFO")
    
    # Check if file exists first
    if not os.path.exists(file_path):
        debug_print(f"FILE DOES NOT EXIST: {file_path}", "ERROR")
        return False
    
    debug_print(f"File exists, proceeding with lock detection tests", "INFO")
    
    # Run all methods and combine results
    debug_print("-" * 40, "INFO")
    debug_print("RUNNING TEST METHOD 1: Rename Test", "INFO")
    locked_1 = method1_rename_test(file_path)
    debug_print(f"Method 1 result: {'LOCKED' if locked_1 else 'NOT LOCKED'}", 
               "WARNING" if locked_1 else "SUCCESS")
    
    debug_print("-" * 40, "INFO")
    debug_print("RUNNING TEST METHOD 2: Exclusive Open Test", "INFO")
    locked_2 = method2_exclusive_open(file_path)
    debug_print(f"Method 2 result: {'LOCKED' if locked_2 else 'NOT LOCKED'}", 
               "WARNING" if locked_2 else "SUCCESS")
    
    debug_print("-" * 40, "INFO")
    debug_print("RUNNING TEST METHOD 3: Directory Write Test", "INFO")
    locked_3 = method3_write_test(file_path)
    debug_print(f"Method 3 result: {'LOCKED' if locked_3 else 'NOT LOCKED'}", 
               "WARNING" if locked_3 else "SUCCESS")
    
    debug_print("-" * 40, "INFO")
    debug_print("RUNNING TEST METHOD 4: Copy Test", "INFO")
    locked_4 = method4_copyfile_test(file_path)
    debug_print(f"Method 4 result: {'LOCKED' if locked_4 else 'NOT LOCKED'}", 
               "WARNING" if locked_4 else "SUCCESS")
    
    debug_print("-" * 40, "INFO")
    debug_print("RUNNING TEST METHOD 5: Windows API Test", "INFO")
    locked_5 = method5_mswindows_test(file_path)
    debug_print(f"Method 5 result: {'LOCKED' if locked_5 else 'NOT LOCKED'}", 
               "WARNING" if locked_5 else "SUCCESS")
    
    # If any method says it's locked, consider it locked
    result = locked_1 or locked_2 or locked_3 or locked_4 or locked_5
    
    # Create a summary of which methods detected locks
    methods_locked = []
    if locked_1: methods_locked.append("Rename")
    if locked_2: methods_locked.append("Exclusive Open")
    if locked_3: methods_locked.append("Directory Write")
    if locked_4: methods_locked.append("Copy")
    if locked_5: methods_locked.append("Windows API")
    
    debug_print("=" * 40, "INFO")
    if result:
        debug_print(f"FINAL RESULT: FILE IS LOCKED", "WARNING")
        if methods_locked:
            debug_print(f"Lock detected by methods: {', '.join(methods_locked)}", "WARNING")
            # Give more information about which app might be locking
            debug_print(f"File is likely open in a program like Notepad, Wordpad, or another text editor", "WARNING")
            debug_print(f"Please close the file in all applications before continuing", "WARNING")
        else:
            debug_print(f"Lock detection succeeded but no specific method identified the lock", "ERROR")
    else:
        debug_print(f"FINAL RESULT: FILE IS NOT LOCKED", "SUCCESS")
        debug_print(f"All detection methods indicate file is accessible", "SUCCESS")
    debug_print("=" * 40, "INFO")
    
    return result

def method4_copyfile_test(file_path):
    """
    Method 4: Try to copy the file
    
    Some applications allow renames but block copy operations.
    This provides an additional detection method.
    """
    debug_print("Testing Method 4: Copy file test", "DEBUG")
    debug_print(f"Attempting to copy {file_path}", "DEBUG")
    
    try:
        temp_path = file_path + ".copy"
        debug_print(f"Copying {file_path} -> {temp_path}", "DEBUG")
        
        with open(file_path, 'rb') as src:
            with open(temp_path, 'wb') as dst:
                dst.write(src.read())
                debug_print("Successfully copied file contents", "SUCCESS")
        
        debug_print("Removing temporary copy", "DEBUG")
        os.remove(temp_path)
        debug_print("Successfully removed copy", "SUCCESS")
        
        debug_print("RESULT: File is NOT locked (copy succeeded)", "SUCCESS")
        return False  # File is not locked
    except PermissionError as e:
        debug_print(f"PermissionError occurred: {e}", "ERROR")
        debug_print("RESULT: File IS locked (copy failed with PermissionError)", "WARNING")
        return True  # File is locked
    except IOError as e:
        debug_print(f"IOError occurred: {e}", "ERROR")
        debug_print("RESULT: File might be locked (copy failed with IOError)", "WARNING")
        return True  # Assume locked
    except Exception as e:
        debug_print(f"Unexpected exception: {str(e)}", "ERROR")
        debug_print("RESULT: Status unclear due to unexpected error", "ERROR")
        return False  # Unclear if locked

def method5_mswindows_test(file_path):
    """
    Method 5: Try Windows-specific API approach for detecting sharing violations
    
    Uses ctypes to call Windows APIs to check for specific sharing violation errors.
    """
    debug_print("Testing Method 5: Windows API sharing violation test", "DEBUG")
    debug_print(f"Checking for sharing violations on {file_path}", "DEBUG")
    
    try:
        # Try to open with specific sharing flags
        CREATE_NEW = 1
        OPEN_EXISTING = 3
        GENERIC_READ = 0x80000000
        GENERIC_WRITE = 0x40000000
        FILE_SHARE_READ = 0x00000001
        FILE_SHARE_WRITE = 0x00000002
        
        CreateFile = ctypes.windll.kernel32.CreateFileW
        CloseHandle = ctypes.windll.kernel32.CloseHandle
        
        debug_print("Calling Windows CreateFileW API", "DEBUG")
        handle = CreateFile(
            file_path,
            GENERIC_READ | GENERIC_WRITE,
            0,  # No sharing
            None,
            OPEN_EXISTING,
            0,
            None
        )
        
        debug_print(f"CreateFileW returned handle: {handle}", "DEBUG")
        
        # INVALID_HANDLE_VALUE is typically -1
        if handle == -1 or handle == 0xFFFFFFFFFFFFFFFF:
            error = ctypes.windll.kernel32.GetLastError()
            debug_print(f"Windows API error code: {error}", "DEBUG")
            
            # ERROR_SHARING_VIOLATION is 32
            if error == 32:
                debug_print("Windows API detected sharing violation (error 32)", "WARNING")
                debug_print("RESULT: File IS locked (sharing violation detected)", "WARNING")
                return True
            else:
                debug_print(f"Windows API failed with error code: {error}", "ERROR")
                debug_print("RESULT: Status unclear, but file might be locked", "WARNING")
                return True
        else:
            debug_print("Successfully opened file with exclusive access", "SUCCESS")
            CloseHandle(handle)
            debug_print("RESULT: File is NOT locked (exclusive access succeeded)", "SUCCESS")
            return False
    except Exception as e:
        debug_print(f"Exception during Windows API test: {str(e)}", "ERROR")
        debug_print("RESULT: Status unclear due to API exception", "ERROR")
        return False

if __name__ == "__main__":
    # Get file path from command line or use default
    file_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FILE_PATH
    
    # Setup colored output format
    debug_print("=" * 60, "INFO")
    debug_print("FILE LOCK DETECTION TEST SCRIPT", "INFO")
    debug_print("=" * 60, "INFO")
    debug_print(f"Target file: {file_path}", "INFO")
    debug_print(f"Date/Time: {time.strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
    debug_print(f"Python version: {sys.version}", "INFO")
    debug_print("-" * 60, "INFO")
    
    # First check if file exists
    if not os.path.exists(file_path):
        debug_print(f"ERROR: File does not exist: {file_path}", "ERROR")
        sys.exit(1)
    
    # Run the main detection function
    is_locked = is_file_locked(file_path)
    
    # Bonus: Add the additional methods if needed
    if not is_locked:
        debug_print("\nRunning additional detection methods for verification...", "INFO")
        debug_print("-" * 60, "INFO")
        
        debug_print("RUNNING TEST METHOD 4: Copy Test", "INFO")
        locked_4 = method4_copyfile_test(file_path)
        
        debug_print("-" * 60, "INFO")
        debug_print("RUNNING TEST METHOD 5: Windows API Test", "INFO")
        locked_5 = method5_mswindows_test(file_path)
        
        # Check if additional methods found a lock
        if locked_4 or locked_5:
            debug_print("\nWARNING: Basic methods did not detect lock, but additional methods did!", "WARNING")
            is_locked = True
    
    # Print final summary
    print("\n" + "=" * 60)
    if is_locked:
        print(f"\033[93m[WARNING] FILE IS LOCKED: {file_path}\033[0m")
        print("The file appears to be open in another program like Notepad or Wordpad.")
    else:
        print(f"\033[92m[SUCCESS] FILE IS NOT LOCKED: {file_path}\033[0m")
        print("The file is available for operations like backup or modification.")
    print("=" * 60)
    
    print("\nInstructions for testing:")
    print("1. Run this script when the file is NOT open in any program")
    print("2. Open the file in Notepad and run this script again")
    print("3. Compare the results")
    print("4. Try with other editors like Wordpad, VSCode, etc.")
    print("\nIf you need to integrate this into your backup system:")
    print("1. Copy the successful detection methods to your file_lock.py module")
    print("2. Update your backup_manager.py to use these improved lock detection methods")
    print("3. Test thoroughly in your production environment")
