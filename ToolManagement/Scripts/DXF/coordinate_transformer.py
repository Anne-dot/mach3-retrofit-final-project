"""
Modular coordinate transformation system for MVP.

This module provides specialized transformer classes for coordinate transformations
in the CNC machining context. For the MVP, focuses on workpiece transformation
with proper Y-axis inversion to convert from DXF coordinates (bottom-left origin)
to machine coordinates (top-left origin).

Each transformer has a single responsibility, making the code more maintainable
and easier to extend with additional transformation types in the future.
"""

from typing import Tuple, Dict, Any, Optional, List

# Import from Utils package - centralized utility functions
from Utils.logging_utils import setup_logger, log_exception
from Utils.error_utils import ErrorHandler, BaseError, ErrorCategory, ErrorSeverity
#from Utils.validation_utils import ValidationUtils     #not implemented yet
from Utils.path_utils import PathUtils


class TransformationError(BaseError):
    """Error related to coordinate transformation operations."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.TRANSFORMATION,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        value: Any = None,
        details: Dict[str, Any] = None
    ):
        """
        Initialize TransformationError.
        
        Args:
            message: Error message
            category: Error category
            severity: Error severity
            value: Problematic value (optional)
            details: Additional error details (optional)
        """
        super().__init__(
            message=message,
            category=category,
            severity=severity,
            details=details or {}
        )
        if value is not None:
            self.details["value"] = value


class BaseTransformer:
    """
    Base class for all coordinate transformers.
    
    Provides common functionality and interface for all transformers,
    ensuring consistent behavior across the system.
    """
    
    def __init__(self):
        """Initialize the base transformer."""
        # Set up logger for this class
        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")
        
        # Default workpiece parameters
        self.workpiece_width = 0.0
        self.workpiece_height = 0.0
        self.workpiece_thickness = 22.5  # Default thickness in mm
        
        # Workpiece boundary info
        self.min_x = 0.0
        self.min_y = 0.0
        self.max_x = 0.0
        self.max_y = 0.0
        
        self.logger.info(f"{self.__class__.__name__} initialized")
    
    def set_workpiece_parameters(
        self, 
        width: float, 
        height: float, 
        thickness: Optional[float] = None,
        min_x: Optional[float] = None,
        min_y: Optional[float] = None,
        max_x: Optional[float] = None,
        max_y: Optional[float] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
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
            
        Returns:
            Tuple containing:
                - Success flag (bool)
                - Message (str)
                - Details dictionary (Dict[str, Any])
        """
        try:
            # Set parameters
            self.workpiece_width = float(width)
            self.workpiece_height = float(height)
            
            if thickness is not None:
                self.workpiece_thickness = float(thickness)
            
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
            
            # Return success response
            return ErrorHandler.create_success_response(
                message="Workpiece parameters set successfully",
                data={
                    "width": self.workpiece_width,
                    "height": self.workpiece_height,
                    "thickness": self.workpiece_thickness,
                    "boundary": {
                        "min_x": self.min_x,
                        "min_y": self.min_y,
                        "max_x": self.max_x,
                        "max_y": self.max_y
                    }
                }
            )
            
        except Exception as e:
            log_exception(self.logger, "Error setting workpiece parameters", e)
            return ErrorHandler.from_exception(e)
    
    def set_from_workpiece_info(self, workpiece_info: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Set parameters from workpiece_info dictionary from workpiece_extractor.
        
        Args:
            workpiece_info: Dictionary with workpiece information
            
        Returns:
            Tuple containing:
                - Success flag (bool)
                - Message (str)
                - Details dictionary (Dict[str, Any])
        """
        try:
            if not isinstance(workpiece_info, dict):
                return ErrorHandler.create_error_response(
                    TransformationError(
                        message="Invalid workpiece_info parameter - must be a dictionary",
                        category=ErrorCategory.VALIDATION,
                        severity=ErrorSeverity.ERROR
                    )
                )
                
            if 'dimensions' not in workpiece_info:
                return ErrorHandler.create_error_response(
                    TransformationError(
                        message="Missing dimensions in workpiece_info",
                        category=ErrorCategory.VALIDATION,
                        severity=ErrorSeverity.ERROR
                    )
                )
                
            dims = workpiece_info['dimensions']
            result = self.set_workpiece_parameters(
                width=dims.get('width', 0),
                height=dims.get('height', 0),
                thickness=dims.get('depth', self.workpiece_thickness),
                min_x=dims.get('min_x', 0),
                min_y=dims.get('min_y', 0),
                max_x=dims.get('max_x', 0),
                max_y=dims.get('max_y', 0)
            )
            
            self.logger.info("Parameters set from workpiece_info")
            return result
                
        except Exception as e:
            log_exception(self.logger, "Error setting parameters from workpiece_info", e)
            return ErrorHandler.from_exception(e)
    
    def round_coordinates(self, coords: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """
        Round coordinates to 0.1mm precision.
        
        Args:
            coords: Tuple of (X, Y, Z) coordinates
            
        Returns:
            Tuple of rounded coordinates
        """
        return (round(coords[0], 1), round(coords[1], 1), round(coords[2], 1))


class WorkpieceTransformer(BaseTransformer):
    """
    Transforms entire workpiece information.
    
    Handles overall workpiece transformations, specifically Y-axis inversion
    to convert from DXF coordinates (bottom-left origin) to machine coordinates
    (top-left origin).
    """
    
    def transform_workpiece(
        self,
        workpiece_info: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
        """
        Transform workpiece information to machine coordinates with 0.1mm rounding.
        
        The primary transformation is Y-axis inversion:
        - DXF uses bottom-left origin
        - Machine uses top-left origin
        
        This inverts Y coordinates for boundaries and reference points,
        with all values rounded to 0.1mm precision.
        
        Args:
            workpiece_info: Dictionary with workpiece information
            
        Returns:
            Tuple containing:
                - Success flag (bool)
                - Transformed workpiece information (Dict[str, Any])
                - Details dictionary (Dict[str, Any])
        """
        try:
            # Validate input
            if not isinstance(workpiece_info, dict):
                return ErrorHandler.create_error_response(
                    TransformationError(
                        message="Invalid workpiece_info parameter - must be a dictionary",
                        category=ErrorCategory.PROCESSING,
                        severity=ErrorSeverity.ERROR
                    )
                )
            
            # Create a copy of workpiece_info to avoid modifying the original
            transformed = workpiece_info.copy()
            
            # Transform dimensions if they exist
            if 'dimensions' in workpiece_info:
                transformed['dimensions'] = workpiece_info['dimensions'].copy()
                
                # Transform min_y and max_y (invert Y axis)
                if 'min_y' in transformed['dimensions'] and 'max_y' in transformed['dimensions']:
                    # Store original values
                    min_y = transformed['dimensions']['min_y']
                    max_y = transformed['dimensions']['max_y']
                    
                    # Invert Y (machine uses top-left origin) and round to 0.1mm
                    transformed['dimensions']['min_y'] = round(-max_y, 1)
                    transformed['dimensions']['max_y'] = round(-min_y, 1)
                    
                    # Also round other dimension values
                    for key in ['min_x', 'max_x', 'width', 'height', 'depth']:
                        if key in transformed['dimensions']:
                            transformed['dimensions'][key] = round(transformed['dimensions'][key], 1)
            
            # Transform reference points if they exist
            if 'reference_points' in workpiece_info:
                transformed['reference_points'] = {}
                
                for point_name, coords in workpiece_info['reference_points'].items():
                    # Invert Y coordinate and round both X and Y to 0.1mm
                    x, y = coords
                    transformed['reference_points'][point_name] = (round(x, 1), round(-y, 1))
            
            self.logger.info("Transformed workpiece to machine coordinates (Y inverted with 0.1mm rounding)")
            
            # Create details dictionary with original and transformed boundaries
            details = {
                "transformation_type": "Y-axis inversion with 0.1mm rounding",
                "orientation": "Machine uses top-left origin"
            }
            
            if 'dimensions' in transformed:
                dims = workpiece_info['dimensions']
                tdims = transformed['dimensions']
                
                # Log boundaries for debugging
                self.logger.info(
                    f"DXF Boundary: ({dims.get('min_x', 0)}, {dims.get('min_y', 0)}) "
                    f"to ({dims.get('max_x', 0)}, {dims.get('max_y', 0)})"
                )
                self.logger.info(
                    f"Machine Boundary: ({tdims.get('min_x', 0)}, {tdims.get('min_y', 0)}) "
                    f"to ({tdims.get('max_x', 0)}, {tdims.get('max_y', 0)})"
                )
                
                # Add boundaries to details
                details["original_boundary"] = {
                    "min_x": dims.get('min_x', 0),
                    "min_y": dims.get('min_y', 0),
                    "max_x": dims.get('max_x', 0),
                    "max_y": dims.get('max_y', 0)
                }
                details["transformed_boundary"] = {
                    "min_x": tdims.get('min_x', 0),
                    "min_y": tdims.get('min_y', 0),
                    "max_x": tdims.get('max_x', 0),
                    "max_y": tdims.get('max_y', 0)
                }
                
            return True, transformed, details
            
        except Exception as e:
            log_exception(self.logger, "Error transforming workpiece", e)
            error_response = ErrorHandler.from_exception(e)
            # Return original workpiece_info with the error
            return error_response[0], workpiece_info, error_response[2]


class EdgeTransformer:
    """Base class for edge-specific transformations."""
    
    def __init__(self):
        """Initialize the edge transformer."""
        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")
    
    def transform(self, point, workpiece_dims):
        """Transform a point based on edge type."""
        raise NotImplementedError("Subclasses must implement transform")
    
    def _round_point(self, x, y, z):
        """Round coordinates to 0.1mm precision."""
        return (round(x, 1), round(y, 1), round(z, 1))


class FrontEdgeTransformer(EdgeTransformer):
    """Handles front edge drilling transformations."""
    
    def transform(self, point, workpiece_dims):
        """Transform front edge drilling point."""
        x, y, z = point
        
        # Front edge transformation - based on test results
        transformed_x = workpiece_dims['width'] - abs(x)  # Mirror and subtract from width
        transformed_y = -workpiece_dims['height']  # Bottom of workpiece (Y inverted)
        transformed_z = workpiece_dims['depth'] - abs(y)  # Z is material thickness minus drill depth
        
        return self._round_point(transformed_x, transformed_y, transformed_z)


class BackEdgeTransformer(EdgeTransformer):
    """Handles back edge drilling transformations."""
    
    def transform(self, point, workpiece_dims):
        """Transform back edge drilling point."""
        x, y, z = point
        
        # Back edge transformation - based on test results
        transformed_x = workpiece_dims['width'] - abs(x)  # Mirror and subtract from width
        transformed_y = 0.0  # Top of workpiece (Y inverted)
        transformed_z = workpiece_dims['depth'] - abs(y)  # Z is material thickness minus drill depth
        
        return self._round_point(transformed_x, transformed_y, transformed_z)


class LeftEdgeTransformer(EdgeTransformer):
    """Handles left edge drilling transformations."""
    
    def transform(self, point, workpiece_dims):
        """Transform left edge drilling point."""
        x, y, z = point
        
        # Left edge transformation
        transformed_x = 0.0  # Left edge of workpiece
        transformed_y = -abs(x)  # Y position is the X position from DXF (must be negative)
        transformed_z = workpiece_dims['depth'] - abs(y)  # Z is material thickness minus drill depth
        
        return self._round_point(transformed_x, transformed_y, transformed_z)


class RightEdgeTransformer(EdgeTransformer):
    """Handles right edge drilling transformations."""
    
    def transform(self, point, workpiece_dims):
        """Transform right edge drilling point."""
        x, y, z = point
        
        # Right edge transformation
        transformed_x = workpiece_dims['width']  # Right edge of workpiece
        transformed_y = -abs(x)  # Y position is the X position from DXF (must be negative)
        transformed_z = workpiece_dims['depth'] - abs(y)  # Z is material thickness minus drill depth
        
        return self._round_point(transformed_x, transformed_y, transformed_z)


class HorizontalDrillTransformer(BaseTransformer):
    """
    Specialized transformer for horizontal drilling operations.
    
    Transforms horizontal drilling points from DXF to machine coordinates,
    handling specific requirements for edge drilling.
    """
    
    def __init__(self):
        """Initialize with edge-specific transformers."""
        super().__init__()
        # Initialize edge-specific transformers
        self.edge_transformers = {
            "front": FrontEdgeTransformer(),
            "back": BackEdgeTransformer(),
            "left": LeftEdgeTransformer(),
            "right": RightEdgeTransformer()
        }
    
    def transform_point(
        self, 
        dxf_point: Tuple[float, float, float],
        edge: str = "auto"
    ) -> Tuple[bool, Tuple[float, float, float], Dict[str, Any]]:
        """
        Transform a horizontal drilling point from DXF to machine coordinates.
        
        Args:
            dxf_point: Tuple of (X, Y, Z) coordinates from DXF
            edge: Which edge to drill from ('front', 'back', 'left', 'right', or 'auto')
            
        Returns:
            Tuple containing:
                - Success flag (bool)
                - Machine coordinates (Tuple[float, float, float])
                - Details dictionary (Dict[str, Any])
        """
        try:
            # Validate input
            if not isinstance(dxf_point, tuple) or len(dxf_point) != 3:
                return ErrorHandler.create_error_response(
                    TransformationError(
                        message="Invalid dxf_point - must be a tuple of 3 coordinates",
                        category=ErrorCategory.VALIDATION,
                        severity=ErrorSeverity.ERROR
                    )
                )
            
            # Auto-detect edge if not specified
            detected_edge = edge
            if edge == "auto":
                detected_edge = self.detect_edge(dxf_point)
            
            # Get workpiece dimensions
            workpiece_dims = {
                "width": self.workpiece_width,
                "height": self.workpiece_height,
                "depth": self.workpiece_thickness
            }
            
            # Transform point using edge-specific transformer
            if detected_edge in self.edge_transformers:
                transformer = self.edge_transformers[detected_edge]
                transformed_point = transformer.transform(dxf_point, workpiece_dims)
                
                self.logger.info(
                    f"Transformed horizontal drilling point ({detected_edge} edge): "
                    f"DXF {dxf_point} → Machine {transformed_point}"
                )
                
                return True, transformed_point, {
                    "edge": detected_edge,
                    "original_point": dxf_point
                }
            else:
                # Fallback to front edge if unknown
                self.logger.warning(f"Unknown edge type: {detected_edge}, using front edge")
                transformer = self.edge_transformers["front"]
                transformed_point = transformer.transform(dxf_point, workpiece_dims)
                
                return True, transformed_point, {
                    "edge": "front",
                    "original_point": dxf_point,
                    "warning": f"Unknown edge '{detected_edge}', defaulted to front edge"
                }
            
        except Exception as e:
            log_exception(self.logger, "Error transforming horizontal drilling point", e)
            error_response = ErrorHandler.from_exception(e)
            return False, self.round_coordinates(dxf_point), error_response[2]
    
    def detect_edge(self, point: Tuple[float, float, float]) -> str:
        """
        Detect which edge a point belongs to based on its Z coordinate.
        
        Args:
            point: Tuple of (X, Y, Z) coordinates from DXF
            
        Returns:
            str: Edge type ("front", "back", "left", "right")
        """
        x, y, z = point
        
        # Determine edge based on Z value (standard approach)
        if abs(z) < 1.0:
            return "front"
        elif abs(z + self.workpiece_height) < 1.0:
            return "back"
        
        # Default to front edge if unknown
        return "front"
    
    def transform_points(
        self,
        points: List[Dict[str, Any]]
    ) -> Tuple[bool, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Transform a list of horizontal drilling points.
        
        Args:
            points: List of drilling point dictionaries
            
        Returns:
            Tuple containing:
                - Success flag (bool)
                - List of transformed points (List[Dict[str, Any]])
                - Details dictionary (Dict[str, Any])
        """
        try:
            transformed_points = []
            success_count = 0
            failure_count = 0
            
            for point in points:
                try:
                    # Extract position from point dictionary
                    position = point.get('position', (0, 0, 0))
                    
                    # Transform the point
                    success, machine_coords, details = self.transform_point(position)
                    
                    if success:
                        # Copy original point and update with machine coordinates
                        transformed_point = point.copy()
                        transformed_point['machine_coordinates'] = machine_coords
                        transformed_point['edge'] = details.get('edge', 'unknown')
                        
                        transformed_points.append(transformed_point)
                        success_count += 1
                    else:
                        # Include original point with error info
                        point['transformation_error'] = details.get('message', 'Unknown error')
                        transformed_points.append(point)
                        failure_count += 1
                        
                except Exception as e:
                    # Handle individual point errors
                    log_exception(self.logger, f"Error transforming point {point}", e)
                    point['transformation_error'] = str(e)
                    transformed_points.append(point)
                    failure_count += 1
            
            return True, transformed_points, {
                "points_count": len(points),
                "success_count": success_count,
                "failure_count": failure_count
            }
            
        except Exception as e:
            log_exception(self.logger, "Error transforming drilling points", e)
            error_response = ErrorHandler.from_exception(e)
            return False, points, error_response[2]


class VerticalDrillTransformer(BaseTransformer):
    """
    Specialized transformer for vertical drilling operations.
    
    This is a placeholder for future implementation.
    In MVP, focuses on horizontal drilling only.
    """
    
    def transform_point(
        self, 
        dxf_point: Tuple[float, float, float]
    ) -> Tuple[bool, Tuple[float, float, float], Dict[str, Any]]:
        """
        Transform a vertical drilling point from DXF to machine coordinates.
        
        Placeholder for future implementation - not used in MVP.
        
        Args:
            dxf_point: Tuple of (X, Y, Z) coordinates from DXF
            
        Returns:
            Tuple containing:
                - Success flag (bool)
                - Machine coordinates (Tuple[float, float, float])
                - Details dictionary (Dict[str, Any])
        """
        self.logger.info("VerticalDrillTransformer.transform_point placeholder called")
        
        # Return placeholder success with original point and a note about future implementation
        return True, dxf_point, {
            "status": "placeholder",
            "message": "Vertical drilling transformation will be implemented in future versions"
        }
    
    def transform_points(
        self,
        points: List[Dict[str, Any]]
    ) -> Tuple[bool, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Transform a list of vertical drilling points.
        
        Placeholder for future implementation - not used in MVP.
        
        Args:
            points: List of drilling point dictionaries
            
        Returns:
            Tuple containing:
                - Success flag (bool)
                - List of transformed points (List[Dict[str, Any]])
                - Details dictionary (Dict[str, Any])
        """
        self.logger.info("VerticalDrillTransformer.transform_points placeholder called")
        
        # Return placeholder success with original points and a note about future implementation
        return True, points, {
            "status": "placeholder",
            "message": "Vertical drilling transformation will be implemented in future versions",
            "points_count": len(points)
        }


class TransformerFactory:
    """
    Factory for creating appropriate transformer instances.
    
    This ensures a single source of truth for creating transformers
    and makes it easy to add new transformer types in the future.
    """
    
    @staticmethod
    def create_transformer(transformer_type: str) -> Tuple[bool, BaseTransformer, Dict[str, Any]]:
        """
        Create a transformer of the specified type.
        
        Args:
            transformer_type: Type of transformer to create
                ('workpiece', 'horizontal_drill', 'vertical_drill')
                
        Returns:
            Tuple containing:
                - Success flag (bool)
                - Transformer instance (BaseTransformer)
                - Details dictionary (Dict[str, Any])
        """
        logger = setup_logger("TransformerFactory")
        
        try:
            if transformer_type == "workpiece":
                logger.info("Creating WorkpieceTransformer")
                return True, WorkpieceTransformer(), {
                    "transformer_type": transformer_type,
                    "class": "WorkpieceTransformer"
                }
            elif transformer_type == "horizontal_drill":
                logger.info("Creating HorizontalDrillTransformer")
                return True, HorizontalDrillTransformer(), {
                    "transformer_type": transformer_type,
                    "class": "HorizontalDrillTransformer"
                }
            elif transformer_type == "vertical_drill":
                logger.info("Creating VerticalDrillTransformer")
                return True, VerticalDrillTransformer(), {
                    "transformer_type": transformer_type,
                    "class": "VerticalDrillTransformer"
                }
            else:
                logger.warning(f"Unknown transformer type: {transformer_type}, using WorkpieceTransformer")
                return True, WorkpieceTransformer(), {
                    "transformer_type": "workpiece",
                    "class": "WorkpieceTransformer",
                    "warning": f"Unknown type '{transformer_type}', defaulted to workpiece"
                }
        except Exception as e:
            log_exception(logger, f"Error creating transformer of type '{transformer_type}'", e)
            error_response = ErrorHandler.from_exception(e)
            # Return default transformer with error info
            return False, WorkpieceTransformer(), {
                "error": error_response[1],
                "details": error_response[2]
            }


# Example usage
if __name__ == "__main__":
    # Test the HorizontalDrillTransformer
    success, transformer, details = TransformerFactory.create_transformer("horizontal_drill")
    
    if not success:
        print(f"Error creating transformer: {details.get('error', 'Unknown error')}")
        exit(1)
        
    print(f"Created transformer: {details['class']}")
    
    # Set up example workpiece
    success, message, param_details = transformer.set_workpiece_parameters(
        width=545.5, 
        height=555.0, 
        thickness=22.5,
        min_x=0.0,
        min_y=0.0,
        max_x=545.5,
        max_y=555.0
    )
    
    if success:
        print(f"Workpiece parameters set: {message}")
        
        # Test front edge point
        front_point = (-517.5, -9.5, 0.0)  # Front edge
        success, transformed_front, details_front = transformer.transform_point(front_point)
        
        if success:
            print(f"\nFront edge point:")
            print(f"  Original: {front_point}")
            print(f"  Transformed: {transformed_front}")
            print(f"  Edge: {details_front.get('edge', 'unknown')}")
        
        # Test back edge point
        back_point = (517.5, -9.5, -555.0)  # Back edge
        success, transformed_back, details_back = transformer.transform_point(back_point)
        
        if success:
            print(f"\nBack edge point:")
            print(f"  Original: {back_point}")
            print(f"  Transformed: {transformed_back}")
            print(f"  Edge: {details_back.get('edge', 'unknown')}")
        
    else:
        print(f"Error setting workpiece parameters: {message}")