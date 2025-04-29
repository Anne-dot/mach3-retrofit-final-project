"""
Test Z transformation for horizontal drilling using real DXF files.

This script loads a DXF file, extracts the workpiece dimensions and drilling points,
and verifies the Z transformation formula: Z_machine = workpiece_thickness + Y_dxf
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
from DXF.coordinate_transformer import HorizontalDrillTransformer

# Import from Utils package
from Utils.logging_utils import setup_logger
from Utils.ui_utils import UIUtils

# Set up logger
logger = setup_logger(__name__)

# Set up path to test data
test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "TestData")
dxf_dir = os.path.join(test_data_dir, "DXF")

def test_z_transformation_from_dxf(dxf_file_path=None):
    """
    Test Z transformation for horizontal drilling points extracted from a DXF file.
    
    Args:
        dxf_file_path: Path to DXF file (if None, will prompt for selection)
    """
    print(f"\n=== Z Transformation Test Using DXF File ===")
    print(f"Running on {platform.system()} platform")
    
    # Let user select a DXF file if not provided
    if dxf_file_path is None:
        dxf_file_path = UIUtils.select_dxf_file(dxf_dir)
        if not dxf_file_path:
            print("No DXF file selected. Exiting.")
            return
    
    print(f"Using DXF file: {dxf_file_path}")
    
    # Step 1: Load DXF file
    print("\n--- Loading DXF File ---")
    loader = DxfLoader()
    success, doc, message = loader.load_dxf(dxf_file_path)
    
    if not success:
        print(f"Error loading DXF: {message}")
        return
    
    print(f"Success: {message}")
    
    # Step 2: Extract workpiece info
    print("\n--- Extracting Workpiece Information ---")
    workpiece_extractor = WorkpieceExtractor()
    success, workpiece_info, message = workpiece_extractor.extract_workpiece_info(doc)
    
    if not success:
        print(f"Error extracting workpiece info: {message}")
        return
    
    dimensions = workpiece_info['dimensions']
    print(f"Success: Workpiece dimensions: {dimensions['width']:.2f} x {dimensions['height']:.2f} x {dimensions['depth']:.2f}mm")
    
    # Step 3: Extract drilling info
    print("\n--- Extracting Drilling Points ---")
    drilling_extractor = DrillingExtractor()
    success, drilling_info, message = drilling_extractor.extract_all_drilling_info(doc)
    
    if not success:
        print(f"Error extracting drilling info: {message}")
        return
    
    print(f"Success: Found {drilling_info['count']} drilling points")
    
    # Step 4: Analyze drilling data
    print("\n--- Analyzing Drilling Points ---")
    success, results, details = analyze_drilling_data(drilling_info['points'])
    
    if not success:
        print(f"Error analyzing drilling data: {details.get('error', 'Unknown error')}")
        return
    
    horizontal_points = sum(group['count'] for group in results['tool_groups'].values() 
                           if group['edge'] in ["LEFT", "RIGHT"])
    
    print(f"Success: Identified {len(results['tool_groups'])} tool groups")
    print(f"Found {horizontal_points} horizontal drilling points (LEFT/RIGHT edges)")
    
    # Step 5: Create transformer
    print("\n--- Setting Up Transformer ---")
    transformer = HorizontalDrillTransformer()
    success, message, details = transformer.set_from_workpiece_info(workpiece_info)
    
    if not success:
        print(f"Error setting workpiece parameters: {message}")
        return
    
    print(f"Success: {message}")
    
    # Step 6: Test Z transformation for horizontal drilling points
    print("\n--- Z Transformation Results ---")
    print(f"Workpiece thickness: {transformer.thickness} mm")
    print(f"Formula: Z_machine = workpiece_thickness + Y_dxf\n")
    
    # Process each tool group
    for key, group in results['tool_groups'].items():
        edge, diameter = key
        
        # # Only process LEFT and RIGHT edges
        # if edge not in ["LEFT", "RIGHT"]:
        #     continue
        
        print(f"--- {edge} Edge - {diameter}mm Diameter Group ---")
        print(f"Points: {group['count']}")
        print(f"Vector: {group['primary_vector_str']}\n")
        
        # Process all points in this group
        for i, point in enumerate(group['points']):
            position = point.position
            y_dxf = position[1]
            expected_z = transformer.thickness + y_dxf
            
            # Calculate Z using the transformer
            z_machine = transformer.transform_z_coordinate(y_dxf)
            
            # Format the result
            position_str = f"({position[0]:.1f}, {position[1]:.1f}, {position[2]:.1f})"
            calculation = f"{transformer.thickness} + ({y_dxf}) = {expected_z:.1f}"
            result = "✓" if abs(z_machine - expected_z) < 0.01 else "✗"
            
            print(f"{result} Point {i+1}: {position_str}")
            print(f"  Y={y_dxf} → Z={z_machine} [{calculation}]")
        
        print()
    
    print("=== Test Complete ===")
    
if __name__ == "__main__":
    test_z_transformation_from_dxf()