#!/usr/bin/env python3
#!/usr/bin/env python3

r"""
Mach3 Comprehensive Sync Test
=============================

This script tests synchronization between C:\Mach3 and Z:\Mach3 directories
to ensure file operations are properly synchronized in both directions.

Tests include:
- File creation in both directions
- File modification in both directions
- File deletion in both directions  
- Directory creation and deletion
- Empty file handling
- Large file handling (1MB)

Usage
-----
Basic usage:
    python mach3-comprehensive-sync-test.py

With custom wait time (in seconds):
    python mach3-comprehensive-sync-test.py --wait-time 180

With custom test folder:
    python mach3-comprehensive-sync-test.py --folder "DevelopmentEnvironment"

Run a specific test only:
    python mach3-comprehensive-sync-test.py --test large

Available test options:
    all         - Run all tests (default)
    create_s2d  - File creation from source to destination
    create_d2s  - File creation from destination to source
    modify_s2d  - File modification from source to destination
    modify_d2s  - File modification from destination to source
    delete_s2d  - File deletion from source to destination
    delete_d2s  - File deletion from destination to source
    directory   - Directory creation and deletion
    empty       - Empty file sync
    large       - Large file sync (1MB)

Combine options:
    python mach3-comprehensive-sync-test.py --wait-time 60 --folder "macros\\Mach3Development" --test create_s2d

Output
------
The script will display results in the console and also save detailed logs to:
C:\Mach3\DevelopmentEnvironment\test_logs\comprehensive_test_YYYYMMDD_HHMMSS.log

Test Paths
----------
Source: C:\Mach3
Destination: Z:\Mach3
Default test folder: ToolManagement

Notes
-----
- Default wait time between operations is 150 seconds
- The script will keep the console window open after completion
- Large file test uses double wait time for synchronization
- If a test directory doesn't exist, the script will try to create it
"""

import os
import sys
import time
import random
import string
import logging
import datetime
import shutil
import hashlib
import argparse
import traceback
from typing import Dict, List, Any, Optional, Tuple, Union, Callable

# Constants
MACH3_DIR = "C:\\Mach3"
SHARED_DIR = "Z:\\Mach3"
SYNC_WAIT_TIME = 150  # Default wait time in seconds
TEST_FOLDERS = ["ToolManagement", "DevelopmentEnvironment", "macros\\Mach3Development"]
DEFAULT_TEST_FOLDER = "ToolManagement"  # This was confirmed working

# Configure logging
def setup_logging() -> str:
    """Set up logging configuration and return the log file path."""
    try:
        log_dir = os.path.join(MACH3_DIR, "DevelopmentEnvironment", "test_logs")
        os.makedirs(log_dir, exist_ok=True)
        log_filename = f"comprehensive_test_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_file = os.path.join(log_dir, log_filename)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return log_file
    except Exception as e:
        print(f"Error setting up logging: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        input("Press Enter to continue...")
        sys.exit(1)

# Test results tracking
class TestResults:
    """Class to track test results."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.details = []  # type: List[Dict[str, str]]
    
    def add_result(self, test_name: str, result: bool, message: str) -> None:
        """Add a test result to tracking."""
        if result:
            self.passed += 1
            status = "PASS"
            logging.info(f"{status}: {test_name} - {message}")
        else:
            self.failed += 1
            status = "FAIL"
            logging.error(f"{status}: {test_name} - {message}")
        
        print(f"{status}: {test_name} - {message}")
        
        self.details.append({
            "name": test_name,
            "status": status,
            "message": message
        })
    
    def display_summary(self, log_file: str) -> None:
        """Display test results summary."""
        total = self.passed + self.failed
        pass_percentage = (self.passed / total) * 100 if total > 0 else 0
        
        print("\n" + "="*70)
        print("MACH3 SYNC COMPREHENSIVE TEST RESULTS")
        print("="*70)
        print(f"Total tests: {total}")
        print(f"Passed: {self.passed} ({pass_percentage:.1f}%)")
        print(f"Failed: {self.failed}")
        print("="*70)
        
        if self.failed > 0:
            print("\nFAILED TESTS:")
            for test in self.details:
                if test["status"] == "FAIL":
                    print(f"- {test['name']}: {test['message']}")
        
        print(f"\nDetailed log saved to: {log_file}")
        print("="*70)
        
        logging.info(f"TEST SUMMARY: Total={total}, "
                    f"Passed={self.passed}, Failed={self.failed}")

# Helper functions
def random_string(length: int = 8) -> str:
    """Generate random string for test content."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def create_file(filepath: str, content: str) -> bool:
    """Create a file with specified content."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    except Exception as e:
        logging.error(f"Error creating file {filepath}: {e}")
        logging.debug(traceback.format_exc())
        return False

def create_binary_file(filepath: str, size_kb: int) -> bool:
    """Create a binary file of specified size."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(os.urandom(size_kb * 1024))
        return True
    except Exception as e:
        logging.error(f"Error creating binary file {filepath}: {e}")
        logging.debug(traceback.format_exc())
        return False

def calculate_file_hash(filepath: str) -> Optional[str]:
    """Calculate MD5 hash of a file to compare content."""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        logging.error(f"Error calculating hash for {filepath}: {e}")
        logging.debug(traceback.format_exc())
        return None

def wait_for_sync(message: str = "Waiting for sync to complete...") -> None:
    """Wait for sync operations to complete."""
    print(f"Waiting {SYNC_WAIT_TIME} seconds for {message}")
    logging.info(f"Waiting {SYNC_WAIT_TIME} seconds for {message}")
    time.sleep(SYNC_WAIT_TIME)

# Test functions
def test_file_creation_source_to_dest(test_folder: str, test_results: TestResults) -> bool:
    """Test file creation from source to destination."""
    test_name = "File Creation (Source to Destination)"
    print(f"\n=== {test_name} ===")
    logging.info(f"Testing {test_name}")
    
    try:
        # Create unique filename
        filename = f"create_s2d_{random_string()}.txt"
        source_path = os.path.join(MACH3_DIR, test_folder, filename)
        dest_path = os.path.join(SHARED_DIR, test_folder, filename)
        
        # Create content
        content = f"File creation test (source to destination) - {datetime.datetime.now()}"
        
        # Create file in source
        if not create_file(source_path, content):
            test_results.add_result(test_name, False, "Failed to create test file in source")
            return False
        
        logging.info(f"Created file in source: {source_path}")
        
        # Wait for sync
        wait_for_sync()
        
        # Check if file was synced
        if not os.path.exists(dest_path):
            test_results.add_result(test_name, False, f"File not synced to destination: {dest_path}")
            return False
        
        # Verify content
        with open(dest_path, 'r') as f:
            dest_content = f.read()
        
        if content == dest_content:
            test_results.add_result(test_name, True, "File successfully synced with correct content")
            return True
        else:
            test_results.add_result(test_name, False, "File synced but content doesn't match")
            return False
    except Exception as e:
        test_results.add_result(test_name, False, f"Error: {str(e)}")
        logging.error(f"Error in {test_name}: {e}")
        logging.debug(traceback.format_exc())
        return False

def test_file_creation_dest_to_source(test_folder: str, test_results: TestResults) -> bool:
    """Test file creation from destination to source."""
    test_name = "File Creation (Destination to Source)"
    print(f"\n=== {test_name} ===")
    logging.info(f"Testing {test_name}")
    
    try:
        # Create unique filename
        filename = f"create_d2s_{random_string()}.txt"
        source_path = os.path.join(MACH3_DIR, test_folder, filename)
        dest_path = os.path.join(SHARED_DIR, test_folder, filename)
        
        # Create content
        content = f"File creation test (destination to source) - {datetime.datetime.now()}"
        
        # Create file in destination
        if not create_file(dest_path, content):
            test_results.add_result(test_name, False, "Failed to create test file in destination")
            return False
        
        logging.info(f"Created file in destination: {dest_path}")
        
        # Wait for sync
        wait_for_sync()
        
        # Check if file was synced
        if not os.path.exists(source_path):
            test_results.add_result(test_name, False, f"File not synced to source: {source_path}")
            return False
        
        # Verify content
        with open(source_path, 'r') as f:
            source_content = f.read()
        
        if content == source_content:
            test_results.add_result(test_name, True, "File successfully synced with correct content")
            return True
        else:
            test_results.add_result(test_name, False, "File synced but content doesn't match")
            return False
    except Exception as e:
        test_results.add_result(test_name, False, f"Error: {str(e)}")
        logging.error(f"Error in {test_name}: {e}")
        logging.debug(traceback.format_exc())
        return False

def test_file_modification_source_to_dest(test_folder: str, test_results: TestResults) -> bool:
    """Test file modification from source to destination."""
    test_name = "File Modification (Source to Destination)"
    print(f"\n=== {test_name} ===")
    logging.info(f"Testing {test_name}")
    
    try:
        # Create unique filename
        filename = f"modify_s2d_{random_string()}.txt"
        source_path = os.path.join(MACH3_DIR, test_folder, filename)
        dest_path = os.path.join(SHARED_DIR, test_folder, filename)
        
        # Create initial content
        initial_content = f"Initial content before modification - {random_string(20)}"
        
        # Create file in source
        if not create_file(source_path, initial_content):
            test_results.add_result(test_name, False, "Failed to create initial test file")
            return False
        
        logging.info(f"Created initial file in source: {source_path}")
        
        # Wait for initial sync
        wait_for_sync("initial file sync")
        
        # Check if initial file was synced
        if not os.path.exists(dest_path):
            test_results.add_result(test_name, False, "Initial file not synced to destination")
            return False
        
        # Modify file in source with new content
        modified_content = f"Modified content in source - {datetime.datetime.now()} - {random_string(20)}"
        
        if not create_file(source_path, modified_content):
            test_results.add_result(test_name, False, "Failed to modify test file in source")
            return False
        
        logging.info(f"Modified file in source with new content")
        
        # Wait for modification sync
        wait_for_sync("modification sync")
        
        # Verify content was updated
        with open(dest_path, 'r') as f:
            dest_content = f.read()
        
        if modified_content == dest_content:
            test_results.add_result(test_name, True, "File modification successfully synced")
            return True
        else:
            test_results.add_result(test_name, False, "File exists but modifications weren't synced correctly")
            return False
    except Exception as e:
        test_results.add_result(test_name, False, f"Error: {str(e)}")
        logging.error(f"Error in {test_name}: {e}")
        logging.debug(traceback.format_exc())
        return False

def test_file_modification_dest_to_source(test_folder: str, test_results: TestResults) -> bool:
    """Test file modification from destination to source."""
    test_name = "File Modification (Destination to Source)"
    print(f"\n=== {test_name} ===")
    logging.info(f"Testing {test_name}")
    
    try:
        # Create unique filename
        filename = f"modify_d2s_{random_string()}.txt"
        source_path = os.path.join(MACH3_DIR, test_folder, filename)
        dest_path = os.path.join(SHARED_DIR, test_folder, filename)
        
        # Create initial content
        initial_content = f"Initial content before modification - {random_string(20)}"
        
        # Create file in destination
        if not create_file(dest_path, initial_content):
            test_results.add_result(test_name, False, "Failed to create initial test file")
            return False
        
        logging.info(f"Created initial file in destination: {dest_path}")
        
        # Wait for initial sync
        wait_for_sync("initial file sync")
        
        # Check if initial file was synced
        if not os.path.exists(source_path):
            test_results.add_result(test_name, False, "Initial file not synced to source")
            return False
        
        # Modify file in destination with new content
        modified_content = f"Modified content in destination - {datetime.datetime.now()} - {random_string(20)}"
        
        if not create_file(dest_path, modified_content):
            test_results.add_result(test_name, False, "Failed to modify test file in destination")
            return False
        
        logging.info(f"Modified file in destination with new content")
        
        # Wait for modification sync
        wait_for_sync("modification sync")
        
        # Verify content was updated
        with open(source_path, 'r') as f:
            source_content = f.read()
        
        if modified_content == source_content:
            test_results.add_result(test_name, True, "File modification successfully synced")
            return True
        else:
            test_results.add_result(test_name, False, "File exists but modifications weren't synced correctly")
            return False
    except Exception as e:
        test_results.add_result(test_name, False, f"Error: {str(e)}")
        logging.error(f"Error in {test_name}: {e}")
        logging.debug(traceback.format_exc())
        return False

def test_file_deletion_source_to_dest(test_folder: str, test_results: TestResults) -> bool:
    """Test file deletion from source to destination."""
    test_name = "File Deletion (Source to Destination)"
    print(f"\n=== {test_name} ===")
    logging.info(f"Testing {test_name}")
    
    try:
        # Create unique filename
        filename = f"delete_s2d_{random_string()}.txt"
        source_path = os.path.join(MACH3_DIR, test_folder, filename)
        dest_path = os.path.join(SHARED_DIR, test_folder, filename)
        
        # Create test file
        content = f"File for deletion test - {random_string(20)}"
        
        if not create_file(source_path, content):
            test_results.add_result(test_name, False, "Failed to create test file")
            return False
        
        logging.info(f"Created test file in source: {source_path}")
        
        # Wait for initial sync
        wait_for_sync("initial file sync")
        
        # Verify file was synced before deletion
        if not os.path.exists(dest_path):
            test_results.add_result(test_name, False, "File wasn't synced to destination before deletion test")
            return False
        
        # Delete file from source
        try:
            os.remove(source_path)
            logging.info(f"Deleted file from source: {source_path}")
        except Exception as e:
            test_results.add_result(test_name, False, f"Failed to delete file from source: {e}")
            logging.debug(traceback.format_exc())
            return False
        
        # Wait for deletion to sync
        wait_for_sync("deletion sync")
        
        # Check if file was deleted from destination
        if os.path.exists(dest_path):
            test_results.add_result(test_name, False, "File still exists in destination after deletion from source")
            return False
        else:
            test_results.add_result(test_name, True, "File deletion successfully synced")
            return True
    except Exception as e:
        test_results.add_result(test_name, False, f"Error: {str(e)}")
        logging.error(f"Error in {test_name}: {e}")
        logging.debug(traceback.format_exc())
        return False

def test_file_deletion_dest_to_source(test_folder: str, test_results: TestResults) -> bool:
    """Test file deletion from destination to source."""
    test_name = "File Deletion (Destination to Source)"
    print(f"\n=== {test_name} ===")
    logging.info(f"Testing {test_name}")
    
    try:
        # Create unique filename
        filename = f"delete_d2s_{random_string()}.txt"
        source_path = os.path.join(MACH3_DIR, test_folder, filename)
        dest_path = os.path.join(SHARED_DIR, test_folder, filename)
        
        # Create test file
        content = f"File for deletion test - {random_string(20)}"
        
        if not create_file(dest_path, content):
            test_results.add_result(test_name, False, "Failed to create test file")
            return False
        
        logging.info(f"Created test file in destination: {dest_path}")
        
        # Wait for initial sync
        wait_for_sync("initial file sync")
        
        # Verify file was synced before deletion
        if not os.path.exists(source_path):
            test_results.add_result(test_name, False, "File wasn't synced to source before deletion test")
            return False
        
        # Delete file from destination
        try:
            os.remove(dest_path)
            logging.info(f"Deleted file from destination: {dest_path}")
        except Exception as e:
            test_results.add_result(test_name, False, f"Failed to delete file from destination: {e}")
            logging.debug(traceback.format_exc())
            return False
        
        # Wait for deletion to sync
        wait_for_sync("deletion sync")
        
        # Check if file was deleted from source
        if os.path.exists(source_path):
            test_results.add_result(test_name, False, "File still exists in source after deletion from destination")
            return False
        else:
            test_results.add_result(test_name, True, "File deletion successfully synced")
            return True
    except Exception as e:
        test_results.add_result(test_name, False, f"Error: {str(e)}")
        logging.error(f"Error in {test_name}: {e}")
        logging.debug(traceback.format_exc())
        return False

def test_directory_creation_and_deletion(test_folder: str, test_results: TestResults) -> bool:
    """Test directory creation and deletion."""
    test_name = "Directory Creation and Deletion"
    print(f"\n=== {test_name} ===")
    logging.info(f"Testing {test_name}")
    
    try:
        # Create a unique directory name
        dir_name = f"test_dir_{random_string()}"
        source_dir = os.path.join(MACH3_DIR, test_folder, dir_name)
        dest_dir = os.path.join(SHARED_DIR, test_folder, dir_name)
        
        # Create directory in source
        try:
            os.makedirs(source_dir, exist_ok=True)
            logging.info(f"Created directory in source: {source_dir}")
        except Exception as e:
            test_results.add_result(test_name, False, f"Failed to create test directory: {e}")
            logging.debug(traceback.format_exc())
            return False
        
        # Wait for directory creation to sync
        wait_for_sync("directory creation sync")
        
        # Check if directory was created in destination
        if not os.path.exists(dest_dir) or not os.path.isdir(dest_dir):
            test_results.add_result(test_name, False, "Directory not synced to destination")
            return False
        
        logging.info(f"Directory successfully synced to destination: {dest_dir}")
        
        # Delete the directory from source
        try:
            shutil.rmtree(source_dir)
            logging.info(f"Deleted directory from source: {source_dir}")
        except Exception as e:
            test_results.add_result(test_name, False, f"Failed to delete test directory: {e}")
            logging.debug(traceback.format_exc())
            return False
        
        # Wait for directory deletion to sync
        wait_for_sync("directory deletion sync")
        
        # Check if directory was deleted from destination
        if os.path.exists(dest_dir):
            test_results.add_result(test_name, False, "Directory still exists in destination after deletion from source")
            return False
        else:
            test_results.add_result(test_name, True, "Directory creation and deletion successfully synced")
            return True
    except Exception as e:
        test_results.add_result(test_name, False, f"Error: {str(e)}")
        logging.error(f"Error in {test_name}: {e}")
        logging.debug(traceback.format_exc())
        return False

def test_empty_file(test_folder: str, test_results: TestResults) -> bool:
    """Test syncing of an empty (zero-byte) file."""
    test_name = "Empty File Sync"
    print(f"\n=== {test_name} ===")
    logging.info(f"Testing {test_name}")
    
    try:
        # Create a unique filename
        filename = f"empty_file_{random_string()}.txt"
        source_path = os.path.join(MACH3_DIR, test_folder, filename)
        dest_path = os.path.join(SHARED_DIR, test_folder, filename)
        
        # Create an empty file
        try:
            os.makedirs(os.path.dirname(source_path), exist_ok=True)
            with open(source_path, 'w'):
                pass  # Just create an empty file
            logging.info(f"Created empty file in source: {source_path}")
        except Exception as e:
            test_results.add_result(test_name, False, f"Failed to create empty file: {e}")
            logging.debug(traceback.format_exc())
            return False
        
        # Wait for sync
        wait_for_sync()
        
        # Check if file was synced
        if not os.path.exists(dest_path):
            test_results.add_result(test_name, False, "Empty file not synced to destination")
            return False
        
        # Verify file is still empty
        file_size = os.path.getsize(dest_path)
        if file_size == 0:
            test_results.add_result(test_name, True, "Empty file successfully synced")
            return True
        else:
            test_results.add_result(test_name, False, f"File synced but is not empty (size: {file_size} bytes)")
            return False
    except Exception as e:
        test_results.add_result(test_name, False, f"Error: {str(e)}")
        logging.error(f"Error in {test_name}: {e}")
        logging.debug(traceback.format_exc())
        return False

def test_large_file(test_folder: str, test_results: TestResults) -> bool:
    """Test syncing of a large file (1MB)."""
    test_name = "Large File Sync"
    print(f"\n=== {test_name} ===")
    logging.info(f"Testing {test_name}")
    
    try:
        # Create a unique filename
        filename = f"large_file_{random_string()}.bin"
        source_path = os.path.join(MACH3_DIR, test_folder, filename)
        dest_path = os.path.join(SHARED_DIR, test_folder, filename)
        
        # Create a 1MB file
        file_size_kb = 1024  # 1MB = 1024KB
        
        if not create_binary_file(source_path, file_size_kb):
            test_results.add_result(test_name, False, "Failed to create large test file")
            return False
        
        logging.info(f"Created {file_size_kb}KB file in source: {source_path}")
        
        # Calculate source file hash for later comparison
        source_hash = calculate_file_hash(source_path)
        if not source_hash:
            test_results.add_result(test_name, False, "Failed to calculate hash for source file")
            return False
        
        # Wait for sync (possibly longer for large file)
        wait_time = SYNC_WAIT_TIME * 2  # Double wait time for large file
        print(f"Waiting {wait_time} seconds for large file sync...")
        logging.info(f"Waiting {wait_time} seconds for large file sync...")
        time.sleep(wait_time)
        
        # Check if file was synced
        if not os.path.exists(dest_path):
            test_results.add_result(test_name, False, "Large file not synced to destination")
            return False
        
        # Verify file content with hash comparison
        dest_hash = calculate_file_hash(dest_path)
        if not dest_hash:
            test_results.add_result(test_name, False, "Failed to calculate hash for destination file")
            return False
        
        if source_hash == dest_hash:
            test_results.add_result(test_name, True, f"Large file ({file_size_kb}KB) successfully synced")
            return True
        else:
            test_results.add_result(test_name, False, "Large file synced but content doesn't match")
            return False
    except Exception as e:
        test_results.add_result(test_name, False, f"Error: {str(e)}")
        logging.error(f"Error in {test_name}: {e}")
        logging.debug(traceback.format_exc())
        return False

def verify_environment() -> bool:
    """Verify the environment is set up correctly."""
    try:
        # Check if source directory exists
        if not os.path.exists(MACH3_DIR):
            print(f"ERROR: Source directory does not exist: {MACH3_DIR}")
            return False
        
        # Check if destination directory exists
        if not os.path.exists(SHARED_DIR):
            print(f"ERROR: Destination directory does not exist: {SHARED_DIR}")
            return False
        
        # Verify test directories exist or can be created
        for test_folder in TEST_FOLDERS:
            source_test_dir = os.path.join(MACH3_DIR, test_folder)
            dest_test_dir = os.path.join(SHARED_DIR, test_folder)
            
            # Try to create directories if they don't exist
            try:
                if not os.path.exists(source_test_dir):
                    os.makedirs(source_test_dir, exist_ok=True)
                    logging.info(f"Created source test directory: {source_test_dir}")
                
                if not os.path.exists(dest_test_dir):
                    os.makedirs(dest_test_dir, exist_ok=True)
                    logging.info(f"Created destination test directory: {dest_test_dir}")
            except Exception as e:
                print(f"ERROR: Failed to create test directories: {e}")
                logging.error(f"Failed to create test directories: {e}")
                logging.debug(traceback.format_exc())
                return False
        
        return True
    except Exception as e:
        print(f"ERROR: Failed to verify environment: {e}")
        logging.error(f"Failed to verify environment: {e}")
        logging.debug(traceback.format_exc())
        return False

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Mach3 Comprehensive Sync Test')
    parser.add_argument('--wait-time', type=int, default=SYNC_WAIT_TIME,
                       help=f'Wait time for sync operations in seconds (default: {SYNC_WAIT_TIME})')
    parser.add_argument('--folder', type=str, default=DEFAULT_TEST_FOLDER,
                       help=f'Folder to test within Mach3 directories (default: {DEFAULT_TEST_FOLDER})')
    parser.add_argument('--test', type=str, default="all",
                       help='Specific test to run (default: all)')
    return parser.parse_args()

def print_header(test_folder: str, wait_time: int) -> None:
    """Print test header information."""
    print("="*70)
    print("MACH3 COMPREHENSIVE SYNC TEST")
    print("="*70)
    print(f"Source directory: {MACH3_DIR}")
    print(f"Destination directory: {SHARED_DIR}")
    print(f"Test folder: {test_folder}")
    print(f"Wait time: {wait_time} seconds")
    print("="*70)

def main() -> int:
    """Main function to run all tests."""
    try:
        # Set up logging first
        log_file = setup_logging()
        
        # Parse command line arguments
        args = parse_arguments()
        
        # Set the wait time and test folder from arguments
        global SYNC_WAIT_TIME
        SYNC_WAIT_TIME = args.wait_time
        test_folder = args.folder
        
        # Initialize test results
        test_results = TestResults()
        
        # Print header
        print_header(test_folder, SYNC_WAIT_TIME)
        
        # Verify environment
        if not verify_environment():
            print("Environment verification failed. Cannot continue tests.")
            logging.error("Environment verification failed. Cannot continue tests.")
            input("Press Enter to continue...")
            return 1
        
        # Run specific test or all tests
        if args.test == "all" or args.test == "create_s2d":
            test_file_creation_source_to_dest(test_folder, test_results)
        
        if args.test == "all" or args.test == "create_d2s":
            test_file_creation_dest_to_source(test_folder, test_results)
            
        if args.test == "all" or args.test == "modify_s2d":
            test_file_modification_source_to_dest(test_folder, test_results)
            
        if args.test == "all" or args.test == "modify_d2s":
            test_file_modification_dest_to_source(test_folder, test_results)
            
        if args.test == "all" or args.test == "delete_s2d":
            test_file_deletion_source_to_dest(test_folder, test_results)
            
        if args.test == "all" or args.test == "delete_d2s":
            test_file_deletion_dest_to_source(test_folder, test_results)
            
        if args.test == "all" or args.test == "directory":
            test_directory_creation_and_deletion(test_folder, test_results)
            
        if args.test == "all" or args.test == "empty":
            test_empty_file(test_folder, test_results)
            
        if args.test == "all" or args.test == "large":
            test_large_file(test_folder, test_results)
        
        # Display test results
        test_results.display_summary(log_file)
        
        # Return appropriate exit code
        return 0 if test_results.failed == 0 else 1
    
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        logging.critical(f"FATAL ERROR: {e}")
        logging.critical(traceback.format_exc())
        input("Press Enter to continue...")
        return 1
    finally:
        # If this is run from a double-click, prevent window from closing immediately
        if len(sys.argv) == 1:  # Script was run without arguments (likely double-clicked)
            input("\nPress Enter to exit...")

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Unhandled exception: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        input("Press Enter to exit...")
        sys.exit(1)
