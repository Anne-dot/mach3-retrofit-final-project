"""
Simple module for analyzing drilling points by tool requirements.

This module takes drilling points and groups them by their tool requirements,
focusing on edge direction and diameter as the key parameters for CNC operations.

Main functions:
- group_by_tool: Groups drilling points by edge/direction and diameter
- analyze_drilling_data: Generates a complete analysis of drilling operations
"""

import math
from typing import List, Dict, Any, Tuple, Set, Union
import numpy as np

# Import from Utils package
from Utils.logging_utils import setup_logger

# Setup logger
logger = setup_logger(__name__)

def vector_to_string(vector: Tuple[float, float, float]) -> str:
    """Convert a vector to a readable string format."""
    if vector is None:
        return "None"
    return f"({vector[0]:.1f}, {vector[1]:.1f}, {vector[2]:.1f})"

def round_vector(vector: Tuple[float, float, float], precision: int = 1) -> Tuple[float, float, float]:
    """Round vector components to specified precision."""
    if vector is None:
        return None
    return (round(vector[0], precision), round(vector[1], precision), round(vector[2], precision))

def detect_edge(vector: Tuple[float, float, float]) -> str:
    """Detect which edge a drilling operation is for based on its direction vector."""
    if vector is None:
        return "UNKNOWN"
    
    # Use a tolerance for comparing vector components
    tolerance = 0.1
    
    # Normalize the vector
    magnitude = math.sqrt(vector[0]**2 + vector[1]**2 + vector[2]**2)
    if magnitude < 0.0001:  # Prevent division by zero
        return "UNKNOWN"
    
    x = vector[0] / magnitude
    y = vector[1] / magnitude
    z = vector[2] / magnitude
    
    # Check if it's a vertical drilling (Z direction)
    if abs(z - 1.0) < tolerance and abs(x) < tolerance and abs(y) < tolerance:
        return "VERTICAL"
    
    # Detect edge based on primary direction
    # For horizontal drilling, one component will be dominant
    if abs(x) > abs(y) and abs(x) > abs(z):
        return "RIGHT" if x > 0 else "LEFT"
    elif abs(y) > abs(x) and abs(y) > abs(z):
        return "BACK" if y > 0 else "FRONT"
    else:
        return "UNKNOWN"

def group_by_tool(drilling_points: List[Any]) -> Dict[str, Any]:
    """
    Group drilling points by tool requirements (edge and diameter).
    
    For horizontal drilling, the edge (front/back/left/right) is the primary 
    grouping factor since different tools are needed for different edges.
    
    Args:
        drilling_points: List of drilling point objects with position, vector and diameter
        
    Returns:
        Dictionary with tool groups, organized by tool characteristics
    """
    logger.info(f"Grouping {len(drilling_points)} drilling points by edge and diameter")
    
    # Initialize results
    tool_groups = {}
    
    # Process each drilling point
    for point in drilling_points:
        # Extract key parameters
        position = getattr(point, 'position', None)
        diameter = round(getattr(point, 'diameter', 0), 1)  # Round to 1 decimal place
        depth = round(getattr(point, 'depth', 0), 1)  # Round to 1 decimal place
        vector = getattr(point, 'extrusion_vector', None)
        layer = getattr(point, 'layer_name', '')
        
        # Skip invalid points
        if position is None or diameter <= 0:
            logger.warning(f"Skipping invalid point: {point}")
            continue
        
        # Round vector components for consistent grouping
        rounded_vector = round_vector(vector)
        
        # Determine edge from vector
        edge = detect_edge(vector)
        
        # Create a key combining edge and diameter
        # For horizontal drilling, edge is critical because different tools
        # are needed for different edges
        key = (edge, diameter)
        
        # Create new group if needed
        if key not in tool_groups:
            tool_groups[key] = {
                'edge': edge,
                'diameter': diameter,
                'points': [],
                'depths': set(),
                'layers': set(),
                'vectors': set(),  # Track unique vectors in this group
                'is_vertical': edge == "VERTICAL"
            }
        
        # Add point to its group
        tool_groups[key]['points'].append(point)
        tool_groups[key]['depths'].add(depth)
        tool_groups[key]['layers'].add(layer)
        
        # Store the vector as a tuple to be hashable for the set
        if rounded_vector is not None:
            tool_groups[key]['vectors'].add(rounded_vector)
    
    # Add count information and finalize each group
    for key, group in tool_groups.items():
        group['count'] = len(group['points'])
        group['depths'] = sorted(list(group['depths']))
        
        # Convert vectors set to list for easier handling
        vectors_list = list(group['vectors'])
        group['vectors'] = vectors_list
        
        # Add a representative vector for display
        if vectors_list:
            group['primary_vector'] = vectors_list[0]
            group['primary_vector_str'] = vector_to_string(vectors_list[0])
        else:
            group['primary_vector'] = None
            group['primary_vector_str'] = "None"
    
    # Sort groups: first by type (vertical/horizontal), then by edge, then by diameter
    sorted_keys = sorted(tool_groups.keys(), 
                         key=lambda k: (0 if tool_groups[k]['is_vertical'] else 1,
                                        tool_groups[k]['edge'], 
                                        tool_groups[k]['diameter']))
    
    sorted_groups = {k: tool_groups[k] for k in sorted_keys}
    
    logger.info(f"Found {len(sorted_groups)} tool groups")
    return sorted_groups

def analyze_drilling_data(drilling_points: List[Any]) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
    """
    Analyze drilling points and group them by tool requirements.
    
    Args:
        drilling_points: List of drilling point objects
        
    Returns:
        Tuple containing:
        - success flag (bool)
        - results dictionary with tool groups and statistics
        - details dictionary with additional information
    """
    if not drilling_points:
        logger.warning("No drilling points to analyze")
        return True, {'tool_groups': {}, 'statistics': {'total_points': 0}}, {}
    
    try:
        # Group points by tool requirements
        tool_groups = group_by_tool(drilling_points)
        
        # Calculate statistics
        vertical_groups = [group for group in tool_groups.values() if group['is_vertical']]
        horizontal_groups = [group for group in tool_groups.values() if not group['is_vertical']]
        
        statistics = {
            'total_points': len(drilling_points),
            'total_groups': len(tool_groups),
            'vertical_groups': len(vertical_groups),
            'horizontal_groups': len(horizontal_groups),
            'vertical_points': sum(group['count'] for group in vertical_groups),
            'horizontal_points': sum(group['count'] for group in horizontal_groups),
        }
        
        # Count points by edge
        edge_counts = {'VERTICAL': 0, 'FRONT': 0, 'BACK': 0, 'LEFT': 0, 'RIGHT': 0, 'UNKNOWN': 0}
        for group in tool_groups.values():
            edge_counts[group['edge']] += group['count']
        
        statistics['edge_counts'] = edge_counts
        
        # Create results dictionary
        results = {
            'tool_groups': tool_groups,
            'statistics': statistics
        }
        
        # Create details dictionary with specific information for each edge
        edge_details = {}
        for edge in ["VERTICAL", "FRONT", "BACK", "LEFT", "RIGHT"]:
            edge_groups = [group for group in tool_groups.values() if group['edge'] == edge]
            if edge_groups:
                edge_details[edge] = {
                    'group_count': len(edge_groups),
                    'point_count': sum(group['count'] for group in edge_groups),
                    'diameters': sorted(set(group['diameter'] for group in edge_groups))
                }
        
        details = {
            'group_count': len(tool_groups),
            'edge_summary': edge_counts,
            'edge_details': edge_details
        }
        
        logger.info(f"Analysis complete: {statistics['total_groups']} tool groups "
                   f"({statistics['vertical_groups']} vertical, {statistics['horizontal_groups']} horizontal)")
        return True, results, details
        
    except Exception as e:
        logger.error(f"Error during drilling analysis: {str(e)}")
        return False, {}, {'error': str(e)}


# Example usage if run directly
if __name__ == "__main__":
    import os
    import sys
    from DXF.file_loader import DxfLoader
    from DXF.drilling_extractor import DrillingExtractor
    from Utils.ui_utils import UIUtils
    
    # Create loader and extractor
    loader = DxfLoader()
    extractor = DrillingExtractor()
    
    # Set up path to test data
    test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Tests", "TestData")
    dxf_dir = os.path.join(test_data_dir, "DXF")
    
    # Let user select a DXF file
    dxf_file_path = UIUtils.select_dxf_file(dxf_dir)
    if not dxf_file_path:
        print("No DXF file selected. Exiting.")
        UIUtils.keep_terminal_open("Test aborted - no file selected.")
        sys.exit(1)
    
    print(f"Using test DXF file: {dxf_file_path}")
    
    # Load DXF file
    UIUtils.print_separator("Loading DXF File")
    success, doc, message = loader.load_dxf(dxf_file_path)
    
    if success:
        print(f"SUCCESS: {message}")
        
        # Extract drilling points
        UIUtils.print_separator("Extracting Drilling Points")
        success, drilling_info, message = extractor.extract_all_drilling_info(doc)
        
        if success:
            print(f"SUCCESS: {message}")
            
            # Analyze drilling points
            UIUtils.print_separator("Analyzing Drilling Points")
            success, results, details = analyze_drilling_data(drilling_info["points"])
            
            if success:
                UIUtils.print_separator("Tool Group Analysis")
                stats = results['statistics']
                print(f"Total points: {stats['total_points']}")
                print(f"Total tool groups: {stats['total_groups']}")
                print(f"Vertical groups: {stats['vertical_groups']} ({stats['vertical_points']} points)")
                print(f"Horizontal groups: {stats['horizontal_groups']} ({stats['horizontal_points']} points)")
                
                UIUtils.print_separator("Tool Groups")
                for i, (key, group) in enumerate(results['tool_groups'].items()):
                    edge, diameter = key
                    print(f"\nTool Group {i+1}: {edge} Edge, {diameter}mm")
                    print(f"  Points: {group['count']}")
                    print(f"  Primary vector: {group['primary_vector_str']}")
                    
                    if len(group['depths']) > 1:
                        print(f"  Multiple depths: {', '.join(f'{d}mm' for d in group['depths'])}")
                    else:
                        print(f"  Depth: {group['depths'][0]}mm")
                    
                    # For horizontal groups, show position examples
                    if not group['is_vertical'] and len(group['points']) > 0:
                        print("  Position examples:")
                        for j, point in enumerate(group['points'][:2]):  # Show first 2 points
                            pos = getattr(point, 'position', None)
                            pos_str = "None" if pos is None else f"({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})"
                            print(f"    {j+1}. {pos_str}")
                        
                        if len(group['points']) > 2:
                            print(f"    ...and {len(group['points']) - 2} more")
                
                UIUtils.print_separator("Edge Summary")
                for edge, count in stats['edge_counts'].items():
                    if count > 0:
                        print(f"  {edge}: {count} points")
                
                # Show detailed information for significant edges
                for edge in ["VERTICAL", "FRONT", "BACK", "LEFT", "RIGHT"]:
                    if edge in details['edge_details']:
                        edge_info = details['edge_details'][edge]
                        if edge_info['point_count'] > 0:
                            print(f"\n{edge} Edge Details:")
                            print(f"  Groups: {edge_info['group_count']}")
                            print(f"  Points: {edge_info['point_count']}")
                            print(f"  Diameters: {', '.join(f'{d}mm' for d in edge_info['diameters'])}")
            else:
                print(f"Analysis failed: {details.get('error', 'Unknown error')}")
        else:
            print(f"Extraction failed: {message}")
    else:
        print(f"Loading failed: {message}")
        
    # Keep terminal open
    UIUtils.keep_terminal_open("Drilling analysis completed.")