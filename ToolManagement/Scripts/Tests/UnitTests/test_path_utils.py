"""
Unit tests for the path_utils module.

These tests verify that the PathUtils class functions correctly
across platforms and provides consistent path handling.
"""

import unittest
import os
import sys
import tempfile
import shutil
import platform
from pathlib import Path

# Add parent directory to path to import the module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the module to test
from Utils.path_utils import PathUtils


class TestPathUtils(unittest.TestCase):
    """Tests for the PathUtils class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = os.path.join(self.temp_dir, "test_directory")
        
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary test directory
        shutil.rmtree(self.temp_dir)
    
    def test_ensure_dir(self):
        """Test that ensure_dir creates directories as expected."""
        # Test with string path
        result_str = PathUtils.ensure_dir(self.test_dir)
        self.assertTrue(os.path.exists(self.test_dir))
        self.assertEqual(result_str, Path(self.test_dir))
        
        # Test with Path object
        test_path = Path(os.path.join(self.temp_dir, "test_path_obj"))
        result_path = PathUtils.ensure_dir(test_path)
        self.assertTrue(test_path.exists())
        self.assertEqual(result_path, test_path)
        
        # Test nested directories
        nested_dir = os.path.join(self.test_dir, "nested1", "nested2")
        PathUtils.ensure_dir(nested_dir)
        self.assertTrue(os.path.exists(nested_dir))
    
    def test_normalize_path(self):
        """Test that normalize_path handles platform-specific paths."""
        # Test with mixed slashes
        mixed_path = "folder/subfolder\\file.txt"
        normalized = PathUtils.normalize_path(mixed_path)
        
        if platform.system() == 'Windows':
            self.assertNotIn('/', normalized)
            self.assertEqual(normalized, os.path.normpath(mixed_path.replace('/', '\\')))
        else:
            self.assertNotIn('\\', normalized)
            self.assertEqual(normalized, os.path.normpath(mixed_path.replace('\\', '/')))
        
        # Test with Path object
        path_obj = Path("folder/subfolder")
        normalized_obj = PathUtils.normalize_path(path_obj)
        self.assertIsInstance(normalized_obj, str)
    
    def test_relative_to_absolute(self):
        """Test that relative_to_absolute correctly resolves paths."""
        # Create a subdirectory for testing
        base_dir = os.path.join(self.temp_dir, "base_dir")
        os.makedirs(base_dir, exist_ok=True)
        
        # Test relative path resolution
        rel_path = "subdir/file.txt"
        abs_path = PathUtils.relative_to_absolute(rel_path, base_dir)
        
        expected_path = Path(base_dir) / "subdir" / "file.txt"
        self.assertEqual(abs_path, expected_path.resolve())
        
        # Test with default base path
        with tempfile.TemporaryDirectory() as temp_cwd:
            # Change current working directory temporarily
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_cwd)
                abs_path_default = PathUtils.relative_to_absolute("test.txt")
                self.assertEqual(abs_path_default, Path(temp_cwd) / "test.txt")
            finally:
                os.chdir(original_cwd)
    
    def test_project_root_detection(self):
        """Test that get_project_root returns a valid directory."""
        root_dir = PathUtils.get_project_root()
        
        # Verify it's a real directory
        self.assertTrue(os.path.isdir(str(root_dir)))
        
        # On test systems, it should contain either the 'Utils' folder or be the test directory
        utils_exists = (root_dir / "Utils").exists() or (root_dir / "utils").exists()
        tests_exists = (root_dir / "tests").exists()
        
        # At least one of these should be true in a valid project structure
        self.assertTrue(utils_exists or tests_exists or "Mach3" in root_dir.parts)
    
    def test_directory_getters(self):
        """Test directory getter methods return valid paths."""
        # Test data directory
        data_dir = PathUtils.get_data_dir()
        self.assertTrue(os.path.isdir(str(data_dir)))
        
        # Test logs directory
        logs_dir = PathUtils.get_logs_dir()
        self.assertTrue(os.path.isdir(str(logs_dir)))
        
        # Test test data directory
        test_data_dir = PathUtils.get_test_data_dir()
        self.assertTrue(os.path.isdir(str(test_data_dir)))
        
        # Directory names should match expected patterns
        if platform.system() == 'Windows' and 'Mach3' in str(PathUtils.get_project_root()):
            # Production environment structure
            self.assertTrue(str(data_dir).endswith('Data'))
            self.assertTrue(str(logs_dir).endswith('Logs'))
            self.assertTrue('TestData' in str(test_data_dir))
        else:
            # Development environment structure
            self.assertTrue(str(data_dir).endswith('data'))
            self.assertTrue(str(logs_dir).endswith('logs'))
            self.assertTrue('data' in str(test_data_dir))


if __name__ == '__main__':
    unittest.main()
