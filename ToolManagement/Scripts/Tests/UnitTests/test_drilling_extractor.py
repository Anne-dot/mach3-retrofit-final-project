#!/usr/bin/env python3
"""
Simplified unit tests for the drilling_extractor module.

This approach uses the existing DXF file in TestData/DXF instead of
creating mock objects or generating test files.
"""

import os
import sys
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import modules to test
from DXF.drilling_extractor import DrillingExtractor
from DXF.file_loader import DxfLoader

class TestDrillingExtractorSimple(unittest.TestCase):
    """Test drilling point extraction using an existing DXF file."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        # Initialize extractors
        cls.extractor = DrillingExtractor()
        cls.loader = DxfLoader()
        
        # Define test data directory
        cls.test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'TestData', 'DXF'))
        
        # Find available DXF file in the test directory
        cls.dxf_files = []
        if os.path.exists(cls.test_dir):
            cls.dxf_files = [f for f in os.listdir(cls.test_dir) if f.lower().endswith('.dxf')]
        
        # Pre-load DXF document for efficiency
        cls.doc = None
        cls.dxf_file = None
        
        if cls.dxf_files:
            cls.dxf_file = os.path.join(cls.test_dir, cls.dxf_files[0])
            success, doc, message = cls.loader.load_dxf(cls.dxf_file)
            if success:
                cls.doc = doc
            else:
                print(f"Failed to load test file: {message}")
    
    def setUp(self):
        """Set up for each test."""
        # Skip all tests if no DXF file is available
        if not self.doc:
            self.skipTest("No valid DXF file available in TestData/DXF directory")
    
    def test_file_loading(self):
        """Verify that the test file loaded correctly."""
        self.assertIsNotNone(self.doc)
        self.assertTrue(self.dxf_file.endswith('.dxf'))
        
        # Print file info for debugging
        info = self.loader.get_dxf_info(self.doc)
        print(f"\nLoaded test file: {os.path.basename(self.dxf_file)}")
        print(f"  Version: {info['dxf_version']}")
        print(f"  Total entities: {info['total_entities']}")
        
        # Print layer info for better debugging
        print("\nLayers:")
        for layer_name in info['layers']:
            print(f"  - {layer_name}")
        
        # Print entity counts
        print("\nEntity types:")
        for entity_type, count in info['entity_counts'].items():
            print(f"  - {entity_type}: {count}")
    
    def test_find_drilling_points(self):
        """Test extraction of drilling points from the test file."""
        # Extract drilling points
        success, points, message = self.extractor.find_drilling_points(self.doc)
        
        # Print results for debugging
        print(f"\nDrilling point extraction: {'Success' if success else 'Failed'}")
        print(f"Message: {message}")
        
        if success:
            print(f"Vertical drilling points: {len(points['vertical'])}")
            print(f"Horizontal drilling points: {len(points['horizontal'])}")
            
            # Print some details about the first few points
            if points['vertical']:
                print("\nSample vertical points:")
                for i, point in enumerate(points['vertical'][:2]):  # Just show first 2
                    print(f"  {i+1}. Position: {point.position}, Diameter: {point.diameter}, Depth: {point.depth}")
            
            if points['horizontal']:
                print("\nSample horizontal points:")
                for i, point in enumerate(points['horizontal'][:2]):  # Just show first 2
                    print(f"  {i+1}. Position: {point.position}, Diameter: {point.diameter}, Depth: {point.depth}, Edge: {point.edge}")
        
        # Basic assertions
        self.assertTrue(success)
        self.assertIsNotNone(points)
        self.assertIn('vertical', points)
        self.assertIn('horizontal', points)
    
    def test_extract_parameters(self):
        """Test extraction of drilling parameters."""
        # First get drilling points
        success, points, _ = self.extractor.find_drilling_points(self.doc)
        if not success:
            self.skipTest("Could not extract drilling points")
        
        # Extract parameters
        success, params, message = self.extractor.extract_drilling_parameters(self.doc, points)
        
        # Print results for debugging
        print(f"\nParameter extraction: {'Success' if success else 'Failed'}")
        print(f"Message: {message}")
        
        if success:
            print(f"Vertical parameters: {len(params['vertical'])}")
            print(f"Horizontal parameters: {len(params['horizontal'])}")
        
        # Basic assertions
        self.assertTrue(success)
        self.assertIsNotNone(params)
        self.assertIn('vertical', params)
        self.assertIn('horizontal', params)
    
    def test_group_drilling_operations(self):
        """Test grouping of drilling operations."""
        # First get drilling points
        success, points, _ = self.extractor.find_drilling_points(self.doc)
        if not success:
            self.skipTest("Could not extract drilling points")
        
        # Extract parameters
        success, params, _ = self.extractor.extract_drilling_parameters(self.doc, points)
        if not success:
            self.skipTest("Could not extract drilling parameters")
        
        # Group operations
        success, groups, message = self.extractor.group_drilling_operations(self.doc, params)
        
        # Print results for debugging
        print(f"\nGrouping operations: {'Success' if success else 'Failed'}")
        print(f"Message: {message}")
        
        if success:
            print("\nVertical groups:")
            for group_key, operations in groups['vertical'].items():
                print(f"  - {group_key}: {len(operations)} operations")
            
            print("\nHorizontal groups:")
            for group_key, operations in groups['horizontal'].items():
                print(f"  - {group_key}: {len(operations)} operations")
        
        # Basic assertions
        self.assertTrue(success)
        self.assertIsNotNone(groups)
        self.assertIn('vertical', groups)
        self.assertIn('horizontal', groups)
    
    def test_extract_all_drilling_info(self):
        """Test complete extraction of drilling info."""
        # Extract all info in one call
        success, info, message = self.extractor.extract_all_drilling_info(self.doc)
        
        # Print results for debugging
        print(f"\nAll drilling info extraction: {'Success' if success else 'Failed'}")
        print(f"Message: {message}")
        
        if success:
            print(f"Vertical points: {info['vertical_count']}")
            print(f"Horizontal points: {info['horizontal_count']}")
            print(f"Vertical groups: {info['vertical_groups']}")
            print(f"Horizontal groups: {info['horizontal_groups']}")
        else:
            print(f"Error: {message}")
        
        # Basic assertions
        self.assertTrue(success)
        self.assertIsNotNone(info)
        self.assertIn('points', info)
        self.assertIn('directions', info)
        self.assertIn('parameters', info)
        self.assertIn('groups', info)

if __name__ == '__main__':
    unittest.main()