"""
Module for extracting workpiece geometry from DXF files.

This module identifies and extracts the workpiece boundaries, dimensions,
and orientation from DXF files. It provides the physical properties of the
stock material needed for proper machining operations.

References:
    - MRFP-80: DXF to G-code Generation Epic
    - MRFP-129: Extract Workpiece Dimensions
"""

import re
import math
from typing import List, Dict, Tuple, Optional, Any, Union

# Import from Utils package
from Utils.logging_utils import setup_logger, log_exception


class WorkpieceExtractor:
    """Class for extracting workpiece geometry from DXF files."""
    
    def __init__(self):
        """Initialize the workpiece extractor."""
        # Set up logger for this class
        self.logger = setup_logger(__name__)
        
        # Layer keywords for identifying workpiece boundaries
        self.panel_keyword = "PANEL"
        self.outline_keyword = "OUTLINE"
        
        # Alternative keywords for different naming conventions
        self.alt_panel_keywords = ["MATERIAL", "STOCK", "WORKPIECE"]
        self.alt_outline_keywords = ["PROFILE", "BOUNDARY", "CONTOUR", "BORDER"]
        
        # Regular expressions for extracting information from layer names
        self.thickness_pattern = r"T(\d+\.?\d*)"  # Matches T followed by a number (e.g., T22.5)
        self.panel_thickness_pattern = r"(\d+)mm"  # Matches a number followed by mm (e.g., 22mm)
        
        # Tolerance settings for geometric detection
        self.POSITION_TOLERANCE = 0.1   # 0.1mm tolerance for position detection
        self.ANGLE_TOLERANCE = 0.01     # Angular tolerance for rectangular detection
        self.AREA_TOLERANCE = 0.05      # 5% tolerance for area comparison
        
        # Default thickness if none can be determined
        self.DEFAULT_THICKNESS = 20.0  # Default 20mm material thickness
        
        self.logger.info("WorkpieceExtractor initialized")
    
    def extract_workpiece_boundaries(self, dxf_doc):
        """
        Extract the workpiece boundary entities from the DXF document.
        
        Identifies closed polylines on PANEL or OUTLINE layers that represent
        the workpiece boundaries.
        
        Args:
            dxf_doc: ezdxf document object
            
        Returns:
            tuple: (success, boundaries, message) where:
                - success is a boolean indicating if boundaries were found
                - boundaries is a list of boundary entities or None if not found
                - message contains success details or error information
        """
        if dxf_doc is None:
            error_msg = "No DXF document provided"
            self.logger.error(error_msg)
            return False, None, error_msg
        
        self.logger.info("Extracting workpiece boundaries")
        
        try:
            # Get all entities in modelspace
            modelspace = dxf_doc.modelspace()
            
            # Lists to store found boundaries
            panel_boundaries = []
            outline_boundaries = []
            other_closed_polylines = []  # For fallback
            
            # Look for closed polylines on relevant layers
            for entity in modelspace:
                try:
                    # Check if entity is a polyline
                    if entity.dxftype() == "POLYLINE" or entity.dxftype() == "LWPOLYLINE":
                        # Get the layer name
                        layer_name = entity.dxf.layer if hasattr(entity.dxf, "layer") else ""
                        
                        # Check if it's closed
                        is_closed = self._is_entity_closed(entity)
                        
                        # Only process closed polylines - they represent boundaries
                        if is_closed:
                            # Categorize by layer type
                            if self._is_panel_layer(layer_name):
                                panel_boundaries.append(entity)
                                self.logger.info(f"Found PANEL boundary on layer: {layer_name}")
                            elif self._is_outline_layer(layer_name):
                                outline_boundaries.append(entity)
                                self.logger.info(f"Found OUTLINE boundary on layer: {layer_name}")
                            else:
                                # Store other closed polylines as potential fallbacks
                                other_closed_polylines.append(entity)
                                self.logger.debug(f"Found other closed polyline on layer: {layer_name}")
                except Exception as e:
                    self.logger.warning(f"Error processing entity: {str(e)}")
                    continue
            
            # Combine results, prioritizing panel boundaries, then outline boundaries
            all_boundaries = panel_boundaries + outline_boundaries
            
            # If no explicit boundaries found, use other closed polylines as fallback
            if not all_boundaries and other_closed_polylines:
                self.logger.warning("No explicit workpiece boundaries found, using fallback polylines")
                all_boundaries = other_closed_polylines
            
            if not all_boundaries:
                error_msg = "No workpiece boundaries found in DXF file"
                self.logger.warning(error_msg)
                return False, None, error_msg
            
            success_msg = f"Found {len(all_boundaries)} workpiece boundaries"
            self.logger.info(success_msg)
            return True, all_boundaries, success_msg
        
        except Exception as e:
            error_msg = f"Error extracting workpiece boundaries: {str(e)}"
            log_exception(self.logger, error_msg)
            return False, None, error_msg
    
    def _is_panel_layer(self, layer_name):
        """Check if layer name indicates a panel layer."""
        if not layer_name:
            return False
        
        layer_upper = layer_name.upper()
        if self.panel_keyword in layer_upper:
            return True
            
        # Check alternative keywords
        for keyword in self.alt_panel_keywords:
            if keyword in layer_upper:
                return True
                
        return False
    
    def _is_outline_layer(self, layer_name):
        """Check if layer name indicates an outline layer."""
        if not layer_name:
            return False
            
        layer_upper = layer_name.upper()
        if self.outline_keyword in layer_upper:
            return True
            
        # Check alternative keywords
        for keyword in self.alt_outline_keywords:
            if keyword in layer_upper:
                return True
                
        return False
    
    def _is_entity_closed(self, entity):
        """
        Determine if an entity is closed using various methods.
        
        This handles different polyline types and attribute structures.
        """
        try:
            # Check different attributes for "closed" status
            if hasattr(entity.dxf, "flags"):
                # Bit 0 (value 1) in flags indicates closed polyline
                return bool(entity.dxf.flags & 1)
            elif hasattr(entity.dxf, "closed"):
                return bool(entity.dxf.closed)
            elif hasattr(entity, "is_closed"):
                # For 2D polylines
                return entity.is_closed
            
            # For LWPOLYLINE, check if first and last points match
            if entity.dxftype() == "LWPOLYLINE" and hasattr(entity, "get_points"):
                points = list(entity.get_points())
                if len(points) > 2:
                    return math.isclose(points[0][0], points[-1][0], abs_tol=0.001) and \
                           math.isclose(points[0][1], points[-1][1], abs_tol=0.001)
            
            # For POLYLINE, check if first and last vertices match
            if entity.dxftype() == "POLYLINE" and hasattr(entity, "vertices"):
                vertices = list(entity.vertices)
                if len(vertices) > 2:
                    try:
                        first_x = vertices[0].dxf.location.x
                        first_y = vertices[0].dxf.location.y
                        last_x = vertices[-1].dxf.location.x
                        last_y = vertices[-1].dxf.location.y
                        return math.isclose(first_x, last_x, abs_tol=0.001) and \
                               math.isclose(first_y, last_y, abs_tol=0.001)
                    except AttributeError:
                        # If location doesn't have x/y attributes, try another approach
                        pass
            
            # Default to False if no checks work
            return False
            
        except Exception as e:
            self.logger.warning(f"Error checking if entity is closed: {str(e)}")
            return False  # Default to False on error
    
    def calculate_dimensions(self, boundaries):
        """
        Calculate the workpiece dimensions from boundary entities.
        
        Determines width, height, and depth (thickness) of the workpiece.
        
        Args:
            boundaries: List of boundary entities (polylines)
            
        Returns:
            tuple: (success, dimensions, message) where:
                - success is a boolean indicating if dimensions were calculated
                - dimensions is a dict with 'width', 'height', 'depth' keys
                - message contains success details or error information
        """
        if not boundaries:
            error_msg = "No boundaries provided for dimension calculation"
            self.logger.error(error_msg)
            return False, None, error_msg
        
        self.logger.info("Calculating workpiece dimensions")
        
        try:
            # Use the first boundary for primary dimensions (prioritizing panel boundaries)
            boundary = boundaries[0]
            
            # Initialize min/max values for bounding box calculation
            min_x, min_y, max_x, max_y = float('inf'), float('inf'), float('-inf'), float('-inf')
            
            # Extract vertices
            vertices = self._extract_vertices(boundary)
            
            if not vertices:
                error_msg = "Failed to extract vertices from boundary"
                self.logger.error(error_msg)
                return False, None, error_msg
            
            # Calculate bounding box
            for vertex in vertices:
                try:
                    # Safely extract x, y coordinates
                    x, y = self._extract_vertex_coords(vertex)
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
                except Exception as e:
                    self.logger.warning(f"Error processing vertex: {str(e)}")
                    continue
            
            # Verify we got valid dimensions
            if min_x >= max_x or min_y >= max_y:
                error_msg = "Invalid dimensions calculated (zero or negative size)"
                self.logger.error(error_msg)
                return False, None, error_msg
            
            # Calculate dimensions
            width = max_x - min_x
            height = max_y - min_y
            
            # Get depth/thickness (prioritizing different sources)
            depth = self._get_workpiece_thickness(boundary, boundaries)
            
            # Create dimensions dictionary
            dimensions = {
                'width': width,
                'height': height,
                'depth': depth,
                'min_x': min_x,
                'min_y': min_y,
                'max_x': max_x,
                'max_y': max_y
            }
            
            success_msg = f"Calculated dimensions: {width:.2f} x {height:.2f} x {depth:.2f}mm"
            self.logger.info(success_msg)
            return True, dimensions, success_msg
            
        except Exception as e:
            error_msg = f"Error calculating dimensions: {str(e)}"
            log_exception(self.logger, error_msg)
            return False, None, error_msg
    
    def _extract_vertices(self, boundary):
        """
        Extract vertices from a boundary entity.
        
        Handles different polyline types (POLYLINE, LWPOLYLINE).
        
        Returns:
            list: List of vertex coordinates or objects
        """
        vertices = []
        try:
            entity_type = boundary.dxftype()
            
            if entity_type == "LWPOLYLINE":
                # LWPolyline stores vertices directly
                if hasattr(boundary, "get_points"):
                    vertices = list(boundary.get_points())
                    if not vertices and hasattr(boundary, "points"):
                        # Some ezdxf versions use points attribute
                        vertices = list(boundary.points)
            
            elif entity_type == "POLYLINE":
                # Regular Polyline has separate vertex entities
                if hasattr(boundary, "vertices"):
                    vertices = list(boundary.vertices)
                    
            # If no vertices extracted, try generic approach with get_points
            if not vertices and hasattr(boundary, "get_points"):
                try:
                    vertices = list(boundary.get_points())
                except Exception:
                    pass
                
            # Last resort: check for a points attribute
            if not vertices and hasattr(boundary, "points"):
                vertices = list(boundary.points)
                
            return vertices
            
        except Exception as e:
            self.logger.warning(f"Error extracting vertices: {str(e)}")
            return []
    
    def _extract_vertex_coords(self, vertex):
        """
        Extract x,y coordinates from a vertex.
        
        Handles different vertex representations (tuple, object with dxf.location, etc.)
        
        Returns:
            tuple: (x, y) coordinates
        """
        try:
            # If vertex is already a tuple/list with coordinates
            if isinstance(vertex, (tuple, list)):
                return float(vertex[0]), float(vertex[1])
            
            # If vertex has dxf.location attribute (POLYLINE)
            if hasattr(vertex, "dxf") and hasattr(vertex.dxf, "location"):
                loc = vertex.dxf.location
                if hasattr(loc, "x") and hasattr(loc, "y"):
                    return float(loc.x), float(loc.y)
                elif isinstance(loc, (tuple, list)) and len(loc) >= 2:
                    return float(loc[0]), float(loc[1])
            
            # If vertex has direct x,y attributes
            if hasattr(vertex, "x") and hasattr(vertex, "y"):
                return float(vertex.x), float(vertex.y)
            
            # Handle Vec3/Point3D objects
            if str(type(vertex)).find("Vec3") >= 0 or str(type(vertex)).find("Point") >= 0:
                # Try common attribute patterns for vector objects
                if hasattr(vertex, "x") and hasattr(vertex, "y"):
                    return float(vertex.x), float(vertex.y)
                elif hasattr(vertex, "__getitem__"):
                    return float(vertex[0]), float(vertex[1])
            
            # Last resort, try to convert to string and parse
            str_vertex = str(vertex)
            if "(" in str_vertex and ")" in str_vertex:
                # Extract numbers from "(x, y)" format
                coords = str_vertex.split("(")[1].split(")")[0].split(",")
                if len(coords) >= 2:
                    return float(coords[0]), float(coords[1])
            
            # If nothing works
            raise ValueError(f"Unable to extract coordinates from vertex: {type(vertex)}")
            
        except Exception as e:
            self.logger.warning(f"Error extracting vertex coordinates: {str(e)}")
            raise  # Re-raise to be handled by the caller
    
    def _get_workpiece_thickness(self, primary_boundary, all_boundaries):
        """
        Extract workpiece thickness from boundaries, using prioritized sources.
        
        Priority order:
        1. Attribute 39 from polyline
        2. "T" value from OUTLINE layer name
        3. Numerical info from PANEL layer name
        4. Default thickness
        
        Args:
            primary_boundary: Primary boundary entity
            all_boundaries: List of all boundary entities
            
        Returns:
            float: Thickness value (absolute value, as DXF may use negative values)
        """
        # Default thickness
        thickness = self.DEFAULT_THICKNESS
        
        try:
            # Try to get from attribute 39 first (from any boundary)
            for boundary in all_boundaries:
                # First try direct thickness attribute
                if hasattr(boundary.dxf, "thickness"):
                    try:
                        raw_thickness = boundary.dxf.thickness
                        # Handle ezdxf objects that might not be directly convertible to float
                        if hasattr(raw_thickness, "__abs__"):
                            raw_thickness = abs(raw_thickness)
                        else:
                            raw_thickness = abs(float(raw_thickness))
                            
                        if raw_thickness > 0:
                            thickness = raw_thickness
                            self.logger.info(f"Found thickness from entity thickness attribute: {thickness}mm")
                            return thickness
                    except (TypeError, ValueError):
                        pass
                
                # Try extrusion attribute
                if hasattr(boundary.dxf, "extrusion"):
                    try:
                        extrusion = boundary.dxf.extrusion
                        # Handle different types of extrusion values
                        if isinstance(extrusion, (float, int)):
                            thickness = abs(float(extrusion))
                            self.logger.info(f"Found thickness from entity extrusion (number): {thickness}mm")
                            return thickness
                        elif str(type(extrusion)).find("Vec3") >= 0 or str(type(extrusion)).find("Point") >= 0:
                            # Try to get z component from Vec3/Point3D
                            if hasattr(extrusion, "z"):
                                thickness = abs(float(extrusion.z))
                                self.logger.info(f"Found thickness from entity extrusion object (z): {thickness}mm")
                                return thickness
                            elif hasattr(extrusion, "__getitem__") and len(extrusion) > 2:
                                thickness = abs(float(extrusion[2]))
                                self.logger.info(f"Found thickness from entity extrusion object (index 2): {thickness}mm")
                                return thickness
                    except (TypeError, ValueError, IndexError):
                        pass
                
                # Try custom attribute 39 (extrusion value)
                if hasattr(boundary, "get_dxf_attrib"):
                    try:
                        # Try to get attribute 39 if it exists
                        extrusion = boundary.get_dxf_attrib(39, default=None)
                        if extrusion is not None:
                            if hasattr(extrusion, "__abs__"):
                                thickness = extrusion.__abs__()
                            else:
                                thickness = abs(float(extrusion))
                            self.logger.info(f"Found thickness from custom attribute 39: {thickness}mm")
                            return thickness
                    except Exception:
                        pass
            
            # Try to get from OUTLINE layer name with T value
            for boundary in all_boundaries:
                if hasattr(boundary.dxf, "layer"):
                    layer_name = boundary.dxf.layer
                    if self._is_outline_layer(layer_name):
                        match = re.search(self.thickness_pattern, layer_name)
                        if match:
                            try:
                                thickness = float(match.group(1))
                                self.logger.info(f"Found thickness from OUTLINE layer name: {thickness}mm")
                                return thickness
                            except ValueError:
                                pass
            
            # Try to get from PANEL layer name with mm value
            for boundary in all_boundaries:
                if hasattr(boundary.dxf, "layer"):
                    layer_name = boundary.dxf.layer
                    if self._is_panel_layer(layer_name):
                        match = re.search(self.panel_thickness_pattern, layer_name)
                        if match:
                            try:
                                thickness = float(match.group(1))
                                self.logger.info(f"Found thickness from PANEL layer name: {thickness}mm")
                                return thickness
                            except ValueError:
                                pass
            
            # Default thickness if nothing found
            self.logger.warning(f"Could not determine thickness, using default value of {self.DEFAULT_THICKNESS}mm")
            return thickness
            
        except Exception as e:
            self.logger.warning(f"Error determining thickness: {str(e)}")
            return thickness  # Return default thickness on error
    
    def identify_orientation(self, dxf_doc, boundaries=None):
        """
        Determine the orientation of the workpiece.
        
        Identifies how the workpiece is oriented in the coordinate system,
        which affects tool paths and machining operations.
        
        Args:
            dxf_doc: ezdxf document object
            boundaries: Optional list of boundary entities
            
        Returns:
            tuple: (success, orientation, message) where:
                - success is a boolean indicating if orientation was determined
                - orientation is a dict with orientation information
                - message contains success details or error information
        """
        if dxf_doc is None:
            error_msg = "No DXF document provided"
            self.logger.error(error_msg)
            return False, None, error_msg
        
        try:
            # Get boundaries if not provided
            if boundaries is None:
                success, boundaries, _ = self.extract_workpiece_boundaries(dxf_doc)
                if not success or not boundaries:
                    error_msg = "Could not extract boundaries for orientation analysis"
                    self.logger.error(error_msg)
                    
                    # Return default orientation values as fallback
                    default_orientation = {
                        'origin_aligned': False,
                        'axis_aligned': True,
                        'angle_to_x_axis': 0,
                        'origin_offset_x': 0,
                        'origin_offset_y': 0
                    }
                    return False, default_orientation, error_msg
            
            self.logger.info("Identifying workpiece orientation")
            
            # Get dimensions for orientation analysis
            success, dimensions, _ = self.calculate_dimensions(boundaries)
            if not success or not dimensions:
                error_msg = "Could not calculate dimensions for orientation analysis"
                self.logger.error(error_msg)
                
                # Return default orientation values as fallback
                default_orientation = {
                    'origin_aligned': False,
                    'axis_aligned': True,
                    'angle_to_x_axis': 0,
                    'origin_offset_x': 0,
                    'origin_offset_y': 0
                }
                return False, default_orientation, error_msg
            
            # Analyze the workpiece position
            min_x = dimensions['min_x']
            min_y = dimensions['min_y']
            max_x = dimensions['max_x']
            max_y = dimensions['max_y']
            
            # Determine if the workpiece is aligned with the coordinate system
            # Check if workpiece starts at or near origin (using tolerance)
            starts_at_origin = abs(min_x) < self.POSITION_TOLERANCE and abs(min_y) < self.POSITION_TOLERANCE
            
            # Default angle is 0 (aligned with axes)
            angle_to_x_axis = 0
            
            # Simple check for aligned with axes based on primary boundary
            if boundaries:
                primary_boundary = boundaries[0]
                # Check for rectangular/aligned shape
                is_rectangular = self._is_rectangular(primary_boundary)
            else:
                is_rectangular = True  # Assume aligned if can't verify
            
            # Create orientation info
            orientation = {
                'origin_aligned': starts_at_origin,
                'axis_aligned': is_rectangular,
                'angle_to_x_axis': angle_to_x_axis,
                'origin_offset_x': min_x,
                'origin_offset_y': min_y
            }
            
            success_msg = f"Workpiece orientation identified: origin_aligned={starts_at_origin}, axis_aligned={is_rectangular}"
            self.logger.info(success_msg)
            return True, orientation, success_msg
            
        except Exception as e:
            error_msg = f"Error identifying orientation: {str(e)}"
            log_exception(self.logger, error_msg)
            
            # Return default orientation values on error
            default_orientation = {
                'origin_aligned': False,
                'axis_aligned': True,
                'angle_to_x_axis': 0,
                'origin_offset_x': 0,
                'origin_offset_y': 0
            }
            return False, default_orientation, error_msg
    
    def _is_rectangular(self, boundary):
        """
        Check if a boundary approximates a rectangle.
        
        Args:
            boundary: Boundary entity (polyline)
            
        Returns:
            bool: True if boundary is approximately rectangular
        """
        try:
            # Extract vertices
            vertices = self._extract_vertices(boundary)
            if not vertices:
                return False
            
            # Extract coordinate pairs with safe handling
            coords = []
            for vertex in vertices:
                try:
                    coords.append(self._extract_vertex_coords(vertex))
                except Exception:
                    continue
            
            # Need at least 4 vertices for a rectangle
            if len(coords) < 4:
                return False
            
            # For exact rectangles, 4 vertices are enough
            if len(coords) == 4:
                # Check for right angles (use dot product)
                for i in range(4):
                    p1 = coords[i]
                    p2 = coords[(i+1) % 4]
                    p3 = coords[(i+2) % 4]
                    
                    # Calculate vectors
                    v1 = (p2[0] - p1[0], p2[1] - p1[1])
                    v2 = (p3[0] - p2[0], p3[1] - p2[1])
                    
                    # Calculate dot product
                    dot_product = v1[0] * v2[0] + v1[1] * v2[1]
                    
                    # Check if perpendicular (approximately)
                    if abs(dot_product) > self.ANGLE_TOLERANCE:
                        return False
                
                return True
            
            # For boundaries with more vertices, check bounding box ratio
            min_x, min_y, max_x, max_y = float('inf'), float('inf'), float('-inf'), float('-inf')
            for x, y in coords:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
            
            # Calculate area of bounding box
            box_area = (max_x - min_x) * (max_y - min_y)
            
            # Calculate approximate area of shape
            shape_area = self._calculate_polygon_area(coords)
            
            # If the areas are close, it's approximately rectangular
            # Avoid division by zero
            if box_area < 0.0001:  # Very small area
                return False
                
            # Allow for defined area tolerance
            return abs(box_area - shape_area) / box_area < self.AREA_TOLERANCE
            
        except Exception as e:
            self.logger.warning(f"Error checking if boundary is rectangular: {str(e)}")
            return False  # Default to false on error
    
    def _calculate_polygon_area(self, vertices):
        """
        Calculate the area of a polygon using the Shoelace formula.
        
        Args:
            vertices: List of (x, y) tuples representing polygon vertices
            
        Returns:
            float: Area of the polygon
        """
        try:
            n = len(vertices)
            area = 0.0
            
            for i in range(n):
                j = (i + 1) % n
                area += vertices[i][0] * vertices[j][1]
                area -= vertices[j][0] * vertices[i][1]
            
            return abs(area) / 2.0
        except Exception as e:
            self.logger.warning(f"Error calculating polygon area: {str(e)}")
            return 0.0  # Default to zero on error
    
    def get_reference_points(self, dxf_doc, boundaries=None):
        """
        Extract reference points for machining from the DXF document.
        
        Identifies key points such as origin, corners, and center that
        might be useful for tool path generation and machine positioning.
        
        Args:
            dxf_doc: ezdxf document object
            boundaries: Optional list of boundary entities
            
        Returns:
            tuple: (success, reference_points, message) where:
                - success is a boolean indicating if points were extracted
                - reference_points is a dict with point coordinates
                - message contains success details or error information
        """
        if dxf_doc is None:
            error_msg = "No DXF document provided"
            self.logger.error(error_msg)
            return False, None, error_msg
        
        try:
            # Get boundaries if not provided
            if boundaries is None:
                success, boundaries, _ = self.extract_workpiece_boundaries(dxf_doc)
                if not success or not boundaries:
                    error_msg = "Could not extract boundaries for reference points"
                    self.logger.error(error_msg)
                    
                    # Return default reference points as fallback
                    default_points = {
                        'origin': (0, 0),
                        'corner_bl': (0, 0),
                        'corner_br': (100, 0),
                        'corner_tr': (100, 100),
                        'corner_tl': (0, 100),
                        'center': (50, 50),
                        'machine_zero': (0, 0),
                        'offset_from_machine_zero': (0, 0)
                    }
                    return False, default_points, error_msg
            
            self.logger.info("Extracting reference points")
            
            # Get dimensions for reference points
            success, dimensions, _ = self.calculate_dimensions(boundaries)
            if not success or not dimensions:
                error_msg = "Could not calculate dimensions for reference points"
                self.logger.error(error_msg)
                
                # Return default reference points as fallback
                default_points = {
                    'origin': (0, 0),
                    'corner_bl': (0, 0),
                    'corner_br': (100, 0),
                    'corner_tr': (100, 100),
                    'corner_tl': (0, 100),
                    'center': (50, 50),
                    'machine_zero': (0, 0),
                    'offset_from_machine_zero': (0, 0)
                }
                return False, default_points, error_msg
            
            # Extract key points from dimensions
            min_x = dimensions['min_x']
            min_y = dimensions['min_y']
            max_x = dimensions['max_x']
            max_y = dimensions['max_y']
            
            # Create reference points for machining
            reference_points = {
                'origin': (min_x, min_y),
                'corner_bl': (min_x, min_y),
                'corner_br': (max_x, min_y),
                'corner_tr': (max_x, max_y),
                'corner_tl': (min_x, max_y),
                'center': ((min_x + max_x) / 2, (min_y + max_y) / 2),
                'machine_zero': (0, 0)  # Default machine zero
            }
            
            # Add offset information - use larger tolerance
            reference_points['offset_from_machine_zero'] = (
                min_x if abs(min_x) > self.POSITION_TOLERANCE else 0,
                min_y if abs(min_y) > self.POSITION_TOLERANCE else 0
            )
            
            success_msg = "Reference points extracted successfully"
            self.logger.info(success_msg)
            return True, reference_points, success_msg
            
        except Exception as e:
            error_msg = f"Error extracting reference points: {str(e)}"
            log_exception(self.logger, error_msg)
            
            # Return default reference points on error
            default_points = {
                'origin': (0, 0),
                'corner_bl': (0, 0),
                'corner_br': (100, 0),
                'corner_tr': (100, 100),
                'corner_tl': (0, 100),
                'center': (50, 50),
                'machine_zero': (0, 0),
                'offset_from_machine_zero': (0, 0)
            }
            return False, default_points, error_msg
    
    def extract_workpiece_info(self, dxf_doc):
        """
        Extract complete workpiece information from the DXF document.
        
        Combines all extraction functions to provide a complete set of
        workpiece properties in a single call.
        
        Args:
            dxf_doc: ezdxf document object
            
        Returns:
            tuple: (success, workpiece_info, message) where:
                - success is a boolean indicating if extraction succeeded
                - workpiece_info is a dict with all workpiece properties
                - message contains success details or error information
        """
        if dxf_doc is None:
            error_msg = "No DXF document provided"
            self.logger.error(error_msg)
            return False, None, error_msg
        
        self.logger.info("Extracting complete workpiece information")
        
        try:
            # Create empty result structure for fallbacks
            empty_workpiece_info = {
                'dimensions': {
                    'width': 100.0,
                    'height': 100.0,
                    'depth': self.DEFAULT_THICKNESS,
                    'min_x': 0,
                    'min_y': 0,
                    'max_x': 100,
                    'max_y': 100
                },
                'orientation': {
                    'origin_aligned': False,
                    'axis_aligned': True,
                    'angle_to_x_axis': 0,
                    'origin_offset_x': 0,
                    'origin_offset_y': 0
                },
                'reference_points': {
                    'origin': (0, 0),
                    'corner_bl': (0, 0),
                    'corner_br': (100, 0),
                    'corner_tr': (100, 100),
                    'corner_tl': (0, 100),
                    'center': (50, 50),
                    'machine_zero': (0, 0),
                    'offset_from_machine_zero': (0, 0)
                },
                'boundary_count': 0,
                'material_thickness': self.DEFAULT_THICKNESS
            }
            
            # Extract boundaries
            boundaries_success, boundaries, boundaries_msg = self.extract_workpiece_boundaries(dxf_doc)
            if not boundaries_success:
                self.logger.error(f"Failed to extract boundaries: {boundaries_msg}")
                return False, empty_workpiece_info, f"Failed to extract workpiece info: {boundaries_msg}"
            
            # Calculate dimensions
            dimensions_success, dimensions, dimensions_msg = self.calculate_dimensions(boundaries)
            if not dimensions_success:
                self.logger.error(f"Failed to calculate dimensions: {dimensions_msg}")
                return False, empty_workpiece_info, f"Failed to extract workpiece info: {dimensions_msg}"
            
            # Identify orientation
            orientation_success, orientation, orientation_msg = self.identify_orientation(dxf_doc, boundaries)
            if not orientation_success:
                self.logger.warning(f"Failed to identify orientation: {orientation_msg}")
                # Continue with default orientation from identify_orientation
            
            # Get reference points
            points_success, reference_points, points_msg = self.get_reference_points(dxf_doc, boundaries)
            if not points_success:
                self.logger.warning(f"Failed to extract reference points: {points_msg}")
                # Continue with default reference points from get_reference_points
            
            # Combine all information into a single workpiece info dictionary
            workpiece_info = {
                'dimensions': dimensions,
                'orientation': orientation,
                'reference_points': reference_points,
                'boundary_count': len(boundaries),
                'material_thickness': dimensions['depth']  # For convenience
            }
            
            success_msg = "Workpiece information extracted successfully"
            self.logger.info(success_msg)
            return True, workpiece_info, success_msg
            
        except Exception as e:
            error_msg = f"Error extracting workpiece info: {str(e)}"
            log_exception(self.logger, error_msg)
            
            # Return empty structure on error
            return False, empty_workpiece_info, error_msg


# Example usage if run directly
if __name__ == "__main__":
    import sys
    from DXF.file_loader import DxfLoader
    
    extractor = WorkpieceExtractor()
    loader = DxfLoader()
    
    success, doc, message = loader.load_dxf()
    
    if success:
        print(message)
        success, workpiece_info, message = extractor.extract_workpiece_info(doc)
        
        print(f"\nWorkpiece info extraction: {'Succeeded' if success else 'Failed'}")
        print(f"Message: {message}")
        
        if success:
            print("\nWorkpiece Information:")
            print(f"Dimensions: {workpiece_info['dimensions']['width']:.2f} x {workpiece_info['dimensions']['height']:.2f} x {workpiece_info['dimensions']['depth']:.2f}mm")
            print(f"Aligned with origin: {workpiece_info['orientation']['origin_aligned']}")
            print(f"Aligned with axes: {workpiece_info['orientation']['axis_aligned']}")
            print("\nReference Points:")
            for point_name, coordinates in workpiece_info['reference_points'].items():
                print(f"  - {point_name}: ({coordinates[0]:.2f}, {coordinates[1]:.2f})")
        else:
            print(f"Error: {message}")
    else:
        print(f"Error: {message}")