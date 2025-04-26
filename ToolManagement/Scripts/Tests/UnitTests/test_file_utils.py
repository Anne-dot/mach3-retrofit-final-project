"""
Unit tests for the file_utils module.

These tests verify that the file handling utilities work correctly
including file locking, reading, writing, and managing backups.
"""

import unittest
import os
import sys
import time
import csv
import json
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path to import the module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the modules to test
from Utils.file_utils import FileLock, FileUtils


class TestFileLock(unittest.TestCase):
    """Tests for the FileLock class."""
    
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
        # Remove temporary test directory
        shutil.rmtree(self.temp_dir)
    
    def test_acquire_release(self):
        """Test basic lock acquisition and release."""
        # Create a lock
        lock = FileLock(self.test_file)
        
        # Check initial state
        self.assertFalse(lock.acquired)
        self.assertFalse(Path(self.test_file + '.lock').exists())
        
        # Acquire lock
        result = lock.acquire()
        self.assertTrue(result)
        self.assertTrue(lock.acquired)
        self.assertTrue(Path(self.test_file + '.lock').exists())
        
        # Verify lock file content
        with open(self.test_file + '.lock', 'r') as f:
            lock_data = json.loads(f.read())
            self.assertEqual(lock_data['pid'], os.getpid())
        
        # Release lock
        result = lock.release()
        self.assertTrue(result)
        self.assertFalse(lock.acquired)
        self.assertFalse(Path(self.test_file + '.lock').exists())
    
    def test_lock_contention(self):
        """Test behavior when multiple locks are attempted."""
        # Create first lock
        lock1 = FileLock(self.test_file, timeout=1.0)
        self.assertTrue(lock1.acquire())
        
        # Create second lock (should fail to acquire)
        lock2 = FileLock(self.test_file, timeout=1.0)
        result = lock2.acquire()
        self.assertFalse(result)
        self.assertFalse(lock2.acquired)
        
        # Release first lock
        lock1.release()
        
        # Now second lock should be able to acquire
        result = lock2.acquire()
        self.assertTrue(result)
        self.assertTrue(lock2.acquired)
        lock2.release()
    
    def test_stale_lock_handling(self):
        """Test that stale locks are detected and removed."""
        # Create a lock file with old timestamp
        lock_path = Path(self.test_file + '.lock')
        with open(lock_path, 'w') as f:
            lock_data = {
                'pid': 99999,  # Unlikely to be a real process
                'hostname': 'test',
                'created': time.time() - 100  # 100 seconds old
            }
            f.write(json.dumps(lock_data))
        
        # Modify the file time to make it appear old
        os.utime(lock_path, (time.time() - 100, time.time() - 100))
        
        # Create a new lock with short timeout (should detect stale lock)
        lock = FileLock(self.test_file, timeout=5.0)
        result = lock.acquire()
        
        # Should acquire the lock even though lock file exists
        self.assertTrue(result)
        self.assertTrue(lock.acquired)
        
        # Verify lock file content has been updated
        with open(self.test_file + '.lock', 'r') as f:
            lock_data = json.loads(f.read())
            self.assertEqual(lock_data['pid'], os.getpid())
        
        lock.release()
    
    def test_context_manager(self):
        """Test FileLock as a context manager."""
        lock_path = Path(self.test_file + '.lock')
        
        # Use as context manager
        with FileLock(self.test_file) as lock:
            self.assertTrue(lock.acquired)
            self.assertTrue(lock_path.exists())
        
        # Lock should be released after context exit
        self.assertFalse(lock.acquired)
        self.assertFalse(lock_path.exists())


class TestFileUtils(unittest.TestCase):
    """Tests for the FileUtils class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_file.txt")
        self.binary_file = os.path.join(self.temp_dir, "test_binary.bin")
        self.csv_file = os.path.join(self.temp_dir, "test_data.csv")
        
        # Create sample files
        with open(self.test_file, 'w') as f:
            f.write("Test content")
        
        with open(self.binary_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03')
        
        # Create CSV file
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'value'])
            writer.writerow(['item1', '100'])
            writer.writerow(['item2', '200'])
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary test directory
        shutil.rmtree(self.temp_dir)
    
    def test_read_text(self):
        """Test reading text from a file."""
        # Test successful read
        success, message, details = FileUtils.read_text(self.test_file)
        self.assertTrue(success)
        # Extract the content from the details dictionary
        self.assertEqual(details["content"], "Test content")
        self.assertEqual(details["size"], len("Test content"))
        
        # Test reading non-existent file
        non_existent = os.path.join(self.temp_dir, "does_not_exist.txt")
        success, message, details = FileUtils.read_text(non_existent)
        self.assertFalse(success)
        self.assertIn("not found", message)
    
    def test_write_text(self):
        """Test writing text to a file."""
        # Test writing to a new file
        new_file = os.path.join(self.temp_dir, "new_file.txt")
        content = "New content"
        success, message, details = FileUtils.write_text(new_file, content)
        
        self.assertTrue(success)
        self.assertIn("Successfully wrote", message)
        self.assertEqual(details["size"], len(content))
        
        # Verify file content
        with open(new_file, 'r') as f:
            saved_content = f.read()
        self.assertEqual(saved_content, content)
        
        # Test overwriting existing file
        modified_content = "Modified content"
        success, message, details = FileUtils.write_text(new_file, modified_content)
        
        self.assertTrue(success)
        
        # Verify modified content
        with open(new_file, 'r') as f:
            saved_content = f.read()
        self.assertEqual(saved_content, modified_content)
    
    def test_backup_creation(self):
        """Test backup creation when writing files."""
        # Write to a file with backup
        success, message, details = FileUtils.write_text(
            self.test_file, 
            "Updated content",
            create_backup=True
        )
        
        self.assertTrue(success)
        self.assertIn("backup_path", details)
        
        # Verify backup file exists
        backup_path = Path(details["backup_path"])
        self.assertTrue(backup_path.exists())
        
        # Verify backup content
        with open(backup_path, 'r') as f:
            backup_content = f.read()
        self.assertEqual(backup_content, "Test content")
        
        # Verify original file has new content
        with open(self.test_file, 'r') as f:
            new_content = f.read()
        self.assertEqual(new_content, "Updated content")
    
    def test_read_binary(self):
        """Test reading binary data from a file."""
        # Test successful read
        success, data_or_message, details = FileUtils.read_binary(self.binary_file)
        self.assertTrue(success)
        # For binary data, we expect it directly in the second position
        # But we'll check the details dictionary if our implementation uses it
        if isinstance(data_or_message, bytes):
            binary_content = data_or_message
        else:
            binary_content = details.get("content", b'')
        
        self.assertEqual(binary_content, b'\x00\x01\x02\x03')
        
        # Test reading non-existent file
        non_existent = os.path.join(self.temp_dir, "does_not_exist.bin")
        success, data_or_message, details = FileUtils.read_binary(non_existent)
        self.assertFalse(success)
        # Allow for either approach: direct error message or empty bytes
        if isinstance(data_or_message, bytes):
            self.assertEqual(data_or_message, b'')
        else:
            self.assertIn("not found", data_or_message)
    
    def test_write_binary(self):
        """Test writing binary data to a file."""
        # Test writing to a new file
        new_file = os.path.join(self.temp_dir, "new_binary.bin")
        content = b'\x04\x05\x06\x07'
        success, message, details = FileUtils.write_binary(new_file, content)
        
        self.assertTrue(success)
        self.assertIn("Successfully wrote", message)
        self.assertEqual(details["size"], len(content))
        
        # Verify file content
        with open(new_file, 'rb') as f:
            saved_content = f.read()
        self.assertEqual(saved_content, content)
    
    def test_read_csv(self):
        """Test reading data from a CSV file."""
        # Test successful read
        success, message_or_rows, details = FileUtils.read_csv(self.csv_file)
        
        self.assertTrue(success)
        
        # Get rows either directly or from details
        if isinstance(message_or_rows, list):
            rows = message_or_rows
        else:
            rows = details.get("rows", [])
        
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["name"], "item1")
        self.assertEqual(rows[0]["value"], "100")
        self.assertEqual(rows[1]["name"], "item2")
        self.assertEqual(rows[1]["value"], "200")
        
        # Test reading non-existent file
        non_existent = os.path.join(self.temp_dir, "does_not_exist.csv")
        success, message_or_rows, details = FileUtils.read_csv(non_existent)
        self.assertFalse(success)
        
        # Get rows either directly or from details
        if isinstance(message_or_rows, list):
            rows = message_or_rows
        else:
            rows = details.get("rows", [])
            
        self.assertEqual(len(rows), 0)
    
    def test_write_csv(self):
        """Test writing data to a CSV file."""
        # Test writing to a new file
        new_file = os.path.join(self.temp_dir, "new_data.csv")
        rows = [
            {"name": "item3", "value": "300", "extra": "note1"},
            {"name": "item4", "value": "400", "extra": "note2"}
        ]
        
        success, message, details = FileUtils.write_csv(new_file, rows)
        
        self.assertTrue(success)
        self.assertIn("Successfully wrote", message)
        self.assertEqual(details["count"], 2)
        
        # Read back to verify
        with open(new_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            saved_rows = list(reader)
        
        self.assertEqual(len(saved_rows), 2)
        self.assertEqual(saved_rows[0]["name"], "item3")
        self.assertEqual(saved_rows[0]["value"], "300")
        self.assertEqual(saved_rows[0]["extra"], "note1")
        self.assertEqual(saved_rows[1]["name"], "item4")
        self.assertEqual(saved_rows[1]["value"], "400")
        self.assertEqual(saved_rows[1]["extra"], "note2")
    
    def test_ensure_backup_dir(self):
        """Test creating and managing a backup directory."""
        # Test creating backup directory
        success, message_or_path, details = FileUtils.ensure_backup_dir(self.temp_dir)
        
        self.assertTrue(success)
        
        # Get backup directory path either directly or from details
        if isinstance(message_or_path, (str, Path)):
            # If it's a string that starts with "Backup" it's likely a message
            if isinstance(message_or_path, str) and message_or_path.startswith("Backup"):
                backup_dir = Path(details.get("backup_dir", ""))
            else:
                backup_dir = Path(message_or_path)
        else:
            backup_dir = Path(details.get("backup_dir", ""))
            
        self.assertEqual(backup_dir, Path(self.temp_dir) / "backups")
        self.assertTrue(Path(self.temp_dir, "backups").exists())
        
        # Test backup management
        # Create test files in backup dir
        backup_files = []
        for i in range(25):  # More than default max_backups (20)
            backup_file = Path(self.temp_dir, "backups", f"backup_{i}.txt")
            with open(backup_file, 'w') as f:
                f.write(f"Backup content {i}")
            backup_files.append(backup_file)
            # Add a small delay to ensure different modification times
            time.sleep(0.01)
        
        # Ensure backup dir with management
        success, message_or_path, details = FileUtils.ensure_backup_dir(
            self.temp_dir, max_backups=20
        )
        
        self.assertTrue(success)
        
        # Should have removed the 5 oldest backup files
        remaining_files = list(Path(self.temp_dir, "backups").glob("*"))
        self.assertEqual(len(remaining_files), 20)
        
        # The oldest 5 files should be gone
        for i in range(5):
            self.assertFalse(Path(self.temp_dir, "backups", f"backup_{i}.txt").exists())
        
        # The newest 20 files should still exist
        for i in range(5, 25):
            self.assertTrue(Path(self.temp_dir, "backups", f"backup_{i}.txt").exists())


if __name__ == '__main__':
    unittest.main()
