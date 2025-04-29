"""
Simple manual test for the drilling analyzer module.

This test runs the simple drilling analyzer on a DXF file and displays complete
results showing all drilling points to verify correct grouping.
"""

import os
import sys
import platform
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import from DXF package
from DXF.file_loader import DxfLoader
from DXF.drilling_extractor import DrillingExtractor
from DXF.drilling_analyzer import analyze_drilling_data

# Import from Utils package
from Utils.logging_utils import setup_logger
from Utils.ui_utils import UIUtils

# Set up logger
logger = setup_logger(__name__)

# Set up path to test data
test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "TestData")
dxf_dir = os.path.join(test_data_dir, "DXF")

def display_tool_groups(results):
    """Display ALL points in each tool group for complete verification."""
    stats = results['statistics']
    UIUtils.print_separator("Tool Group Summary")
    print(f"Total points: {stats['total_points']}")
    print(f"Total tool groups: {stats['total_groups']}")
    print(f"Vertical groups: {stats['vertical_groups']} ({stats['vertical_points']} points)")
    print(f"Horizontal groups: {stats['horizontal_groups']} ({stats['horizontal_points']} points)")
    
    UIUtils.print_separator("Tool Groups - Complete Data")
    for i, (key, group) in enumerate(results['tool_groups'].items()):
        edge, diameter = key
        UIUtils.print_separator(f"Tool Group {i+1}: {edge} Edge, {diameter}mm")
        print(f"Points: {group['count']}")
        print(f"Depths: {', '.join(f'{d}mm' for d in group['depths'])}")
        if group['vectors']:
            print(f"Primary vector: {group['primary_vector_str']}")
        
        # Show ALL points in this group
        print("\nAll points in this group:")
        for j, point in enumerate(group['points']):
            pos = point.position
            pos_str = f"({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})" if pos else "None"
            depth = point.depth
            vector = point.extrusion_vector
            vector_str = "None" if vector is None else f"({vector[0]:.1f}, {vector[1]:.1f}, {vector[2]:.1f})"
            print(f"  {j+1}. Position: {pos_str}, Depth: {depth:.1f}mm, Vector: {vector_str}")

def display_edge_summary(results, details):
    """Display a summary of drilling by edge."""
    UIUtils.print_separator("Edge Summary")
    edge_counts = results['statistics']['edge_counts']
    
    for edge, count in edge_counts.items():
        if count > 0:
            print(f"{edge} Edge: {count} points")
    
    # Show details for edges with points
    for edge in ["VERTICAL", "FRONT", "BACK", "LEFT", "RIGHT"]:
        if edge in details['edge_details']:
            edge_info = details['edge_details'][edge]
            if edge_info['point_count'] > 0:
                UIUtils.print_separator(f"{edge} Edge Details")
                print(f"Groups: {edge_info['group_count']}")
                print(f"Points: {edge_info['point_count']}")
                print(f"Diameters: {', '.join(f'{d}mm' for d in edge_info['diameters'])}")

def display_raw_points(drilling_info):
    """Display ALL raw drilling point data for verification."""
    UIUtils.print_separator("Raw Drilling Points - Complete Data")
    points = drilling_info['points']
    
    print(f"Total drilling points: {len(points)}")
    
    # Show ALL drilling points
    for i, point in enumerate(points):
        UIUtils.print_separator(f"Point {i+1}")
        print(f"Position: {point.position}")
        print(f"Layer: {point.layer_name}")
        print(f"Diameter: {point.diameter}mm")
        print(f"Depth: {point.depth}mm")
        print(f"Extrusion Vector: {point.extrusion_vector}")

def display_points_by_edge(results):
    """Display all points grouped by edge for verification."""
    # Create edge groups
    edge_groups = {}
    
    # Go through all tool groups
    for key, group in results['tool_groups'].items():
        edge, diameter = key
        
        # Initialize edge group if needed
        if edge not in edge_groups:
            edge_groups[edge] = []
        
        # Add all points from this group to the edge group
        edge_groups[edge].extend(group['points'])
    
    # Display points by edge
    for edge, points in edge_groups.items():
        if points:
            UIUtils.print_separator(f"{edge} Edge - All {len(points)} Points")
            for i, point in enumerate(points):
                pos = point.position
                pos_str = f"({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})" if pos else "None"
                print(f"{i+1}. {pos_str}, D={point.diameter:.1f}mm, Depth={point.depth:.1f}mm")

print("=== Simple Drilling Analyzer Test ===")
print(f"Running on {platform.system()} platform")

# Let user select a DXF file
dxf_file_path = UIUtils.select_dxf_file(dxf_dir)
if not dxf_file_path:
    print("No DXF file selected. Exiting.")
    UIUtils.keep_terminal_open("Test aborted - no file selected.")
    sys.exit(1)

print(f"Using test DXF file: {dxf_file_path}")

# Step 1: Load the DXF file
UIUtils.print_separator("Step 1: Loading DXF File")
loader = DxfLoader()
success, doc, message = loader.load_dxf(dxf_file_path)

if not success:
    print(f"Error loading DXF: {message}")
    UIUtils.keep_terminal_open("Test failed at DXF loading stage.")
    sys.exit(1)

print(f"SUCCESS: {message}")

# Step 2: Extract drilling points
UIUtils.print_separator("Step 2: Extracting Drilling Points")
extractor = DrillingExtractor()
success, drilling_info, message = extractor.extract_all_drilling_info(doc)

if not success:
    print(f"Error extracting drilling info: {message}")
    UIUtils.keep_terminal_open("Test failed at drilling extraction stage.")
    sys.exit(1)

print(f"SUCCESS: {message}")

# Step 3: Analyze drilling points
UIUtils.print_separator("Step 3: Analyzing Drilling Points")
success, results, details = analyze_drilling_data(drilling_info['points'])

if not success:
    print(f"Error analyzing drilling points: {details.get('error', 'Unknown error')}")
    UIUtils.keep_terminal_open("Test failed at drilling analysis stage.")
    sys.exit(1)

print(f"SUCCESS: Found {results['statistics']['total_groups']} tool groups")

# Show initial summary
UIUtils.print_separator("Initial Results Summary")
print(f"Total points: {results['statistics']['total_points']}")
print(f"Tool groups: {results['statistics']['total_groups']}")
print(f"Vertical groups: {results['statistics']['vertical_groups']} ({results['statistics']['vertical_points']} points)")
print(f"Horizontal groups: {results['statistics']['horizontal_groups']} ({results['statistics']['horizontal_points']} points)")

print("\nEdge distribution:")
for edge, count in results['statistics']['edge_counts'].items():
    if count > 0:
        print(f"- {edge}: {count} points")

# User choice menu
while True:
    UIUtils.print_separator("Options")
    print("1. Show ALL raw drilling points")
    print("2. Show ALL points grouped by tool")
    print("3. Show ALL points grouped by edge")
    print("4. Show edge summary")
    print("5. Exit test")
    
    choice = input("\nSelect an option (1-5): ")
    
    if choice == "1":
        display_raw_points(drilling_info)
    elif choice == "2":
        display_tool_groups(results)
    elif choice == "3":
        display_points_by_edge(results)
    elif choice == "4":
        display_edge_summary(results, details)
    elif choice == "5":
        break
    else:
        print("Invalid selection")

# Keep terminal open until user presses a key
UIUtils.keep_terminal_open("Drilling analysis completed successfully.")