"""
Module for generating safe tool paths for CNC operations.

This module focuses on creating safe and efficient tool paths for
different CNC operations, particularly drilling. It generates the
complete sequence of movements needed for each operation type.

Functions:
    calculate_safe_heights: Calculates safe Z heights for different operations
    calculate_drilling_paths: Generates complete drilling approach paths
    calculate_approach_point: Determines safe approach positions

References:
    - MRFP-80: DXF to G-code Generation Epic
"""

import math
import logging
from typing import Tuple, List, Dict, Any, Optional, Union

# Import from Utils package
from Utils.logging_utils import setup_logger, log_exception


class ToolPathGenerator:
    """
    Generates safe tool paths for CNC operations.
    
    This class provides methods for calculating safe approach paths,
    appropriate heights, and complete operation sequences for different
    types of CNC operations.
    """
    
    def __init__(self):
        """Initialize the tool path generator."""
        # Set up logger for this class
        self.logger = setup_logger(__name__)
        
        # Default clearance for operations
        self.clearance_height = 10.0  # mm above workpiece for safe travel
        
        # Default workpiece thickness if not specified
        self.default_thickness = 22.5  # mm
        
        # Safe approach distance for horizontal drilling
        self.approach_distance = 30.0  # mm from edge for safe positioning
        
        # Initialize workpiece parameters
        self.workpiece_width = 0.0
        self.workpiece_height = 0.0
        self.workpiece_thickness = self.default_thickness
        
        self.logger.info("ToolPathGenerator initialized")
    
    def set_workpiece_parameters(
        self, 
        width: float, 
        height: float, 
        thickness: Optional[float] = None
    ):
        """
        Set workpiece parameters for path generation.
        
        Args:
            width: Workpiece width in mm (X dimension)
            height: Workpiece height in mm (Y dimension)
            thickness: Workpiece thickness in mm (Z dimension, default is 22.5mm)
        """
        self.workpiece_width = float(width)
        self.workpiece_height = float(height)
        self.workpiece_thickness = float(thickness or self.default_thickness)
        
        self.logger.info(
            f"Workpiece parameters set: {self.workpiece_width}mm x "
            f"{self.workpiece_height}mm x {self.workpiece_thickness}mm"
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
                    thickness=dims.get('depth', self.default_thickness)
                )
            self.logger.info("Parameters set from workpiece_info")
        except Exception as e:
            self.logger.error(f"Error setting parameters from workpiece_info: {str(e)}")
    
    def set_clearance_height(self, clearance: float):
        """
        Set the clearance height for safe travel moves.
        
        Args:
            clearance: Clearance height in mm above workpiece surface
        """
        self.clearance_height = float(clearance)
        self.logger.info(f"Clearance height set to {self.clearance_height}mm")
    
    def calculate_safe_heights(
        self, 
        operation_type: str,
        point: Tuple[float, float, float],
        drill_depth: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculate safe Z heights for different operations.
        
        Args:
            operation_type: Type of operation ('vertical_drill', 'horizontal_drill')
            point: Machine coordinates of the operation point
            drill_depth: Depth of drilling operation (if applicable)
            
        Returns:
            Dict: Dictionary with safe Z heights for different phases
        """
        try:
            # Extract coordinates
            x, y, z = point
            
            # Common heights
            safe_travel_z = self.workpiece_thickness + self.clearance_height
            
            # Operation-specific heights
            if operation_type == "vertical_drill":
                safe_rapid_z = self.workpiece_thickness + 2.0  # 2mm above workpiece
                
                # Calculate drill depth if provided
                if drill_depth is not None:
                    drill_to_z = self.workpiece_thickness - drill_depth
                else:
                    drill_to_z = None
                    
                heights = {
                    "safe_travel": safe_travel_z,
                    "safe_rapid": safe_rapid_z,
                    "start_position": self.workpiece_thickness,
                    "drill_to": drill_to_z
                }
                
            elif operation_type == "horizontal_drill":
                # For horizontal drilling, Z is already set correctly
                # Just need to provide safe travel height
                heights = {
                    "safe_travel": safe_travel_z,
                    "operation_z": z
                }
                
            else:
                # Default heights
                heights = {
                    "safe_travel": safe_travel_z
                }
            
            self.logger.debug(f"Calculated safe heights for {operation_type}: {heights}")
            return heights
            
        except Exception as e:
            self.logger.error(f"Error calculating safe heights: {str(e)}")
            # Return basic safe height if calculation fails
            return {"safe_travel": self.workpiece_thickness + self.clearance_height}
    
    def calculate_drilling_paths(
        self,
        operation_type: str,
        point: Tuple[float, float, float],
        direction: Optional[Tuple[float, float, float]] = None,
        drill_depth: Optional[float] = None,
        feed_rate: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate complete drilling paths including approach, operation, and retract.
        
        Args:
            operation_type: Type of operation ('vertical_drill', 'horizontal_drill')
            point: Machine coordinates of the operation point
            direction: Drilling direction vector (for horizontal drilling)
            drill_depth: Depth of drilling operation
            feed_rate: Feed rate for drilling operations (mm/min)
            
        Returns:
            List: List of path segments with coordinates and G-code commands
        """
        try:
            # Extract coordinates
            x, y, z = point
            
            # Get safe heights
            heights = self.calculate_safe_heights(operation_type, point, drill_depth)
            
            # Default feed rate if not specified
            if feed_rate is None:
                feed_rate = 300  # mm/min
            
            # Build path segments based on operation type
            path_segments = []
            
            if operation_type == "vertical_drill":
                # Follow vertical drilling path pattern:
                # 1. Rapid to position at safe height
                path_segments.append({
                    "type": "rapid",
                    "command": "G0",
                    "coordinates": (x, y, heights["safe_travel"]),
                    "comment": "Rapid to position at safe height"
                })
                
                # 2. Rapid to position 2mm above surface
                path_segments.append({
                    "type": "rapid",
                    "command": "G0",
                    "coordinates": (x, y, heights["safe_rapid"]),
                    "comment": "Rapid to safe height above workpiece"
                })
                
                # 3. Move to surface
                path_segments.append({
                    "type": "positioning",
                    "command": "G0",
                    "coordinates": (x, y, heights["start_position"]),
                    "comment": "Position at top of workpiece"
                })
                
                # 4. Drill to depth
                if heights.get("drill_to") is not None:
                    path_segments.append({
                        "type": "drilling",
                        "command": "G1",
                        "coordinates": (x, y, heights["drill_to"]),
                        "feed_rate": feed_rate,
                        "comment": f"Drill to depth ({drill_depth}mm)"
                    })
                
                # 5. Retract to safe height
                path_segments.append({
                    "type": "retract",
                    "command": "G0",
                    "coordinates": (x, y, heights["safe_travel"]),
                    "comment": "Retract to safe height"
                })
                
            elif operation_type == "horizontal_drill":
                # Need direction for horizontal drilling
                if direction is None:
                    direction = (1, 0, 0)  # Default: X+ direction
                
                # Determine approach direction
                approach_x, approach_y = self._calculate_approach_point(x, y, direction)
                
                # Follow horizontal drilling path pattern:
                # 1. Rapid to approach position at safe height
                path_segments.append({
                    "type": "rapid",
                    "command": "G0",
                    "coordinates": (approach_x, approach_y, heights["safe_travel"]),
                    "comment": "Rapid to safe approach position"
                })
                
                # 2. Rapid down to drilling height
                path_segments.append({
                    "type": "rapid",
                    "command": "G0",
                    "coordinates": (approach_x, approach_y, heights["operation_z"]),
                    "comment": "Rapid to drilling height"
                })
                
                # 3. Feed to drilling position
                path_segments.append({
                    "type": "approach",
                    "command": "G1",
                    "coordinates": (x, y, heights["operation_z"]),
                    "feed_rate": feed_rate,
                    "comment": "Approach drilling position"
                })
                
                # 4. Drill to depth
                if drill_depth is not None and direction is not None:
                    # Calculate end point
                    end_x = x + direction[0] * drill_depth
                    end_y = y + direction[1] * drill_depth
                    
                    path_segments.append({
                        "type": "drilling",
                        "command": "G1",
                        "coordinates": (end_x, end_y, heights["operation_z"]),
                        "feed_rate": feed_rate,
                        "comment": f"Drill to depth ({drill_depth}mm)"
                    })
                    
                    # 5. Retract to drilling position
                    path_segments.append({
                        "type": "retract",
                        "command": "G1",
                        "coordinates": (x, y, heights["operation_z"]),
                        "feed_rate": feed_rate * 2,  # Faster retract
                        "comment": "Retract to drilling position"
                    })
                
                # 6. Retract to approach position
                path_segments.append({
                    "type": "retract",
                    "command": "G0",
                    "coordinates": (approach_x, approach_y, heights["operation_z"]),
                    "comment": "Retract to approach position"
                })
                
                # Retract to safe height
                path_segments.append({
                    "type": "retract",
                    "command": "G0",
                    "coordinates": (approach_x, approach_y, heights["safe_travel"]),
                    "comment": "Retract to safe height"
                })
            
            self.logger.debug(f"Calculated {len(path_segments)} path segments for {operation_type}")
            return path_segments
            
        except Exception as e:
            self.logger.error(f"Error calculating drilling paths: {str(e)}")
            return []
    
    def _calculate_approach_point(
        self, 
        x: float, 
        y: float, 
        direction: Tuple[float, float, float]
    ) -> Tuple[float, float]:
        """
        Calculate a safe approach point for horizontal drilling.
        
        Args:
            x: X coordinate of drilling point
            y: Y coordinate of drilling point
            direction: Direction vector of drilling
            
        Returns:
            Tuple: (X, Y) coordinates of approach point
        """
        try:
            # Extract direction components
            dx, dy, dz = direction
            
            # Normalize direction vector (ensure unit length)
            length = math.sqrt(dx*dx + dy*dy + dz*dz)
            if length > 0.0001:  # Avoid division by zero
                dx, dy, dz = dx/length, dy/length, dz/length
            
            # Calculate approach point by moving in the opposite direction of drilling
            approach_x = x - dx * self.approach_distance
            approach_y = y - dy * self.approach_distance
            
            # Check if approach point is inside workpiece bounds
            if 0 <= approach_x <= self.workpiece_width and 0 <= approach_y <= self.workpiece_height:
                # Approach is inside workpiece, try to find an approach from outside
                if abs(dx) > abs(dy):  # X-dominant direction
                    if dx > 0:  # Drilling from left
                        approach_x = 0
                    else:  # Drilling from right
                        approach_x = self.workpiece_width
                else:  # Y-dominant direction
                    if dy > 0:  # Drilling from bottom
                        approach_y = 0
                    else:  # Drilling from top
                        approach_y = self.workpiece_height
            
            # Round to 0.1mm accuracy
            approach_x = round(approach_x, 1)
            approach_y = round(approach_y, 1)
            
            return (approach_x, approach_y)
            
        except Exception as e:
            self.logger.error(f"Error calculating approach point: {str(e)}")
            # Default to original point if calculation fails
            return (round(x, 1), round(y, 1))
    
    def generate_operation_gcode(
        self,
        path_segments: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate actual G-code lines from path segments.
        
        Args:
            path_segments: List of path segment dictionaries
            
        Returns:
            List: List of G-code lines
        """
        try:
            gcode_lines = []
            
            # Add header comment
            gcode_lines.append("(Generated toolpath)")
            
            # Process each segment
            for segment in path_segments:
                # Extract coordinates and command
                x, y, z = segment["coordinates"]
                command = segment["command"]
                comment = segment.get("comment", "")
                
                # Format command based on type
                if segment["type"] in ["rapid", "retract", "positioning"]:
                    # No feed rate for rapid movements
                    code_line = f"{command} X{x:.1f} Y{y:.1f} Z{z:.1f}"
                else:
                    # Include feed rate for cutting/drilling movements
                    feed_rate = segment.get("feed_rate", 300)
                    code_line = f"{command} X{x:.1f} Y{y:.1f} Z{z:.1f} F{feed_rate}"
                
                # Add comment if available
                if comment:
                    code_line += f" ({comment})"
                
                gcode_lines.append(code_line)
            
            self.logger.debug(f"Generated {len(gcode_lines)} lines of G-code")
            return gcode_lines
            
        except Exception as e:
            self.logger.error(f"Error generating G-code: {str(e)}")
            return []


# Only initialize if run directly
if __name__ == "__main__":
    # Simple test
    path_generator = ToolPathGenerator()
    path_generator.set_workpiece_parameters(545.5, 555.0, 22.5)
    
    # Test drilling paths for vertical drilling
    drill_paths = path_generator.calculate_drilling_paths(
        operation_type="vertical_drill",
        point=(35.5, 34.0, 22.5),
        drill_depth=14.0
    )
    print(f"\nVertical drilling paths: {len(drill_paths)} segments")
    for i, segment in enumerate(drill_paths):
        coord = segment['coordinates']
        print(f"  {i+1}: {segment['command']} to ({coord[0]}, {coord[1]}, {coord[2]}) - {segment['comment']}")
    
    # Generate G-code for vertical drilling
    gcode = path_generator.generate_operation_gcode(drill_paths)
    print("\nG-code for vertical drilling:")
    for line in gcode:
        print(f"  {line}")
    
    # Test drilling paths for horizontal drilling
    drill_paths = path_generator.calculate_drilling_paths(
        operation_type="horizontal_drill",
        point=(510.0, 0, 13.0),
        direction=(1, 0, 0),
        drill_depth=21.5
    )
    print(f"\nHorizontal drilling paths: {len(drill_paths)} segments")
    for i, segment in enumerate(drill_paths):
        coord = segment['coordinates']
        print(f"  {i+1}: {segment['command']} to ({coord[0]}, {coord[1]}, {coord[2]}) - {segment['comment']}")
    
    # Generate G-code for horizontal drilling
    gcode = path_generator.generate_operation_gcode(drill_paths)
    print("\nG-code for horizontal drilling:")
    for line in gcode:
        print(f"  {line}")