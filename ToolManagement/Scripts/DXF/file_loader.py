"""
Module for loading and validating DXF files.

This module handles the initial loading of DXF files, validation of file
format, and provides the basic file object that other modules will use
for data extraction. It isolates file I/O operations from data processing.

Functions:
    load_dxf(file_path): Loads and validates a DXF file
    is_valid_dxf(file_path): Checks if file is a valid DXF
    get_dxf_info(dxf_doc): Returns basic information about the DXF file

References:
    - MRFP-80: DXF to G-code Generation Epic
"""

class DxfLoader:
    """Class for loading and validating DXF files."""
    pass