"""
Test script to verify package imports can be resolved.
Tests that DXF and GCode package structure is correct across platforms.
"""
import unittest
import os
import sys
import importlib

# Add the parent directory to the path so Python can find our packages
# This is needed when running tests from the UnitTests directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


class TestPackageImports(unittest.TestCase):
    """Tests that package imports can be resolved without errors."""
    
    def test_dxf_package_import(self):
        """Test that the DXF package can be imported."""
        try:
            import DXF
            self.assertTrue(True, "DXF package imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import DXF package: {e}")
            
    def test_gcode_package_import(self):
        """Test that the GCode package can be imported."""
        try:
            import GCode
            self.assertTrue(True, "GCode package imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import GCode package: {e}")
    
    def test_dxf_module_imports(self):
        """Test that DXF modules can be imported."""
        dxf_modules = [
            "DXF.file_loader", 
            "DXF.workpiece_extractor",
            "DXF.drilling_extractor",
            "DXF.tool_extractor",
            "DXF.entity_processor",
            "DXF.geometry",
            "DXF.coordinate_utils"
        ]
        
        for module in dxf_modules:
            try:
                importlib.import_module(module)
                self.assertTrue(True, f"{module} imported successfully")
            except ImportError as e:
                self.fail(f"Failed to import {module}: {e}")
    
    def test_gcode_module_imports(self):
        """Test that GCode modules can be imported."""
        gcode_modules = [
            "GCode.code_generator",
            "GCode.safety_checker",
            "GCode.tool_validator",
            "GCode.path_planner",
            "GCode.drilling_operations",
            "GCode.preprocessor",
            "GCode.formatter"
        ]
        
        for module in gcode_modules:
            try:
                importlib.import_module(module)
                self.assertTrue(True, f"{module} imported successfully")
            except ImportError as e:
                self.fail(f"Failed to import {module}: {e}")
                
    def test_import_across_platforms(self):
        """Test that platform-specific path handling works correctly."""
        # Get platform information
        import platform
        system = platform.system()
        
        # This test just checks that the platform is correctly identified
        # You can expand this later with platform-specific tests
        if system == 'Windows':
            self.assertEqual(os.sep, '\\', "Correct path separator for Windows")
        else:
            self.assertEqual(os.sep, '/', "Correct path separator for Unix-like systems")


if __name__ == '__main__':
    unittest.main()