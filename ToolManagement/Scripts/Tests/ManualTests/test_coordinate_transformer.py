"""
Simple manual test to verify Z transformation for horizontal drilling points.

This script tests only the Z coordinate transformation for LEFT and RIGHT edges
to verify the formula: Z_machine = workpiece_thickness + Y_dxf
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from DXF.coordinate_transformer import HorizontalDrillTransformer

def test_z_transformation():
    """Test Z coordinate transformation for horizontal drilling."""
    print("\n=== Z Transformation Test for Horizontal Drilling ===\n")
    
    # Create transformer
    transformer = HorizontalDrillTransformer()
    
    # Set workpiece parameters
    print("Setting workpiece parameters...")
    success, message, details = transformer.set_workpiece_parameters(
        width=555.0,      # Example workpiece width
        height=570.0,     # Example workpiece height
        thickness=22.5,   # Example workpiece thickness
        min_x=0.0,        # Bounds min X
        min_y=0.0,        # Bounds min Y
        max_x=555.0,      # Bounds max X
        max_y=570.0       # Bounds max Y
    )
    
    if not success:
        print(f"Failed to set workpiece parameters: {message}")
        return
    
    print(f"Workpiece parameters set: {message}")
    
    # Test cases with various Y values
    test_cases = [
        # (name, y_dxf, expected_z)
        ("Standard case", -9.5, 13.0),   # From the example DXF file
        ("Zero Y", 0.0, 22.5),           # Y=0 should give Z=thickness
        ("Positive Y", 10.0, 32.5),      # Y=10 should give Z=thickness+10
        ("Negative Y", -15.0, 7.5)       # Y=-15 should give Z=thickness-15
    ]
    
    # Test the Z transformation
    print("\n--- Z Transformation Test Results ---")
    print(f"Workpiece thickness: {transformer.thickness} mm")
    print("\nFormula: Z_machine = workpiece_thickness + Y_dxf\n")
    
    for name, y_dxf, expected_z in test_cases:
        z_machine = transformer.transform_z_coordinate(y_dxf)
        result = "✓" if abs(z_machine - expected_z) < 0.01 else "✗"
        
        calculation = f"{transformer.thickness} + ({y_dxf}) = {z_machine}"
        
        print(f"{result} {name}: Y={y_dxf} → Z={z_machine} [{calculation}]")
    
    # Test edge detection
    print("\n--- Edge Detection Test ---")
    
    edge_vectors = [
        # (name, vector, expected_edge)
        ("RIGHT edge", (1.0, 0.0, 0.0), "RIGHT"),
        ("LEFT edge", (-1.0, 0.0, 0.0), "LEFT"),
        ("UNKNOWN edge", (0.0, 1.0, 0.0), "UNKNOWN")
    ]
    
    for name, vector, expected_edge in edge_vectors:
        edge = transformer.detect_edge(vector)
        result = "✓" if edge == expected_edge else "✗"
        print(f"{result} {name}: Vector={vector} → Edge={edge}")
    
    # Test complete transformation
    print("\n--- Complete Transformation Tests ---")
    print("Note: Only Z transformation is fully implemented\n")
    
    drill_points = [
        # (name, point, vector)
        ("LEFT edge point", (-542.0, -9.5, -555.0), (-1.0, 0.0, 0.0)),
        ("RIGHT edge point", (542.0, -9.5, 0.0), (1.0, 0.0, 0.0))
    ]
    
    for name, point, vector in drill_points:
        success, transformed, details = transformer.transform_horizontal_point(point, vector)
        
        if success:
            print(f"{name}:")
            print(f"  Original: {point}")
            print(f"  Vector: {vector}")
            print(f"  Transformed Z: {transformed[2]}")
            print(f"  Edge: {details['edge']}")
            
            # Verify Z transformation
            expected_z = transformer.thickness + point[1]
            z_correct = "✓" if abs(transformed[2] - expected_z) < 0.01 else "✗"
            print(f"  Z Transformation: {z_correct} [{transformer.thickness} + ({point[1]}) = {expected_z}]")
        else:
            print(f"{name}: Transformation failed - {details.get('error', 'Unknown error')}")
        
        print()

    print("=== Test Complete ===")

if __name__ == "__main__":
    test_z_transformation()