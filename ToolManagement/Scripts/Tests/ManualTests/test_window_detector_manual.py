"""
Manual test script for window_detector module.

This script provides a simple way to manually test if the WindowDetector
can detect if a specific file is open in Notepad or WordPad.

Usage:
    python test_manual_window_detector.py [path_to_file]
"""

import os
import sys
import time
import logging

# Add FileMonitor directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'FileMonitor'))

from window_detector import WindowDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(text):
    """Print a header with decorative borders."""
    border = "=" * 60
    print(f"\n{border}")
    print(f"{text.center(60)}")
    print(f"{border}\n")


def test_file_detection(file_path):
    """
    Test if file is detected as open in Notepad or WordPad.
    
    Args:
        file_path: Path to the file to check
    """
    print_header("WINDOW DETECTOR MANUAL TEST")
    
    # Normalize path
    file_path = os.path.abspath(file_path)
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        return
    
    print(f"Testing file: {file_path}")
    print(f"Filename: {os.path.basename(file_path)}")
    print("\nInitializing detector...")
    
    # Create detector
    detector = WindowDetector(debug_mode=True)
    
    # First test with file hopefully NOT open
    print("\nTEST 1: Checking if file is currently open...")
    result = detector.is_file_open(file_path)
    
    if result:
        app = detector.get_application_with_file(file_path)
        print(f"File IS currently open in {app}")
        print("Please close the file and run the test again.")
        return
    else:
        print("File is NOT currently open in any supported editor.")
    
    # Instructions for user
    print("\n" + "-" * 60)
    print("INSTRUCTIONS:")
    print("1. Please open the file in Notepad now")
    print("2. Waiting 20 seconds...")
    print("-" * 60)
    
    # Wait for user to open file
    time.sleep(20)
    
    # Test again after file should be open
    print("\nTEST 2: Checking if file is now open...")
    result = detector.is_file_open(file_path)
    
    if result:
        app = detector.get_application_with_file(file_path)
        print(f"SUCCESS: File detected as open in {app}")
    else:
        print("FAILED: File not detected as open in any supported editor.")
        print("This could mean:")
        print("- The file wasn't opened yet")
        print("- The file was opened in an unsupported editor")
        print("- The detection failed")
    
    print("\n" + "-" * 60)
    print("TEST COMPLETE")
    print("-" * 60)


if __name__ == "__main__":
    # Get file path from command line or use default
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Default path for tool data CSV
        file_path = r"C:\Mach3\ToolManagement\Data\tool-data.csv"
    
    # Run test
    test_file_detection(file_path)
