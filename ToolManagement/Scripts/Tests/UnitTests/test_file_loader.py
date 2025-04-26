"""
Unit tests for the file_loader module.

These tests verify that the DXF file loading functionality works correctly,
including validation, error handling, and metadata extraction.
"""

import unittest
import os
import sys
import tempfile
import platform
import shutil
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Mock the logging_utils module to avoid file creation during tests
sys.modules['Utils.logging_utils'] = MagicMock()
from Utils.logging_utils import setup_logger, log_exception

# Import ezdxf first to ensure it's available for mocking
import ezdxf

# Now import the module to test
from DXF.file_loader import DxfLoader


class TestDxfLoader(unittest.TestCase):
    """Tests for the DxfLoader class in file_loader module."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create a minimal valid DXF test file
        self.valid_dxf_path = os.path.join(self.test_dir, "valid_test.dxf")
        self.create_test_dxf_file(self.valid_dxf_path, valid=True)
        
        # Create an invalid DXF test file
        self.invalid_dxf_path = os.path.join(self.test_dir, "invalid_test.dxf")
        self.create_test_dxf_file(self.invalid_dxf_path, valid=False)
        
        # Create a non-DXF file
        self.non_dxf_path = os.path.join(self.test_dir, "test.txt")
        with open(self.non_dxf_path, 'w') as f:
            f.write("This is not a DXF file")
            
        # Set up mocks for logging
        setup_logger.return_value = MagicMock()
        
        # Create the loader instance for testing
        self.loader = DxfLoader()
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)
    
    def create_test_dxf_file(self, path, valid=True):
        """
        Helper to create a test DXF file.
        
        For testing purposes, we're just creating a file with the DXF extension.
        The actual DXF content will be mocked in tests.
        """
        with open(path, 'w') as f:
            if valid:
                f.write("MOCK DXF CONTENT - For testing only")
            else:
                f.write("INVALID CONTENT")
    
    @patch('ezdxf.readfile')
    def test_load_valid_dxf(self, mock_readfile):
        """Test loading a valid DXF file."""
        # Set up mock ezdxf.readfile to return a mock document
        mock_doc = MagicMock()
        mock_doc.dxfversion = "AC1024"
        mock_modelspace = MagicMock()
        mock_doc.modelspace.return_value = mock_modelspace
        mock_modelspace.__iter__.return_value = [MagicMock(), MagicMock()]  # Two mock entities
        mock_modelspace.__len__.return_value = 2  # Length for list conversion
        mock_doc.layers = [MagicMock(), MagicMock()]  # Two mock layers
        mock_doc.header = {'TEST': 'VALUE'}
        
        mock_readfile.return_value = mock_doc
        
        # Test loading the valid file
        success, doc, message = self.loader.load_dxf(self.valid_dxf_path)
        
        # Verify results
        self.assertTrue(success)
        self.assertIsNotNone(doc)
        self.assertIn("Successfully loaded", message)
        
        # Verify mock was called correctly
        mock_readfile.assert_called_once_with(self.valid_dxf_path)
    
    @patch('ezdxf.readfile')
    def test_load_invalid_dxf(self, mock_readfile):
        """Test loading an invalid DXF file."""
        # Set up mock to raise a DXFError
        mock_readfile.side_effect = ezdxf.DXFError("Invalid DXF format")
        
        # Test loading the invalid file
        success, doc, message = self.loader.load_dxf(self.invalid_dxf_path)
        
        # Verify results
        self.assertFalse(success)
        self.assertIsNone(doc)
        self.assertIn("Error loading DXF file", message)
    
    def test_is_valid_dxf_nonexistent_file(self):
        """Test validation with a non-existent file."""
        is_valid, message = self.loader.is_valid_dxf("nonexistent_file.dxf")
        
        # Verify results
        self.assertFalse(is_valid)
        self.assertIn("not found", message)
    
    def test_is_valid_dxf_non_dxf_file(self):
        """Test validation with a non-DXF file."""
        is_valid, message = self.loader.is_valid_dxf(self.non_dxf_path)
        
        # Verify results
        self.assertFalse(is_valid)
        self.assertIn("does not have .dxf extension", message)
    
    @patch('ezdxf.readfile')
    def test_is_valid_dxf_empty_file(self, mock_readfile):
        """Test validation with a DXF file containing no entities."""
        # Set up mock to return an empty document
        mock_doc = MagicMock()
        mock_modelspace = MagicMock()
        mock_doc.modelspace.return_value = mock_modelspace
        mock_modelspace.__iter__.return_value = []  # No entities
        mock_modelspace.__len__.return_value = 0    # Length 0
        
        mock_readfile.return_value = mock_doc
        
        # Test validation
        is_valid, message = self.loader.is_valid_dxf(self.valid_dxf_path)
        
        # Verify results
        self.assertFalse(is_valid)
        self.assertIn("contains no entities", message)
    
    @patch('ezdxf.readfile')
    def test_get_dxf_info(self, mock_readfile):
        """Test extracting information from a DXF file."""
        # Set up mock document
        mock_doc = MagicMock()
        mock_doc.dxfversion = "AC1024"
        mock_doc.encoding = "utf-8"
        
        # Mock entities
        entity1 = MagicMock()
        entity1.dxftype.return_value = "LINE"
        entity2 = MagicMock()
        entity2.dxftype.return_value = "CIRCLE"
        entity3 = MagicMock()
        entity3.dxftype.return_value = "LINE"
        
        # Mock modelspace
        mock_modelspace = MagicMock()
        mock_modelspace.__iter__.return_value = [entity1, entity2, entity3]
        mock_doc.modelspace.return_value = mock_modelspace
        
        # Mock layers
        layer1 = MagicMock()
        layer1.dxf.name = "Layer1"
        layer1.dxf.color = 1
        layer1.dxf.linetype = "CONTINUOUS"
        layer1.is_on = True
        
        layer2 = MagicMock()
        layer2.dxf.name = "Layer2"
        layer2.dxf.color = 2
        layer2.dxf.linetype = "DASHED"
        layer2.is_on = True
        
        mock_doc.layers = [layer1, layer2]
        
        # Mock header
        mock_doc.header = {'TEST1': 'VALUE1', 'TEST2': 'VALUE2'}
        
        mock_readfile.return_value = mock_doc
        
        # Load the file first
        success, doc, _ = self.loader.load_dxf(self.valid_dxf_path)
        
        # Get the DXF info
        info = self.loader.get_dxf_info(doc)
        
        # Verify the info contents
        self.assertEqual(info['dxf_version'], "AC1024")
        self.assertEqual(info['encoding'], "utf-8")
        self.assertEqual(info['total_entities'], 3)
        self.assertEqual(info['entity_counts']['LINE'], 2)
        self.assertEqual(info['entity_counts']['CIRCLE'], 1)
        self.assertEqual(len(info['layers']), 2)
        self.assertIn('Layer1', info['layers'])
        self.assertIn('Layer2', info['layers'])
        self.assertEqual(info['header_variables'], 2)
    
    @patch('DXF.file_loader.platform.system')
    @patch('DXF.file_loader.filedialog.askopenfilename')
    def test_select_dxf_file_windows(self, mock_askopenfilename, mock_system):
        """Test file selection on Windows."""
        # Mock Windows platform
        mock_system.return_value = "Windows"
        
        # Mock file dialog response
        mock_askopenfilename.return_value = "C:/Path/to/selected.dxf"
        
        # Test file selection
        selected_file = self.loader.select_dxf_file()
        
        # Verify results
        self.assertEqual(selected_file, "C:/Path/to/selected.dxf")
        mock_askopenfilename.assert_called_once()

    @unittest.skipIf(platform.system() == 'Windows', "Skipping Linux-specific test on Windows")
    @patch('DXF.file_loader.platform.system')
    @patch('DXF.file_loader.os.path.abspath')
    @patch('DXF.file_loader.os.listdir')
    @patch('builtins.input')
    def test_select_dxf_file_linux(self, mock_input, mock_listdir, mock_abspath, mock_system):
        """Test file selection on Linux."""
        # Mock Linux platform
        mock_system.return_value = "Linux"
        
        # Mock directory path
        mock_abspath.return_value = "/path/to/test/data/dir"
        
        # Mock directory listing
        mock_listdir.return_value = ["test1.dxf", "test2.dxf", "not_a_dxf.txt"]
        
        # Mock user input
        mock_input.return_value = "1"  # User selects the first file
        
        # Mock directory existence check
        with patch('DXF.file_loader.os.path.exists', return_value=True):
            # Test file selection
            selected_file = self.loader.select_dxf_file()
        
        # Verify results
        self.assertEqual(selected_file, "/path/to/test/data/dir/test1.dxf")
        mock_input.assert_called_once()


if __name__ == '__main__':
    unittest.main()
