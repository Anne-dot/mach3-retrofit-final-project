"""
FileUtils package for FileLock system.

This package contains utility modules for file operations and lock detection
used by the main FileLock class.
"""

# Import key functions to make them available at package level
from .lock_detection import check_file_locked
from .file_operations import create_lock_file, remove_file_safely, backup_file

# Version information
__version__ = "1.0.0"
