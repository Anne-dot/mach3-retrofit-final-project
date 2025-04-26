#!/usr/bin/env python3
"""
Debug test script for drilling_extractor.py

This script runs a step-by-step analysis of the drilling extraction process,
printing detailed information at each stage.
"""

import os
import sys
import time

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import the modules we need
from DXF.file_loader import DxfLoader
from DXF.drilling_extractor import HorizontalDrillPoint, DrillingExtractor

# Print separator for readability
def print_separator(title):
    print("\n" + "="*80)
    print(f" {title} ".center(80, '='))
    print("="*80 + "\n")

# Create a subclass of HorizontalDrillPoint that prints debug info
class DebugHorizontalDrillPoint(HorizontalDrillPoint):
    """Debug version of HorizontalDrillPoint that prints detailed info."""
    
    def extract_common_data(self):
        """Override to add debug prints."""
        print(f"\n>> Processing point on layer: {self.layer_name}")
        
        # Extract position
        super().extract_common_data()
        
        # Print position info
        print(f"  Position after extraction: {self.position}")
        print(f"  Z value: {self.position[2]}")
        
        # Print edge determination info
        print(f"  Edge determined: {self.edge}")
        print(f"  Direction vector: {self.direction_vector}")
        print(f"  Direction: {self.direction}")

# Create a subclass of DrillingExtractor that uses the debug point class
class DebugDrillingExtractor(DrillingExtractor):
    """Debug version of DrillingExtractor."""
    
    def find_drilling_points(self, dxf_doc):
        """Override to use debug drill point class and add prints."""
        print_separator("FINDING DRILLING POINTS")
        
        if dxf_doc is None:
            print("No DXF document provided")
            return False, None, "No DXF document provided"
        
        print("Starting to find drilling points...")
        
        try:
            # Get all entities in modelspace
            modelspace = dxf_doc.modelspace()
            
            # Lists to store found drilling points
            vertical_points = []
            horizontal_points = []
            
            # Look for drilling points
            for entity in modelspace:
                try:
                    # Check if entity is a circle
                    if entity.dxftype() == "CIRCLE":
                        # Get the layer name
                        layer_name = entity.dxf.layer
                        
                        # Check if it's a horizontal drilling point
                        if (self.horz_drill_keyword in layer_name or 
                              any(keyword in layer_name for keyword in self.alt_horz_drill_keywords)):
                            print(f"\nFound horizontal drilling entity on layer: {layer_name}")
                            print(f"  Center: {entity.dxf.center}")
                            
                            # Create debug point
                            try:
                                # Use our debug class instead of regular HorizontalDrillPoint
                                point = DebugHorizontalDrillPoint(entity, layer_name)
                                horizontal_points.append(point)
                                print(f"  Successfully processed point at {point.position}")
                                print(f"  Edge determination result: {point.edge}")
                            except Exception as e:
                                print(f"  Failed to process horizontal point: {str(e)}")
                        
                        # Handle other point types normally
                        elif (self.vert_drill_keyword in layer_name or 
                            any(keyword in layer_name for keyword in self.alt_vert_drill_keywords)):
                            # Just add vertical points normally
                            vertical_points.append(super(DebugDrillingExtractor, self).find_drilling_points)
                except Exception as e:
                    print(f"Failed to process entity: {str(e)}")
                    continue
            
            # Create the points dictionary
            all_points = {
                'vertical': vertical_points,
                'horizontal': horizontal_points
            }
            
            total_points = len(vertical_points) + len(horizontal_points)
            
            if total_points == 0:
                print("No drilling points found!")
                return False, all_points, "No drilling points found"
            
            print(f"\nFound {len(vertical_points)} vertical and {len(horizontal_points)} horizontal drilling points")
            return True, all_points, f"Found {len(vertical_points)} vertical and {len(horizontal_points)} horizontal drilling points"
            
        except Exception as e:
            print(f"Error finding drilling points: {str(e)}")
            return False, {'vertical': [], 'horizontal': []}, f"Error: {str(e)}"

    def extract_all_drilling_info(self, dxf_doc):
        """Override to add prints for drilling info extraction."""
        print_separator("EXTRACTING ALL DRILLING INFO")
        
        # First get drilling points
        success, drilling_points, message = self.find_drilling_points(dxf_doc)
        print(f"Finding drilling points: {'Success' if success else 'Failed'}")
        print(f"Message: {message}")
        
        # Print horizontal point details
        print("\nHorizontal Drilling Points Details:")
        for i, point in enumerate(drilling_points['horizontal']):
            print(f"\nPoint {i+1}:")
            print(f"  Position: {point.position}")
            print(f"  Edge: {point.edge}")
            print(f"  Direction: {point.direction}")
            print(f"  Z value: {point.position[2]}")
        
        print_separator("TESTING Z POSITION EDGE DETECTION")
        # Test Z position directly
        print("Testing Z position edge detection directly:")
        
        for i, point in enumerate(drilling_points['horizontal']):
            # Get the Z position
            z = point.position[2]
            
            print(f"\nPoint {i+1} at {point.position}:")
            print(f"  Z value: {z}")
            print(f"  Z rounded: {round(z, 3)}")
            
            # Manually determine edge based on Z
            edge = "BACK" if z < -500 else "FRONT"
            print(f"  Manual edge determination: {edge}")
            print(f"  Current point.edge: {point.edge}")
            
            # Try alternate check
            alternative_edge = "BACK" if abs(z + 554.998) < 1 else "FRONT"
            print(f"  Alternative check (exact match): {alternative_edge}")
        
        # Continue with normal processing
        print_separator("CONTINUING WITH NORMAL PROCESSING")
        return super().extract_all_drilling_info(dxf_doc)

# Main execution
if __name__ == "__main__":
    # Create loader and find test file
    loader = DxfLoader()
    
    # Try to find a DXF file
    test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "TestData")
    dxf_file_path = os.path.join(test_data_dir, "DXF", "complex_case.dxf")
    
    # Check if file exists
    if not os.path.exists(dxf_file_path):
        print(f"Test file not found: {dxf_file_path}")
        print("Please specify a DXF file path as command line argument")
        if len(sys.argv) > 1:
            dxf_file_path = sys.argv[1]
        else:
            sys.exit(1)
    
    print(f"Using DXF file: {dxf_file_path}")
    
    # Load the DXF file
    print("\nLoading DXF file...")
    success, doc, message = loader.load_dxf(dxf_file_path)
    
    if not success:
        print(f"Failed to load DXF file: {message}")
        sys.exit(1)
    
    print(f"Successfully loaded DXF file: {message}")
    
    # Create debug extractor and run analysis
    extractor = DebugDrillingExtractor()
    success, drilling_info, message = extractor.extract_all_drilling_info(doc)
    
    # At the end, print summary
    print_separator("FINAL RESULTS")
    
    if success:
        print(f"Extraction successful: {message}")
        
        # Print horizontal drilling points grouped by edge
        front_points = []
        back_points = []
        
        for point in drilling_info['parameters']['horizontal']:
            if point['edge'] == "FRONT":
                front_points.append(point)
            elif point['edge'] == "BACK":
                back_points.append(point)
        
        print(f"\nHorizontal Drilling Points by Edge:")
        print(f"  FRONT edge: {len(front_points)} points")
        print(f"  BACK edge: {len(back_points)} points")
        
        # Print groups
        print("\nHorizontal Drilling Groups:")
        for group_key, operations in drilling_info['groups']['horizontal'].items():
            print(f"  Group {group_key}: {len(operations)} operations")
    else:
        print(f"Extraction failed: {message}")
