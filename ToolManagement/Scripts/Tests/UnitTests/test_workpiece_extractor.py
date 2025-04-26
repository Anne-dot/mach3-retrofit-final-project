#!/usr/bin/env python3
"""
Simplified unit tests for the workpiece_extractor module.

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
from DXF.workpiece_extractor import WorkpieceExtractor
from DXF.file_loader import DxfLoader

class TestWorkpieceExtractorSimple(unittest.TestCase):
    """Test workpiece geometry extraction using an existing DXF file."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        # Initialize extractors
        cls.extractor = WorkpieceExtractor()
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
    
    def test_extract_workpiece_boundaries(self):
        """Test extraction of workpiece boundaries from the test file."""
        # Extract boundaries
        success, boundaries, message = self.extractor.extract_workpiece_boundaries(self.doc)
        
        # Print results for debugging
        print(f"\nWorkpiece boundary extraction: {'Success' if success else 'Failed'}")
        print(f"Message: {message}")
        
        if success:
            print(f"Number of boundaries found: {len(boundaries)}")
            
            # Print information about each boundary
            for i, boundary in enumerate(boundaries):
                print(f"\nBoundary {i+1}:")
                print(f"  Type: {boundary.dxftype()}")
                print(f"  Layer: {boundary.dxf.layer}")
        
        # Basic assertions
        self.assertTrue(success)
        self.assertIsNotNone(boundaries)
        self.assertGreater(len(boundaries), 0)
    
    def test_calculate_dimensions(self):
        """Test calculation of workpiece dimensions."""
        # First get boundaries
        success, boundaries, _ = self.extractor.extract_workpiece_boundaries(self.doc)
        if not success:
            self.skipTest("Could not extract workpiece boundaries")
        
        # Calculate dimensions
        success, dimensions, message = self.extractor.calculate_dimensions(boundaries)
        
        # Print results for debugging
        print(f"\nDimension calculation: {'Success' if success else 'Failed'}")
        print(f"Message: {message}")
        
        if success:
            print("Workpiece dimensions:")
            print(f"  Width: {dimensions['width']:.2f}mm")
            print(f"  Height: {dimensions['height']:.2f}mm")
            print(f"  Depth: {dimensions['depth']:.2f}mm")
            print(f"  Origin: ({dimensions['min_x']:.2f}, {dimensions['min_y']:.2f})")
            print(f"  Max point: ({dimensions['max_x']:.2f}, {dimensions['max_y']:.2f})")
        
        # Basic assertions
        self.assertTrue(success)
        self.assertIsNotNone(dimensions)
        self.assertIn('width', dimensions)
        self.assertIn('height', dimensions)
        self.assertIn('depth', dimensions)
        self.assertGreater(dimensions['width'], 0)
        self.assertGreater(dimensions['height'], 0)
    
    def test_identify_orientation(self):
        """Test identification of workpiece orientation."""
        # Get boundaries first
        success, boundaries, _ = self.extractor.extract_workpiece_boundaries(self.doc)
        if not success:
            self.skipTest("Could not extract workpiece boundaries")
        
        # Identify orientation
        success, orientation, message = self.extractor.identify_orientation(self.doc, boundaries)
        
        # Print results for debugging
        print(f"\nOrientation identification: {'Success' if success else 'Failed'}")
        print(f"Message: {message}")
        
        if success:
            print("Workpiece orientation:")
            print(f"  Aligned with origin: {orientation['origin_aligned']}")
            print(f"  Aligned with axes: {orientation['axis_aligned']}")
            print(f"  Angle to X-axis: {orientation['angle_to_x_axis']}")
            print(f"  Origin offset: ({orientation['origin_offset_x']:.2f}, {orientation['origin_offset_y']:.2f})")
        
        # Basic assertions
        self.assertTrue(success)
        self.assertIsNotNone(orientation)
        self.assertIn('origin_aligned', orientation)
        self.assertIn('axis_aligned', orientation)
    
    def test_get_reference_points(self):
        """Test extraction of reference points."""
        # Get boundaries first
        success, boundaries, _ = self.extractor.extract_workpiece_boundaries(self.doc)
        if not success:
            self.skipTest("Could not extract workpiece boundaries")
        
        # Get reference points
        success, points, message = self.extractor.get_reference_points(self.doc, boundaries)
        
        # Print results for debugging
        print(f"\nReference point extraction: {'Success' if success else 'Failed'}")
        print(f"Message: {message}")
        
        if success:
            print("Reference points:")
            for point_name, coordinates in points.items():
                print(f"  {point_name}: ({coordinates[0]:.2f}, {coordinates[1]:.2f})")
        
        # Basic assertions
        self.assertTrue(success)
        self.assertIsNotNone(points)
        self.assertIn('origin', points)
        self.assertIn('center', points)
        self.assertIn('corner_bl', points)
        self.assertIn('corner_tr', points)
    
    def test_extract_workpiece_info(self):
        """Test complete extraction of workpiece info."""
        # Extract all info in one call
        success, info, message = self.extractor.extract_workpiece_info(self.doc)
        
        # Print results for debugging
        print(f"\nComplete workpiece info extraction: {'Success' if success else 'Failed'}")
        print(f"Message: {message}")
        
        if success:
            print("Workpiece information:")
            print(f"  Dimensions: {info['dimensions']['width']:.2f} x {info['dimensions']['height']:.2f} x {info['dimensions']['depth']:.2f}mm")
            print(f"  Aligned with origin: {info['orientation']['origin_aligned']}")
            print(f"  Aligned with axes: {info['orientation']['axis_aligned']}")
            print(f"  Boundary count: {info['boundary_count']}")
            print(f"  Material thickness: {info['material_thickness']:.2f}mm")
        
        # Basic assertions
        self.assertTrue(success)
        self.assertIsNotNone(info)
        self.assertIn('dimensions', info)
        self.assertIn('orientation', info)
        self.assertIn('reference_points', info)
        self.assertIn('boundary_count', info)

if __name__ == '__main__':
    unittest.main()