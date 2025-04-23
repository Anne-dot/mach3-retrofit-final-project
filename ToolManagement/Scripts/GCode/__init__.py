"""
Package name: GCode
Purpose: G-code generation for CNC horizontal drilling operations.

This package contains modules for generating safe and efficient G-code
from drilling point data, applying safety constraints, and integrating
with the machine tool data system.

Modules:
- code_generator.py: Core G-code generation functionality
- safety_checker.py: Implements safety constraints
- tool_validator.py: Validates tool compatibility
- path_planner.py: Plans safe and efficient tool paths
- drilling_operations.py: Specialized horizontal drilling code generation
- preprocessor.py: G-code preprocessing and enhancement
- formatter.py: G-code formatting and organization

References:
- MRFP-80: DXF to G-code Generation Epic
- Preprocessor Safety Check Requirements (knowledge base)
- DRO to G-Code Variables Mapping (knowledge base)
"""

# Imports and exports will be added as the modules are implemented
# Import key items to make them available at package level
# These will be uncommented as the modules are implemented
# from .code_generator import generate_gcode, create_header, create_footer
# from .safety_checker import add_safety_checks, validate_movement
# from .tool_validator import validate_tool_for_operation
# from .path_planner import plan_drilling_sequence, optimize_path
# from .drilling_operations import generate_horizontal_drill
# from .preprocessor import preprocess_gcode, insert_safety_checks
# from .formatter import format_gcode, add_section_comments

# Define publicly available items - will expand as modules are implemented
__all__ = []