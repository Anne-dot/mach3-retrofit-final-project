"""
Module for validating tool compatibility with operations.

This module ensures that the correct tools are used for each operation,
checking tool types, directions, and other parameters against operation
requirements to prevent incorrect tool usage.

Functions:
    validate_tool_for_operation(tool_data, operation_type): Checks tool suitability
    check_drill_direction(drill_type, operation_direction): Validates drill alignment
    validate_tool_parameters(tool_data, hole_specs): Checks tool parameters match requirements
    suggest_compatible_tool(available_tools, operation): Suggests appropriate tool

References:
    - MRFP-80: DXF to G-code Generation Epic
    - Unified CSV Structure for Tool Management (knowledge base)
    - Tool Data Validation Rules (knowledge base)
"""

class ToolValidator:
    """Class for validating tool compatibility with operations."""
    pass