#!/usr/bin/env python3
"""
Manual test script for backup_manager.py

This script provides a simple interface to test the backup_manager.py 
functionality through manual verification steps.
"""

import os
import sys
import shutil
import time
import argparse
import tempfile

# Ensure we can import from the Backups directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Backups'))

from backup_manager import BackupManager, BackupRotation

# Setup test paths
TEST_DIR = tempfile.mkdtemp(prefix="backup_test_")
BACKUP_DIR = os.path.join(TEST_DIR, "backups")
TEST_FILE = os.path.join(TEST_DIR, "test_file.csv")

def create_test_file(content="test,data\n1,value1"):
    """Create a test file with sample content"""
    os.makedirs(os.path.dirname(TEST_FILE), exist_ok=True)
    with open(TEST_FILE, 'w') as f:
        f.write(content)
    print(f"Created test file at: {TEST_FILE}")

def cleanup_test_files():
    """Remove all test files and directories"""
    try:
        shutil.rmtree(TEST_DIR)
        print(f"Cleaned up test directory: {TEST_DIR}")
    except Exception as e:
        print(f"Error cleaning up: {e}")

def test_backup_creation():
    """Test creating backups"""
    print("\n=== Testing Backup Creation ===")
    
    # Create test file
    create_test_file()
    
    # Create backup manager
    backup_mgr = BackupManager(BACKUP_DIR)
    
    # Create backup
    result = backup_mgr.create_backup(TEST_FILE)
    
    if result['status'] == 'SUCCESS':
        print(f"SUCCESS: {result['message']}")
        print(f"  Backup created at: {result['backup_path']}")
    else:
        print(f"ERROR: {result['message']}")
    
    # List backups
    backups = backup_mgr.list_backups()
    print(f"\nFound {len(backups)} backup(s):")
    for i, backup in enumerate(backups, 1):
        print(f"  {i}. {backup['filename']}")
    
    return result

def test_backup_rotation():
    """Test backup rotation (creating multiple backups)"""
    print("\n=== Testing Backup Rotation ===")
    
    # Create test file
    create_test_file()
    
    # Create backup manager with small max_backups
    backup_mgr = BackupManager(BACKUP_DIR, max_backups=3)
    
    # Create multiple backups
    for i in range(5):
        # Modify file content to make it unique
        with open(TEST_FILE, 'w') as f:
            f.write(f"test,data\n{i},value{i}")
            
        # Create backup
        result = backup_mgr.create_backup(TEST_FILE)
        print(f"Created backup {i+1}: {result['message']}")
        
        # Small delay to ensure different timestamps
        time.sleep(1)
    
    # List backups (should be only 3)
    backups = backup_mgr.list_backups()
    print(f"\nFound {len(backups)} backup(s) after rotation:")
    for i, backup in enumerate(backups, 1):
        print(f"  {i}. {backup['filename']}")
    
    if len(backups) == 3:
        print(f"SUCCESS: Rotation worked correctly (kept 3 newest backups)")
    else:
        print(f"ERROR: Rotation did not work correctly (found {len(backups)} backups)")
    
    return len(backups) == 3

def test_restore():
    """Test restoring from backup"""
    print("\n=== Testing Restore ===")
    
    # Create test file with initial content
    initial_content = "initial,content\n1,value1"
    create_test_file(initial_content)
    
    # Create backup manager
    backup_mgr = BackupManager(BACKUP_DIR)
    
    # Create backup
    result = backup_mgr.create_backup(TEST_FILE)
    backup_path = result['backup_path']
    print(f"Created backup: {os.path.basename(backup_path)}")
    
    # Modify original file
    modified_content = "modified,content\n2,value2"
    with open(TEST_FILE, 'w') as f:
        f.write(modified_content)
    print(f"Modified original file")
    
    # Restore from backup
    restore_path = TEST_FILE + ".restored"
    restore_result = backup_mgr.restore_from_backup(backup_path, restore_path)
    
    if restore_result['status'] == 'SUCCESS':
        print(f"SUCCESS: {restore_result['message']}")
        
        # Verify content
        with open(restore_path, 'r') as f:
            restored_content = f.read()
        
        if restored_content == initial_content:
            print(f"Restored content matches original")
        else:
            print(f"Restored content does not match original")
    else:
        print(f"ERROR: {restore_result['message']}")
    
    return restore_result['status'] == 'SUCCESS'

def test_file_locking():
    """Test file locking during backup operations"""
    print("\n=== Testing File Locking ===")
    
    # Create test file
    create_test_file()
    
    # Create backup manager
    backup_mgr = BackupManager(BACKUP_DIR)
    
    # Create first backup
    result1 = backup_mgr.create_backup(TEST_FILE)
    print(f"First backup: {result1['message']}")
    
    # Simulate concurrent access by creating a second backup manager
    backup_mgr2 = BackupManager(BACKUP_DIR)
    
    # Try to create a second backup immediately (should work because locks are released)
    result2 = backup_mgr2.create_backup(TEST_FILE)
    print(f"Second backup: {result2['message']}")
    
    if result1['status'] == 'SUCCESS' and result2['status'] == 'SUCCESS':
        print(f"SUCCESS: File locking worked correctly")
        return True
    else:
        print(f"ERROR: File locking test failed")
        return False

def run_all_tests():
    """Run all tests in sequence"""
    try:
        print(f"Creating test environment in: {TEST_DIR}")
        
        # Run tests
        backup_result = test_backup_creation()
        rotation_result = test_backup_rotation()
        restore_result = test_restore()
        locking_result = test_file_locking()
        
        # Summary
        print("\n=== Test Summary ===")
        print(f"Backup Creation: {'PASS' if backup_result['status'] == 'SUCCESS' else 'FAIL'}")
        print(f"Backup Rotation: {'PASS' if rotation_result else 'FAIL'}")
        print(f"Restore: {'PASS' if restore_result else 'FAIL'}")
        print(f"File Locking: {'PASS' if locking_result else 'FAIL'}")
        
        all_passed = (backup_result['status'] == 'SUCCESS' and 
                      rotation_result and 
                      restore_result and 
                      locking_result)
        
        print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
        
    finally:
        # Ask if test files should be cleaned up
        if input("\nClean up test files? (y/n): ").lower() == 'y':
            cleanup_test_files()
        else:
            print(f"Test files kept at: {TEST_DIR}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test backup_manager.py functionality")
    parser.add_argument('--test', choices=['backup', 'rotation', 'restore', 'locking', 'all'], 
                        default='all', help='Test to run')
    
    args = parser.parse_args()
    
    if args.test == 'backup':
        test_backup_creation()
    elif args.test == 'rotation':
        test_backup_rotation()
    elif args.test == 'restore':
        test_restore()
    elif args.test == 'locking':
        test_file_locking()
    else:
        run_all_tests()