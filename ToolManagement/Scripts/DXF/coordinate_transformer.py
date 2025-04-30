"""
Module for transforming horizontal drilling coordinates from DXF to machine coordinates.

This module handles the transformation of coordinates from DXF file format to CNC machine 
coordinates specifically for horizontal drilling points on LEFT and RIGHT edges.
"""

from typing import Tuple, Dict, Any, Optional, List, Union
import math

# Import from Utils package
from Utils.logging_utils import setup_logger

# Set up logger
logger = setup_logger(__name__)


class HorizontalDrillTransformer:
    """Transformer for horizontal drilling operations."""
    
    def __init__(self):
        """Initialize the horizontal drill transformer."""
        # Workpiece dimensions
        self.width = 0.0
        self.height = 0.0
        self.thickness = 0.0
        
        # Bounding box
        self.min_x = 0.0
        self.min_y = 0.0
        self.max_x = 0.0
        self.max_y = 0.0
        
        # Rounding precision for output coordinates
        self.precision = 1
        
        logger.info("HorizontalDrillTransformer initialized")
    
    def set_workpiece_parameters(self, width: float, height: float, thickness: float,
                                min_x: float, min_y: float, max_x: float, max_y: float) -> Tuple[bool, str, Dict]:
        """
        Set workpiece parameters for coordinate transformation.
        
        Args:
            width: Workpiece width in mm
            height: Workpiece height in mm
            thickness: Workpiece thickness in mm
            min_x: Minimum X coordinate of workpiece
            min_y: Minimum Y coordinate of workpiece
            max_x: Maximum X coordinate of workpiece
            max_y: Maximum Y coordinate of workpiece
            
        Returns:
            Tuple of (success, message, details)
        """
        # Validate parameters
        if width <= 0 or height <= 0 or thickness <= 0:
            error_msg = "Invalid workpiece dimensions (must be positive)"
            logger.error(error_msg)
            return False, error_msg, {}
        
        # Set workpiece parameters
        self.width = width
        self.height = height
        self.thickness = thickness
        
        # Set bounding box
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        
        success_msg = f"Workpiece parameters set: {width}x{height}x{thickness}mm"
        logger.info(success_msg)
        return True, success_msg, {
            "width": width,
            "height": height,
            "thickness": thickness
        }
    
    def set_from_workpiece_info(self, workpiece_info: Dict) -> Tuple[bool, str, Dict]:
        """
        Set parameters from workpiece info dictionary.
        
        Args:
            workpiece_info: Dictionary with workpiece information
            
        Returns:
            Tuple of (success, message, details)
        """
        try:
            dimensions = workpiece_info.get('dimensions', {})
            
            width = dimensions.get('width', 0.0)
            height = dimensions.get('height', 0.0)
            thickness = dimensions.get('depth', 0.0)
            
            min_x = dimensions.get('min_x', 0.0)
            min_y = dimensions.get('min_y', 0.0)
            max_x = dimensions.get('max_x', 0.0)
            max_y = dimensions.get('max_y', 0.0)
            
            return self.set_workpiece_parameters(
                width, height, thickness, min_x, min_y, max_x, max_y
            )
        except Exception as e:
            error_msg = f"Error setting parameters from workpiece info: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, {}
    
    def detect_edge(self, vector: Tuple[float, float, float]) -> str:
        """
        Detect which edge a drilling point belongs to based on its vector.
        
        Args:
            vector: Extrusion vector (x, y, z)
            
        Returns:
            Edge name: "LEFT", "RIGHT", "FRONT", or "BACK"
        """
        if not vector:
            return "UNKNOWN"
        
        # Normalize vector to handle different vector magnitudes
        magnitude = math.sqrt(vector[0]**2 + vector[1]**2 + vector[2]**2)
        if magnitude < 0.0001:  # Avoid division by zero
            return "UNKNOWN"
        
        x = vector[0] / magnitude
        y = vector[1] / magnitude
        
        # Use tolerance for float comparisons
        tolerance = 0.1
        
        # Detect edge based on dominant component
        if abs(abs(x) - 1.0) < tolerance:
            if x > 0:
                return "RIGHT"
            else:
                return "LEFT"
        elif abs(abs(y) - 1.0) < tolerance:
            if y > 0:
                return "BACK"
            else:
                return "FRONT"
        
        return "UNKNOWN"
    
    def transform_z_coordinate(self, y_dxf: float) -> float:
        """
        Transform the Z coordinate for horizontal drilling.
        
        Formula: Z_machine = workpiece_thickness + Y_dxf
        
        Args:
            y_dxf: Y coordinate from DXF
            
        Returns:
            Z coordinate in machine coordinates
        """
        z_machine = self.thickness + y_dxf
        return round(z_machine, self.precision)
    
    def transform_horizontal_point(self, point: Tuple[float, float, float], 
                                  vector: Tuple[float, float, float]) -> Tuple[bool, Tuple[float, float, float], Dict]:
        """
        Transform a horizontal drilling point from DXF to machine coordinates.
        
        Currently supports LEFT, RIGHT, FRONT, and BACK edges with transformation of Z coordinate.
        X and Y transformations are placeholders pending further specification.
        
        Args:
            point: DXF coordinates (x, y, z)
            vector: Extrusion vector (x, y, z)
            
        Returns:
            Tuple of (success, transformed_point, details)
        """
        if not vector:
            error_msg = "No vector provided for horizontal drilling point"
            logger.error(error_msg)
            return False, (0, 0, 0), {"error": error_msg}
        
        # Extract coordinates
        x_dxf, y_dxf, z_dxf = point
        
        # Detect edge
        edge = self.detect_edge(vector)
        
        # Handle supported edges
        if edge not in ["LEFT", "RIGHT", "FRONT", "BACK"]:
            error_msg = f"Unsupported edge: {edge}"
            logger.error(error_msg)
            return False, (0, 0, 0), {"error": error_msg}
        
        # Transform Z coordinate using the formula: Z_machine = workpiece_thickness + Y_dxf
        # This formula applies to all horizontal drilling edges (LEFT, RIGHT, FRONT, BACK)
        z_machine = self.transform_z_coordinate(y_dxf)
        
        # PLACEHOLDER: X and Y transformations pending further specification
        if edge == "LEFT":
            # X transformation for LEFT edge: X_machine = z_dxf + self.width
            x_machine = z_dxf + self.width
            # Y transformation for LEFT edge: Y_machine = workpiece_height - abs(X_dxf)
            y_machine = self.height - abs(x_dxf)  # NOTE: This formula needs more testing to be verified
        elif edge == "RIGHT":
            # X transformation for RIGHT edge: X_machine = z_dxf + self.width
            x_machine = z_dxf + self.width
            # Y transformation for RIGHT edge: Y_machine = workpiece_height - abs(X_dxf)
            y_machine = self.height - abs(x_dxf)  # NOTE: This formula needs more testing to be verified
        elif edge == "FRONT":
            # Y transformation for FRONT edge: Y_machine = z_dxf + self.height
            x_machine = self.width - abs(x_dxf)  # NOTE: This formula needs more testing to be verified
            y_machine = z_dxf + self.height
        else:  # BACK edge
            # Y transformation for BACK edge: Y_machine = z_dxf + self.height
            x_machine = self.width - abs(x_dxf)  # NOTE: This formula needs more testing to be verified
            y_machine = z_dxf + self.height
        
        # Round coordinates
        x_machine = round(x_machine, self.precision)
        y_machine = round(y_machine, self.precision)
        
        return True, (x_machine, y_machine, z_machine), {
            "edge": edge,
            "workpiece_dimensions": {
                "width": self.width,
                "height": self.height,
                "thickness": self.thickness
            },
            "original_point": point,
            "vector": vector
        }