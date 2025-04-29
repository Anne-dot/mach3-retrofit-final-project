"""
Test for extraction-only drilling module.

This module demonstrates the extraction-only approach where drilling points
are collected without any classification.
"""

import os
import sys
import platform
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import from DXF package
from DXF.file_loader import DxfLoader
from DXF.drilling_extractor import DrillingExtractor

# Import from Utils package
from Utils.logging_utils import setup_logger
from Utils.ui_utils import UIUtils

# Set up logger
logger = setup_logger(__name__)

# Set up path to test data
test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "TestData")
dxf_dir = os.path.join(test_data_dir, "DXF")

def analyze_drilling_point(point, index):
    """Analyze and display all available data for a drilling point."""
    UIUtils.print_separator(f"Drilling Point #{index+1}")
    
    # Display position and layer
    print(f"Position: {point.position}")
    print(f"Layer: {point.layer_name}")
    
    # Display entity type
    print(f"Entity type: {point.entity_type}")
    
    # Display drilling parameters
    print(f"Diameter: {point.diameter}mm")
    print(f"Depth: {point.depth}mm")
    
    # Display extrusion vector (critical for direction detection)
    print(f"Extrusion vector: {point.extrusion_vector}")
    
    # Display raw entity attributes
    if hasattr(point, 'entity') and point.entity is not None:
        print("\nEntity DXF attributes:")
        try:
            # Get all DXF attributes
            dxf_attrs = vars(point.entity.dxf)
            for key, value in dxf_attrs.items():
                if not key.startswith('_'):  # Skip private attributes
                    print(f"  {key}: {value}")
        except Exception as e:
            print(f"  Error accessing entity attributes: {str(e)}")

print("=== Extraction-Only Drilling Point Test ===")
print(f"Running on {platform.system()} platform")

# Let user select a DXF file
dxf_file_path = UIUtils.select_dxf_file(dxf_dir)
if not dxf_file_path:
    print("No DXF file selected. Exiting.")
    UIUtils.keep_terminal_open("Test aborted - no file selected.")
    sys.exit(1)

print(f"Using test DXF file: {dxf_file_path}")

# Create loader and extractor
loader = DxfLoader()
extractor = DrillingExtractor()

# Step 1: Load the DXF file
print("\nStep 1: Loading DXF file...")
success, doc, message = loader.load_dxf(dxf_file_path)

if not success:
    print(f"Error loading DXF: {message}")
    UIUtils.keep_terminal_open("Test failed at DXF loading stage.")
    sys.exit(1)

print(f"SUCCESS: DXF loaded successfully: {message}")

# Step 2: Extract drilling information (without classification)
print("\nStep 2: Extracting drilling information...")
success, drilling_info, message = extractor.extract_all_drilling_info(doc)

if not success:
    print(f"Error extracting drilling info: {message}")
    UIUtils.keep_terminal_open("Test failed at drilling extraction stage.")
    sys.exit(1)

print(f"SUCCESS: {message}")

# Step 3: Display all extracted drilling points
UIUtils.print_separator("Extracted Drilling Points")

for i, point in enumerate(drilling_info['points']):
    analyze_drilling_point(point, i)

# Keep terminal open until user presses a key
UIUtils.keep_terminal_open("All drilling data has been analyzed and displayed.")