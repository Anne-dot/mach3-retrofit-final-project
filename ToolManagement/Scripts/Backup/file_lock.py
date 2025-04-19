"""
File locking mechanism for preventing concurrent file access.

This module provides a simple file-based locking system that creates 
.lock files to prevent multiple processes from accessing the same 
file simultaneously. It includes automatic handling of stale locks.
"""

import os
import time
import datetime
import socket
import logging


class FileLock:
    """
    Implements a simple file-based locking mechanism.
    
    This class creates and manages .lock files alongside the target file
    to prevent concurrent access by multiple processes. It also handles
    stale locks that might be left if a process terminates abnormally.
    
    Attributes:
        file_path: Path to the file being locked
        lock_file: Path to the lock file (file_path + ".lock")
        timeout: Seconds after which a lock is considered stale
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
    
    def acquire(self):
        """
        Acquire a lock on the file.
        
        Returns:
            bool: True if lock acquired, False if file already locked
        """
        try:
            # Check if lock already exists
            if os.path.exists(self.lock_file):
                # Check if it's a stale lock
                if self._is_stale_lock():
                    # Remove stale lock and create new one
                    try:
                        os.remove(self.lock_file)
                        logging.info(f"Removed stale lock: {self.lock_file}")
                    except Exception as e:
                        logging.error(f"Failed to remove stale lock: {str(e)}")
                        return False
                else:
                    # Lock is still valid
                    return False
            
            # Create lock file with process info
            with open(self.lock_file, 'w') as f:
                f.write(f"PID: {os.getpid()}\n")
                f.write(f"Host: {socket.gethostname()}\n")
                f.write(f"Time: {datetime.datetime.now().isoformat()}\n")
                f.write(f"File: {self.file_path}\n")
            
            logging.info(f"Lock acquired: {self.lock_file}")
            return True
        
        except Exception as e:
            logging.error(f"Error acquiring lock: {str(e)}")
            return False
    
    def release(self):
        """
        Release the lock if it exists.
        
        Returns:
            bool: True if released successfully, False otherwise
        """
        try:
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
                logging.info(f"Lock released: {self.lock_file}")
                return True
            return True  # Return True if lock file doesn't exist
        except Exception as e:
            logging.error(f"Error releasing lock: {str(e)}")
            return False
    
    def _is_stale_lock(self):
        """
        Check if the lock file is older than the timeout.
        
        Returns:
            bool: True if lock is stale, False otherwise
        """
        try:
            mtime = os.path.getmtime(self.lock_file)
            age = time.time() - mtime
            return age > self.timeout
        except Exception as e:
            logging.error(f"Error checking stale lock: {str(e)}")
            # If we can't check the time, assume it's stale
            return True


if __name__ == "__main__":
    """Command-line interface for testing."""
    import argparse
    import sys
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="File locking utility")
    parser.add_argument("--acquire", help="Acquire lock on specified file")
    parser.add_argument("--release", help="Release lock on specified file")
    parser.add_argument("--status", help="Check lock status of specified file")
    parser.add_argument("--status-file", help="File to write results to")
    
    args = parser.parse_args()
    result = None
    
    if args.acquire:
        locker = FileLock(args.acquire)
        success = locker.acquire()
        result = (success, "Lock acquired" if success else "Failed to acquire lock")
    
    elif args.release:
        locker = FileLock(args.release)
        success = locker.release()
        result = (success, "Lock released" if success else "Failed to release lock")
    
    elif args.status:
        locker = FileLock(args.status)
        is_locked = os.path.exists(locker.lock_file)
        is_stale = locker._is_stale_lock() if is_locked else False
        status = "Locked" if is_locked and not is_stale else "Unlocked"
        if is_locked and is_stale:
            status = "Stale lock"
        result = (True, status)
    
    # Write result to status file if specified
    if args.status_file and result:
        success, message = result
        try:
            with open(args.status_file, 'w') as f:
                f.write("SUCCESS\n" if success else "ERROR\n")
                f.write(message)
        except Exception as e:
            print(f"ERROR: Failed to write status file: {str(e)}")
    
    # Print result to console
    if result:
        success, message = result
        print(f"{'SUCCESS' if success else 'ERROR'}: {message}")
        sys.exit(0 if success else 1)
    else:
        print("ERROR: No operation specified")
        sys.exit(1)