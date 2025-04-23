"""
File locking mechanism for preventing concurrent file access.

This module provides the main FileLock class that handles creating,
managing, and checking file locks to prevent concurrent access.
"""

import os
import time
import datetime
import socket
import logging

# Import helper modules
from FileUtils.lock_detection import check_file_locked
from FileUtils.file_operations import create_lock_file, remove_file_safely


class FileLock:
    """
    Implements a file locking mechanism to prevent concurrent access.
    
    This class creates and manages .lock files alongside target files
    to prevent multiple processes from accessing the same files.
    It also detects if files are currently locked by applications.
    """
    
    def __init__(self, file_path, timeout=1800):
        """
        Initialize the file lock.
        
        Args:
            file_path: Path to the file to lock
            timeout: Seconds after which a lock is considered stale (default: 30 min)
        """
        self.file_path = file_path
        self.lock_file = file_path + ".lock"
        self.timeout = timeout
    
    def check_file_lock(self):
        """
        Check if the target file is locked by another application.
        
        Returns:
            bool: True if file is locked, False otherwise
            str: Process information if available, empty string otherwise
        """
        # Use the helper function from lock_detection module
        return check_file_locked(self.file_path)
    
    # Alias for backward compatibility
    is_file_locked = check_file_lock
    
    def acquire(self):
        """
        Acquire a lock on the file.
        
        Returns:
            bool: True if lock acquired, False if file already locked
        """
        try:
            # First check if file is locked by another application
            file_locked, lock_info = self.check_file_lock()
            if file_locked:
                logging.warning(f"Cannot acquire lock: {self.file_path} is in use: {lock_info}")
                return False
                
            # Check if lock file already exists
            if os.path.exists(self.lock_file):
                # Check if it's a stale lock
                if self._is_stale_lock():
                    # Remove stale lock
                    if not remove_file_safely(self.lock_file):
                        logging.error(f"Failed to remove stale lock: {self.lock_file}")
                        return False
                    logging.info(f"Removed stale lock: {self.lock_file}")
                else:
                    # Lock is still valid
                    logging.info(f"Lock file exists and is still valid: {self.lock_file}")
                    return False
            
            # Create lock file with process info
            lock_info = {
                "pid": os.getpid(),
                "host": socket.gethostname(),
                "time": datetime.datetime.now().isoformat(),
                "file": self.file_path
            }
            
            if create_lock_file(self.lock_file, lock_info):
                logging.info(f"Lock acquired: {self.lock_file}")
                return True
            else:
                logging.error(f"Failed to create lock file: {self.lock_file}")
                return False
        
        except Exception as e:
            logging.error(f"Error acquiring lock: {str(e)}")
            return False
    
    def release(self):
        """
        Release the lock if it exists.
        
        Returns:
            bool: True if released successfully, False otherwise
        """
        if os.path.exists(self.lock_file):
            if remove_file_safely(self.lock_file):
                logging.info(f"Lock released: {self.lock_file}")
                return True
            else:
                logging.error(f"Failed to release lock: {self.lock_file}")
                return False
        return True  # Return True if lock file doesn't exist
    
    def _is_stale_lock(self):
        """
        Check if the lock file is older than the timeout.
        
        Returns:
            bool: True if lock is stale, False otherwise
        """
        try:
            if not os.path.exists(self.lock_file):
                return False
                
            mtime = os.path.getmtime(self.lock_file)
            age = time.time() - mtime
            return age > self.timeout
        except Exception as e:
            logging.error(f"Error checking stale lock: {str(e)}")
            # If we can't check the time, assume it's stale
            return True
