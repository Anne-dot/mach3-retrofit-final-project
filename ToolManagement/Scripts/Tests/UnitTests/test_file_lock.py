"""
Unit tests for file_lock.py functionality.

This module contains tests for the FileLock class, verifying lock acquisition,
release, stale lock detection, and proper handling of error conditions.
"""

import os
import sys
import time
import shutil
import unittest

# Add parent directory to path so we can import from Backup
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from Backups.file_lock import FileLock


class TestFileLock(unittest.TestCase):
    """
    Test suite for FileLock class.
    
    This class tests the core functionality of the FileLock class,
    including basic operations and edge cases.
    """
    
    def setUp(self):
        """
        Set up test environment before each test.
        
        Creates a test directory and file for locking operations.
        """
        # Create test directory if it doesn't exist
        self.test_dir = os.path.join(os.path.dirname(__file__), 'test_files')
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Create test file
        self.test_file = os.path.join(self.test_dir, 'test_lock_file.txt')
        with open(self.test_file, 'w') as f:
            f.write('Test content')
        
        # Create file lock
        self.lock = FileLock(self.test_file)
    
    def test_acquire(self):
        """
        Test basic lock acquisition.
        
        Verifies that a lock can be acquired on a file and that
        the lock file is created.
        """
        # Should be able to acquire lock
        self.assertTrue(self.lock.acquire())
        
        # Lock file should exist
        self.assertTrue(os.path.exists(self.lock.lock_file))
        
        # Release lock for next tests
        self.lock.release()
    
    def test_multiple_locks(self):
        """
        Test that second lock fails when file is already locked.
        
        Verifies the core concurrency protection by ensuring a second
        lock cannot be acquired while a file is already locked.
        """
        # Acquire first lock
        self.assertTrue(self.lock.acquire())
        
        # Create second lock object
        second_lock = FileLock(self.test_file)
        
        # Second lock should fail
        self.assertFalse(second_lock.acquire())
        
        # Release first lock
        self.lock.release()
    
    def test_release(self):
        """
        Test lock release functionality.
        
        Verifies that locks can be properly released and that the
        release operation is idempotent (can be called multiple times).
        """
        # Acquire lock
        self.lock.acquire()
        
        # Release should succeed
        self.assertTrue(self.lock.release())
        
        # Lock file should be gone
        self.assertFalse(os.path.exists(self.lock.lock_file))
        
        # Releasing again should still return true (idempotent)
        self.assertTrue(self.lock.release())
    
    def test_stale_lock(self):
        """
        Test stale lock detection and handling.
        
        Verifies that old lock files are correctly identified as stale
        and automatically removed when a new lock is attempted.
        """
        # Create a lock file manually with old timestamp
        with open(self.lock.lock_file, 'w') as f:
            f.write('Stale lock')
        
        # Set modification time to 2 hours ago (definitely stale)
        stale_time = time.time() - 7200  # 2 hours ago
        os.utime(self.lock.lock_file, (stale_time, stale_time))
        
        # Should be able to acquire lock despite existing lock file
        self.assertTrue(self.lock.acquire())
        
        # Release lock
        self.lock.release()
    
    def test_error_handling(self):
        """
        Test error handling during lock operations.
        
        Verifies that the FileLock class gracefully handles error conditions
        like permission issues or unexpected file system states.
        """
        # Create a directory with same name as lock file to cause error
        os.makedirs(self.lock.lock_file, exist_ok=True)
        
        # Acquire should handle error gracefully
        self.assertFalse(self.lock.acquire())
        
        # Release should handle error gracefully 
        self.assertFalse(self.lock.release())
        
        # Clean up directory
        if os.path.exists(self.lock.lock_file):
            shutil.rmtree(self.lock.lock_file)
    
    def tearDown(self):
        """
        Clean up after each test.
        
        Removes any locks and test files created during testing.
        """
        # Release lock if it exists
        if hasattr(self, 'lock'):
            self.lock.release()
        
        # Clean up test directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)


if __name__ == "__main__":
    unittest.main()