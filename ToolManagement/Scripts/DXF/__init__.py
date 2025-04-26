"""
Package name: DXF
Purpose: DXF file processing for CNC horizontal drilling.

This package contains modules for reading and processing DXF files,
extracting drilling points, and preparing data for G-code generation.

Modules:
- file_loader.py: Loading and validating DXF files
- workpiece_extractor.py: Extracting workpiece geometry
- drilling_extractor.py: Finding drilling points and parameters
- tool_extractor.py: Identifying tool requirements
- entity_processor.py: Processing different entity types
- geometry.py: Geometric calculations
- coordinate_utils.py: Coordinate transformations

Conventions:
- Z-coordinate values in DXF entities determine the drilling edge:
  - Z values near 0: FRONT edge (drilling direction Y+)
  - Z values near -555: BACK edge (drilling direction Y-)

References:
- MRFP-80: DXF to G-code Generation Epic
- Python Code Structure and Organization (knowledge base)
"""
# Imports and exports will be added as the modules are implemented
# Import key items to make them available at package level
# These will be uncommented as the modules are implemented
# from .file_loader import load_dxf, is_valid_dxf
# from .workpiece_extractor import extract_workpiece_boundaries, calculate_dimensions
# from .drilling_extractor import find_drilling_points, determine_drilling_direction
# from .tool_extractor import determine_required_tools
# from .entity_processor import process_entity
# from .geometry import calculate_distance, calculate_angle
# from .coordinate_utils import dxf_to_machine_coords
# Define publicly available items - will expand as modules are implemented
__all__ = []