"""
Simplified test script for coordinate transformations with origin offset.

This script shows:
1. Workpiece dimensions
2. Original DXF coordinates
3. Transformed machine coordinates
4. Coordinates with origin offset applied
"""

import sys
import os
import platform
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import from DXF package
from DXF.file_loader import DxfLoader
from DXF.drilling_extractor import DrillingExtractor
from DXF.workpiece_extractor import WorkpieceExtractor
from DXF.drilling_analyzer import analyze_drilling_data
from DXF.coordinate_transformer import HorizontalDrillTransformer, OriginOffsetTransformer

# Import from Utils package
from Utils.logging_utils import setup_logger
from Utils.ui_utils import UIUtils

# Set up logger
logger = setup_logger(__name__)

# Set up path to test data
test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "TestData")
dxf_dir = os.path.join(test_data_dir, "DXF")

def test_transformation_with_offset(dxf_file_path=None):
    """
    Run a test showing coordinate transformations with origin offset.
    
    Args:
        dxf_file_path: Path to DXF file (if None, will prompt for selection)
    """
    print(f"\n=== Coordinate Transformation Test With Origin Offset ===")
    print(f"Running on {platform.system()} platform")
    
    # Let user select a DXF file if not provided
    if dxf_file_path is None:
        dxf_file_path = UIUtils.select_dxf_file(dxf_dir)
        if not dxf_file_path:
            print("No DXF file selected. Exiting.")
            return
    
    print(f"Using DXF file: {os.path.basename(dxf_file_path)}")
    
    # Load DXF file
    loader = DxfLoader()
    success, doc, message = loader.load_dxf(dxf_file_path)
    if not success:
        print(f"Error loading DXF: {message}")
        return
    
    # Extract workpiece info
    workpiece_extractor = WorkpieceExtractor()
    success, workpiece_info, message = workpiece_extractor.extract_workpiece_info(doc)
    if not success:
        print(f"Error extracting workpiece info: {message}")
        return
    
    dimensions = workpiece_info['dimensions']
    print(f"\n--- Workpiece Dimensions ---")
    print(f"Width: {dimensions['width']:.1f}mm")
    print(f"Height: {dimensions['height']:.1f}mm")
    print(f"Thickness: {dimensions['depth']:.1f}mm")
    
    # Extract drilling info
    drilling_extractor = DrillingExtractor()
    success, drilling_info, message = drilling_extractor.extract_all_drilling_info(doc)
    if not success:
        print(f"Error extracting drilling info: {message}")
        return
    
    # Analyze drilling data
    success, results, details = analyze_drilling_data(drilling_info['points'])
    if not success:
        print(f"Error analyzing drilling data: {details.get('error', 'Unknown error')}")
        return
    
    # Create transformers
    transformer = HorizontalDrillTransformer()
    success, message, details = transformer.set_from_workpiece_info(workpiece_info)
    if not success:
        print(f"Error setting workpiece parameters: {message}")
        return
    
    # Create origin offset transformer
    origin_transformer = OriginOffsetTransformer(dimensions['height'])
    
    # Process each tool group
    print(f"\n--- Coordinate Transformations by Edge Type ---")
    
    for key, group in results['tool_groups'].items():
        edge, diameter = key
        
        # Skip vertical drilling points
        if edge == "VERTICAL":
            continue
        
        print(f"\n{edge.upper()} EDGE - {diameter}mm Diameter Group:")
        print(f"Vector: {group['primary_vector_str']}")
        print(f"{'#':<3} {'DXF Point (X, Y, Z)':<30} {'Machine Point (X, Y, Z)':<30} {'With Origin Offset (X, Y, Z)':<30}")
        print(f"{'-'*3} {'-'*30} {'-'*30} {'-'*30}")
        
        # Process all points in this group
        for i, point in enumerate(group['points']):
            position = point.position
            x_dxf, y_dxf, z_dxf = position
            
            # Get the vector for this group
            vector = group['primary_vector']
            
            # Calculate actual values using the transformer
            success, transformed, details = transformer.transform_horizontal_point(position, vector)
            
            if success:
                # Apply origin offset
                offset_success, offset_point, offset_details = origin_transformer.transform_point(transformed)
                
                # Format output
                x_machine, y_machine, z_machine = transformed
                dxf_str = f"({x_dxf:.1f}, {y_dxf:.1f}, {z_dxf:.1f})"
                machine_str = f"({x_machine:.1f}, {y_machine:.1f}, {z_machine:.1f})"
                
                if offset_success:
                    x_offset, y_offset, z_offset = offset_point
                    offset_str = f"({x_offset:.1f}, {y_offset:.1f}, {z_offset:.1f})"
                else:
                    offset_str = f"ERROR: {offset_details.get('error', 'Unknown error')}"
                
                print(f"{i+1:<3} {dxf_str:<30} {machine_str:<30} {offset_str:<30}")
            else:
                print(f"{i+1:<3} {str(position):<30} ERROR: {details.get('error', 'Unknown error')}")
    
    print("\n=== Test Complete ===")
    
if __name__ == "__main__":
    test_transformation_with_offset()