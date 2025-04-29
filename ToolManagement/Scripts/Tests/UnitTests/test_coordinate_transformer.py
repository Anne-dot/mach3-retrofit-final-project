"""
Unit test for coordinate transformation system.

This module tests the coordinate transformers by validating transformations
against known expected results for both front and back edge drilling points.
"""

import unittest
from pathlib import Path
import sys
import os

# Find the Scripts directory (where DXF package is)
# Starting from the test file's directory, go up two levels to reach Scripts/
scripts_dir = Path(__file__).resolve().parent.parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.append(str(scripts_dir))
    
# Verify path was added correctly
print(f"Added to path: {scripts_dir}")
print(f"Full sys.path: {sys.path}")

# Now import the modules
from DXF.coordinate_transformer import TransformerFactory, HorizontalDrillTransformer
from Utils.logging_utils import setup_logger

class TestCoordinateTransformer(unittest.TestCase):
    """Test case for coordinate transformation system."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create logger for test
        self.logger = setup_logger(__name__)
        
        # Sample workpiece dimensions based on real data
        self.workpiece_info = {
            'dimensions': {
                'width': 545.5,
                'height': 555.0,
                'depth': 22.5,
                'min_x': 0.0,
                'min_y': 0.0,
                'max_x': 545.5,
                'max_y': 555.0
            }
        }
        
        # Test drilling points based on real data from manual test
        self.test_points = [
            # Format: (x, y, z, expected_edge)
            (-517.5, -9.5, 0.0, "front"),           # Point 1: Front edge
            (-67.5, -9.5, 0.0, "front"),            # Point 2: Front edge
            (517.5, -9.5, -555.0, "back"),          # Point 3: Back edge
            (67.5, -9.5, -555.0, "back"),           # Point 4: Back edge
            (-485.5, -9.5, 0.0, "front"),           # Point 5: Front edge
            (-35.5, -9.5, 0.0, "front"),            # Point 6: Front edge
            (485.5, -9.5, -555.0, "back"),          # Point 7: Back edge
            (35.5, -9.5, -555.0, "back")            # Point 8: Back edge
        ]
        
        # Expected transformed coordinates based on manual test results
        # Format: (expected_x, expected_y, expected_z)
        self.expected_results = [
            (28.0, -555.0, 13.0),    # Point 1: front edge
            (478.0, -555.0, 13.0),   # Point 2: front edge
            (28.0, 0.0, 13.0),       # Point 3: back edge
            (478.0, 0.0, 13.0),      # Point 4: back edge
            (60.0, -555.0, 13.0),    # Point 5: front edge
            (510.0, -555.0, 13.0),   # Point 6: front edge
            (60.0, 0.0, 13.0),       # Point 7: back edge
            (510.0, 0.0, 13.0)       # Point 8: back edge
        ]
        
        # Create transformer using factory
        success, self.transformer, details = TransformerFactory.create_transformer("horizontal_drill")
        self.assertTrue(success, f"Failed to create transformer: {details}")
        
        # Set workpiece parameters
        success, message, details = self.transformer.set_workpiece_parameters(
            width=self.workpiece_info['dimensions']['width'],
            height=self.workpiece_info['dimensions']['height'],
            thickness=self.workpiece_info['dimensions']['depth'],
            min_x=self.workpiece_info['dimensions']['min_x'],
            min_y=self.workpiece_info['dimensions']['min_y'],
            max_x=self.workpiece_info['dimensions']['max_x'],
            max_y=self.workpiece_info['dimensions']['max_y']
        )
        self.assertTrue(success, f"Failed to set workpiece parameters: {message}")
    
    def test_edge_detection(self):
        """Test edge detection logic."""
        self.logger.info("Testing edge detection logic")
        
        for i, (x, y, z, expected_edge) in enumerate(self.test_points):
            # Test edge detection
            detected_edge = self.transformer.detect_edge((x, y, z))
            
            # Log the test case
            self.logger.info(f"Point {i+1}: ({x}, {y}, {z}) → Expected edge: {expected_edge}, Detected: {detected_edge}")
            
            # Assert the detected edge matches expected edge
            self.assertEqual(detected_edge, expected_edge, 
                             f"Edge detection failed for point {i+1}: ({x}, {y}, {z})")
    
    def test_point_transformation(self):
        """Test transformation of individual points."""
        self.logger.info("Testing point transformation")
        
        for i, ((x, y, z, _), expected) in enumerate(zip(self.test_points, self.expected_results)):
            # Transform the point
            success, transformed, details = self.transformer.transform_point((x, y, z))
            
            # Log the test case
            self.logger.info(f"Point {i+1}: Original: ({x}, {y}, {z}) → Expected: {expected}, Got: {transformed}")
            
            # Assert the transformation succeeded
            self.assertTrue(success, f"Transformation failed for point {i+1}: {details}")
            
            # Assert the transformed coordinates match expected values
            self.assertEqual(transformed, expected, 
                             f"Transformation incorrect for point {i+1}")
    
    def test_points_transformation(self):
        """Test transformation of multiple points."""
        self.logger.info("Testing points transformation")
        
        # Create a list of point dictionaries (similar to what drilling_extractor would provide)
        point_dicts = [
            {"position": (x, y, z), "diameter": 8.0, "depth": y} 
            for x, y, z, _ in self.test_points
        ]
        
        # Transform all points
        success, transformed_points, details = self.transformer.transform_points(point_dicts)
        
        # Assert transformation succeeded
        self.assertTrue(success, f"Points transformation failed: {details}")
        
        # Check all points were transformed
        self.assertEqual(len(transformed_points), len(self.test_points), 
                         "Not all points were transformed")
        
        # Verify each transformed point
        for i, (point_dict, expected) in enumerate(zip(transformed_points, self.expected_results)):
            # Extract machine coordinates
            machine_coords = point_dict.get('machine_coordinates')
            
            # Log the test case
            self.logger.info(f"Point {i+1}: Got: {machine_coords}, Expected: {expected}")
            
            # Assert machine coordinates match expected values
            self.assertEqual(machine_coords, expected, 
                             f"Points transformation incorrect for point {i+1}")
    
    def test_manual_calculation(self):
        """Test manual calculation against transformer results."""
        self.logger.info("Testing manual calculation vs transformer")
        
        for i, (x, y, z, _) in enumerate(self.test_points):
            # Determine edge based on Z value (close to -height indicates back edge)
            edge = "back" if abs(z + self.workpiece_info['dimensions']['height']) < 1.0 else "front"
            
            # Apply transformation formulas manually
            transformed_x = self.workpiece_info['dimensions']['width'] - abs(x)
            transformed_y = -self.workpiece_info['dimensions']['height'] if edge == "front" else 0.0
            transformed_z = self.workpiece_info['dimensions']['depth'] - abs(y)
            
            # Round to 0.1mm
            transformed_x = round(transformed_x, 1)
            transformed_y = round(transformed_y, 1)
            transformed_z = round(transformed_z, 1)
            
            # Get transformer result
            success, transformed, details = self.transformer.transform_point((x, y, z))
            
            # Log comparison
            self.logger.info(f"Point {i+1}: Manual: ({transformed_x}, {transformed_y}, {transformed_z}), Transformer: {transformed}")
            
            # Assert manual calculation matches transformer result
            self.assertEqual((transformed_x, transformed_y, transformed_z), transformed,
                           f"Manual calculation doesn't match transformer for point {i+1}")


if __name__ == '__main__':
    unittest.main()
