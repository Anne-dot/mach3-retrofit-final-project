"""
Module for coordinate system transformations.

This module handles conversions between different coordinate systems,
including DXF coordinates to machine coordinates. It focuses solely on
coordinate transformations, not on generating tool paths or operation sequences.

Functions:
    dxf_to_machine_coords: Converts DXF to machine coordinates
    transform_workpiece: Applies transformations to entire workpiece

References:
    - MRFP-80: DXF to G-code Generation Epic
    - MRFP-150: Clarify Workpiece Thickness with Client
"""

import math
from typing import Tuple, Dict, Any, Optional, Union

# Import from Utils package
from Utils.logging_utils import setup_logger, log_exception


class CoordinateTransformer:
    """
    Handles coordinate system transformations for CNC operations.
    
    This class provides methods for converting between DXF and machine
    coordinate systems, focusing on the mathematical transformations
    without handling tool paths or operation sequences.
    """
    
    def __init__(self):
        """Initialize the coordinate transformer."""
        # Set up logger for this class
        self.logger = setup_logger(__name__)
        
        # Default workpiece thickness if not specified
        self.default_thickness = 22.5  # mm - will be clarified in MRFP-150
        
        # Initialize workpiece parameters
        self.workpiece_width = 0.0
        self.workpiece_height = 0.0
        self.workpiece_thickness = self.default_thickness
        
        # Workpiece boundary info
        self.min_x = 0.0
        self.min_y = 0.0
        self.max_x = 0.0
        self.max_y = 0.0
        
        self.logger.info("CoordinateTransformer initialized")
    
    def set_workpiece_parameters(
        self, 
        width: float, 
        height: float, 
        thickness: Optional[float] = None,
        min_x: Optional[float] = None,
        min_y: Optional[float] = None,
        max_x: Optional[float] = None,
        max_y: Optional[float] = None
    ):
        """
        Set workpiece parameters for coordinate transformations.
        
        Args:
            width: Workpiece width in mm (X dimension)
            height: Workpiece height in mm (Y dimension)
            thickness: Workpiece thickness in mm (Z dimension, default is 22.5mm)
            min_x: Minimum X coordinate from DXF
            min_y: Minimum Y coordinate from DXF
            max_x: Maximum X coordinate from DXF
            max_y: Maximum Y coordinate from DXF
        """
        self.workpiece_width = float(width)
        self.workpiece_height = float(height)
        self.workpiece_thickness = float(thickness or self.default_thickness)
        
        # Set boundary coordinates if provided
        if min_x is not None:
            self.min_x = float(min_x)
        if min_y is not None:
            self.min_y = float(min_y)
        if max_x is not None:
            self.max_x = float(max_x)
        if max_y is not None:
            self.max_y = float(max_y)
        
        self.logger.info(
            f"Workpiece parameters set: {self.workpiece_width}mm x "
            f"{self.workpiece_height}mm x {self.workpiece_thickness}mm"
        )
        if min_x is not None and max_y is not None:
            self.logger.info(
                f"Boundary coordinates: ({self.min_x}, {self.min_y}) to "
                f"({self.max_x}, {self.max_y})"
            )
    
    def set_from_workpiece_info(self, workpiece_info: Dict[str, Any]):
        """
        Set parameters from workpiece_info dictionary from workpiece_extractor.
        
        Args:
            workpiece_info: Dictionary with workpiece information
        """
        try:
            if 'dimensions' in workpiece_info:
                dims = workpiece_info['dimensions']
                self.set_workpiece_parameters(
                    width=dims.get('width', 0),
                    height=dims.get('height', 0),
                    thickness=dims.get('depth', self.default_thickness),
                    min_x=dims.get('min_x', 0),
                    min_y=dims.get('min_y', 0),
                    max_x=dims.get('max_x', 0),
                    max_y=dims.get('max_y', 0)
                )
            self.logger.info("Parameters set from workpiece_info")
        except Exception as e:
            self.logger.error(f"Error setting parameters from workpiece_info: {str(e)}")
    
    def dxf_to_machine_coords(
        self, 
        dxf_point: Tuple[float, float, float],
        point_type: str = "general"
    ) -> Tuple[float, float, float]:
        """
        Convert DXF coordinates to machine coordinates.
        
        The transformation depends on the point type:
        - For vertical drilling and general points:
          X_machine = X_dxf - min_x
          Y_machine = min_y - Y_dxf
          Z_machine depends on operation
        
        - For horizontal drilling:
          X_machine = workpiece_width - abs(X_dxf)
          Y_machine = 0 (front edge) or workpiece_height (back edge)
          Z_machine = workpiece_thickness - abs(Y_dxf)
        
        Args:
            dxf_point: Tuple of (X, Y, Z) coordinates from DXF
            point_type: Type of point ('general', 'vertical_drill', 'horizontal_drill')
            
        Returns:
            Tuple: (X, Y, Z) coordinates in machine coordinate system
        """
        try:
            # Extract DXF coordinates
            x_dxf, y_dxf, z_dxf = dxf_point
            
            # Apply transformations based on point type
            if point_type == "horizontal_drill":
                # Horizontal drilling transformation
                x_machine = self.workpiece_width - abs(x_dxf)
                
                # Y transformation based on Z value
                # Z≈0 indicates front edge, Z≈-height indicates back edge
                if abs(z_dxf) < 1.0:  # Front edge
                    y_machine = 0.0
                else:  # Back edge
                    y_machine = self.workpiece_height
                
                # Z transformation (height from bottom, accounting for drilling depth)
                z_machine = self.workpiece_thickness - abs(y_dxf)
                
            else:  # vertical_drill or general
                # Apply offset transformation for vertical drilling
                x_machine = x_dxf - self.min_x
                y_machine = self.min_y - y_dxf
                
                if point_type == "vertical_drill":
                    # Start position at top of workpiece
                    z_machine = self.workpiece_thickness
                else:
                    # Default Z transformation
                    z_machine = z_dxf + self.workpiece_thickness
            
            # Round all coordinates to 0.1mm accuracy
            x_machine = round(x_machine, 1)
            y_machine = round(y_machine, 1)
            z_machine = round(z_machine, 1)
            
            # Log the transformation
            self.logger.debug(
                f"Transformed {point_type} point: "
                f"DXF ({x_dxf}, {y_dxf}, {z_dxf}) → "
                f"Machine ({x_machine}, {y_machine}, {z_machine})"
            )
            
            return (x_machine, y_machine, z_machine)
            
        except Exception as e:
            self.logger.error(f"Error converting coordinates: {str(e)}")
            # Return original coordinates if transformation fails
            return (round(dxf_point[0], 1), round(dxf_point[1], 1), round(dxf_point[2], 1))
    
    def transform_workpiece(
        self,
        workpiece_info: Dict[str, Any],
        rotation: float = 0.0,
        mirror_x: bool = False,
        mirror_y: bool = False
    ) -> Dict[str, Any]:
        """
        Apply transformations to entire workpiece information.
        
        This is useful for rotating or mirroring the entire workpiece
        for different machine setups or orientations.
        
        Args:
            workpiece_info: Dictionary with workpiece information
            rotation: Rotation angle in degrees (clockwise)
            mirror_x: Whether to mirror along X axis
            mirror_y: Whether to mirror along Y axis
            
        Returns:
            Dict: Transformed workpiece information
        """
        try:
            # Create a copy of workpiece_info to avoid modifying the original
            transformed = workpiece_info.copy()
            
            # Calculate rotation in radians
            rotation_rad = math.radians(rotation)
            
            # Check if we need to swap dimensions for 90/270 degree rotations
            swap_dimensions = abs(abs(rotation) - 90) < 0.01 or abs(abs(rotation) - 270) < 0.01
            
            # Update dimensions if needed
            if swap_dimensions and 'dimensions' in workpiece_info:
                # Swap width and height
                width = workpiece_info['dimensions']['height']
                height = workpiece_info['dimensions']['width']
                transformed['dimensions']['width'] = width
                transformed['dimensions']['height'] = height
                
                # Update workpiece parameters
                self.set_workpiece_parameters(
                    width=width,
                    height=height,
                    thickness=workpiece_info['dimensions'].get('depth', self.workpiece_thickness)
                )
            
            # Transform reference points
            if 'reference_points' in workpiece_info:
                transformed_points = {}
                
                for point_name, coords in workpiece_info['reference_points'].items():
                    # Apply transformations
                    x, y = coords
                    
                    # Apply mirroring
                    if mirror_x:
                        x = self.workpiece_width - x
                    if mirror_y:
                        y = self.workpiece_height - y
                    
                    # Apply rotation around the center
                    if rotation != 0:
                        # Translate to origin
                        center_x = self.workpiece_width / 2
                        center_y = self.workpiece_height / 2
                        x_rel = x - center_x
                        y_rel = y - center_y
                        
                        # Rotate
                        x_rot = x_rel * math.cos(rotation_rad) - y_rel * math.sin(rotation_rad)
                        y_rot = x_rel * math.sin(rotation_rad) + y_rel * math.cos(rotation_rad)
                        
                        # Translate back
                        x = x_rot + center_x
                        y = y_rot + center_y
                    
                    transformed_points[point_name] = (round(x, 1), round(y, 1))
                
                transformed['reference_points'] = transformed_points
            
            self.logger.info(f"Transformed workpiece: rotation={rotation}°, mirror_x={mirror_x}, mirror_y={mirror_y}")
            return transformed
            
        except Exception as e:
            self.logger.error(f"Error transforming workpiece: {str(e)}")
            # Return original workpiece_info if transformation fails
            return workpiece_info
    
    def offset_workpiece(
        self,
        workpiece_info: Dict[str, Any],
        offset_x: float = 0.0,
        offset_y: float = 0.0,
        offset_z: float = 0.0
    ) -> Dict[str, Any]:
        """
        Apply an offset to the entire workpiece.
        
        This function shifts all reference points by the specified offset
        while maintaining the workpiece dimensions.
        
        Args:
            workpiece_info: Dictionary with workpiece information
            offset_x: X-axis offset to apply (mm)
            offset_y: Y-axis offset to apply (mm)
            offset_z: Z-axis offset to apply (mm)
            
        Returns:
            Dict: Offset workpiece information
        """
        try:
            # Create a copy of workpiece_info to avoid modifying the original
            transformed = workpiece_info.copy()
            
            # Apply offset to reference points
            if 'reference_points' in workpiece_info:
                transformed_points = {}
                
                for point_name, coords in workpiece_info['reference_points'].items():
                    # Apply offset
                    x, y = coords
                    new_x = x + offset_x
                    new_y = y + offset_y
                    
                    # Round to 0.1mm accuracy
                    transformed_points[point_name] = (round(new_x, 1), round(new_y, 1))
                
                transformed['reference_points'] = transformed_points
            
            # Update boundary information if present
            if 'dimensions' in workpiece_info and 'min_x' in workpiece_info['dimensions']:
                transformed['dimensions']['min_x'] = workpiece_info['dimensions']['min_x'] + offset_x
                transformed['dimensions']['min_y'] = workpiece_info['dimensions']['min_y'] + offset_y
                transformed['dimensions']['max_x'] = workpiece_info['dimensions']['max_x'] + offset_x
                transformed['dimensions']['max_y'] = workpiece_info['dimensions']['max_y'] + offset_y
            
            self.logger.info(f"Offset workpiece by X:{offset_x}mm Y:{offset_y}mm Z:{offset_z}mm")
            return transformed
            
        except Exception as e:
            self.logger.error(f"Error offsetting workpiece: {str(e)}")
            # Return original workpiece_info if offset fails
            return workpiece_info


# Only initialize if run directly
if __name__ == "__main__":
    # Simple test
    transformer = CoordinateTransformer()
    transformer.set_workpiece_parameters(
        width=545.5, 
        height=555.0, 
        thickness=22.5,
        min_x=0.0,
        min_y=0.0,
        max_x=545.5,
        max_y=555.0
    )
    
    # Test vertical drilling point
    dxf_point = (35.5, 34.0, 0)
    machine_point = transformer.dxf_to_machine_coords(dxf_point, "vertical_drill")
    print(f"Vertical drilling: DXF {dxf_point} → Machine {machine_point}")
    
    # Test horizontal drilling point (front edge)
    dxf_point = (35.5, 9.5, 0)  # Front edge
    machine_point = transformer.dxf_to_machine_coords(dxf_point, "horizontal_drill")
    print(f"Horizontal drilling front: DXF {dxf_point} → Machine {machine_point}")
    
    # Test horizontal drilling point (back edge)
    dxf_point = (35.5, 9.5, -555.0)  # Back edge
    machine_point = transformer.dxf_to_machine_coords(dxf_point, "horizontal_drill")
    print(f"Horizontal drilling back: DXF {dxf_point} → Machine {machine_point}")
    
    # Test workpiece transformation
    workpiece_info = {
        'dimensions': {
            'width': 545.5,
            'height': 555.0,
            'depth': 22.5,
            'min_x': 0.0,
            'min_y': 0.0,
            'max_x': 545.5,
            'max_y': 555.0
        },
        'reference_points': {
            'origin': (0.0, 0.0),
            'center': (272.75, 277.5),
            'corner_tr': (545.5, 0.0),
            'corner_br': (545.5, 555.0)
        }
    }
    
    # Test rotation
    rotated = transformer.transform_workpiece(workpiece_info, rotation=90.0)
    print("\nRotated workpiece:")
    print(f"Original dimensions: {workpiece_info['dimensions']['width']} x {workpiece_info['dimensions']['height']}")
    print(f"Rotated dimensions: {rotated['dimensions']['width']} x {rotated['dimensions']['height']}")
    
    # Test mirroring
    mirrored = transformer.transform_workpiece(workpiece_info, mirror_x=True)
    print("\nMirrored workpiece:")
    print(f"Original corner_tr: {workpiece_info['reference_points']['corner_tr']}")
    print(f"Mirrored corner_tr: {mirrored['reference_points']['corner_tr']}")
    
    # Test offsetting
    offset = transformer.offset_workpiece(workpiece_info, offset_x=10.0, offset_y=-5.0)
    print("\nOffset workpiece:")
    print(f"Original origin: {workpiece_info['reference_points']['origin']}")
    print(f"Offset origin: {offset['reference_points']['origin']}")