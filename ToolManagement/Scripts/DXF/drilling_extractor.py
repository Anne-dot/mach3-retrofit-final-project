"""
Module for extracting drilling information from DXF files.

This module identifies and extracts drilling points and their parameters from DXF
files. It provides separate extractors for vertical and horizontal drilling operations,
extracting all necessary data for G-code generation.

References:
    - MRFP-80: DXF to G-code Generation Epic
    - MRFP-130: Develop Drilling Point Detection
"""

import re
import math
from typing import List, Dict, Tuple, Optional, Any, Union

# Import from Utils package
from Utils.logging_utils import setup_logger, log_exception


class DrillPointBase:
    """Base class for drilling point data."""
    
    def __init__(self, entity, layer_name):
        """
        Initialize base drilling point data.
        
        Args:
            entity: DXF entity representing the drilling point
            layer_name: Layer name containing drilling information
        """
        self.entity = entity
        self.layer_name = layer_name
        self.entity_type = entity.dxftype() if entity else "Unknown"
        self.position = (0, 0, 0)  # Default position (will be updated)
        self.diameter = 0.0        # Drill bit diameter
        self.depth = 0.0           # Drilling depth
        self.extract_common_data()
    
    def extract_common_data(self):
        """Extract common data from entity."""
        # Will be implemented in derived classes
        pass
    
    def __str__(self):
        """String representation of drilling point."""
        return f"{self.__class__.__name__} at {self.position}, D={self.diameter:.1f}mm, Depth={self.depth:.1f}mm"


class VerticalDrillPoint(DrillPointBase):
    """Class representing a vertical drilling point."""
    
    def __init__(self, entity, layer_name):
        """Initialize vertical drill point."""
        super().__init__(entity, layer_name)
        self.direction = (0, 0, -1)  # Vertical drilling (Z-)
        
    def extract_common_data(self):
        """Extract data from entity and layer name."""
        if self.entity_type == "CIRCLE":
            # Extract position - more robust handling of center coordinates
            try:
                # Handle case where center is a Point3D/Vec3 object
                if hasattr(self.entity.dxf, "center"):
                    center = self.entity.dxf.center
                    if hasattr(center, "x") and hasattr(center, "y"):
                        # Convert to simple tuple to avoid Vec3 issues
                        self.position = (
                            float(center.x),
                            float(center.y),
                            float(center.z) if hasattr(center, "z") else 0.0
                        )
                    elif isinstance(center, (tuple, list)) and len(center) >= 2:
                        # Handle tuple/list format
                        self.position = (
                            float(center[0]), 
                            float(center[1]), 
                            float(center[2]) if len(center) > 2 else 0.0
                        )
            except Exception as e:
                # Fallback to origin if position extraction fails
                self.position = (0.0, 0.0, 0.0)
            
            # Extract diameter from circle radius
            try:
                self.diameter = float(self.entity.dxf.radius) * 2.0
            except Exception:
                # Default diameter if extraction fails
                self.diameter = 0.0
            
            # Try to extract depth from attribute 39 (extrusion)
            try:
                if hasattr(self.entity, "get_dxf_attrib"):
                    extrusion = self.entity.get_dxf_attrib(39, default=None)
                    if extrusion is not None:
                        self.depth = abs(float(extrusion))
            except Exception:
                pass
            
            # Extract from layer name if not found in attributes
            if self.depth == 0.0:
                self.extract_parameters_from_layer_name()
    
    def extract_parameters_from_layer_name(self):
        """Extract drilling parameters from layer name."""
        # Layer format example: V.DRILL_D15.0_P14.0_F1
        # Extract diameter (D value)
        diameter_match = re.search(r'D(\d+\.?\d*)', self.layer_name)
        if diameter_match and self.diameter == 0.0:
            try:
                self.diameter = float(diameter_match.group(1))
            except ValueError:
                pass
        
        # Extract depth (P value)
        depth_match = re.search(r'P(\d+\.?\d*)', self.layer_name)
        if depth_match:
            try:
                self.depth = float(depth_match.group(1))
            except ValueError:
                pass


class HorizontalDrillPoint(DrillPointBase):
    """Class representing a horizontal drilling point."""
    
    def __init__(self, entity, layer_name):
        """Initialize horizontal drill point."""
        # Set edge to None initially to make it clear it hasn't been set yet
        self.edge = None
        self.direction = None
        self.direction_vector = None
        # Now call super() which will eventually call extract_common_data()
        super().__init__(entity, layer_name)
        # Add debug print to check final values
        print(f"DEBUG: Final init values - edge={self.edge}, direction={self.direction}")
        
    def extract_common_data(self):
        """Extract data from entity and layer name."""
        if self.entity_type == "CIRCLE":
            # Extract position - more robust handling of center coordinates
            try:
                # Handle case where center is a Point3D/Vec3 object
                if hasattr(self.entity.dxf, "center"):
                    center = self.entity.dxf.center
                    if hasattr(center, "x") and hasattr(center, "y"):
                        # Convert to simple tuple to avoid Vec3 issues
                        self.position = (
                            float(center.x),
                            float(center.y),
                            float(center.z) if hasattr(center, "z") else 0.0
                        )
                    elif isinstance(center, (tuple, list)) and len(center) >= 2:
                        # Handle tuple/list format
                        self.position = (
                            float(center[0]), 
                            float(center[1]), 
                            float(center[2]) if len(center) > 2 else 0.0
                        )
            except Exception as e:
                # Fallback to origin if position extraction fails
                self.position = (0.0, 0.0, 0.0)
            
            # Extract diameter from circle radius
            try:
                self.diameter = float(self.entity.dxf.radius) * 2.0
            except Exception:
                # Default diameter if extraction fails
                self.diameter = 0.0
            
            # Extract drilling parameters from layer name (NOT edge information)
            self.extract_parameters_from_layer_name()
            
            # FINAL STEP: Determine edge based on Z position
            # This is the authoritative source for edge information
            self._determine_edge_from_z()
    
    def extract_parameters_from_layer_name(self):
        """Extract drilling parameters from layer name (NOT edge info)."""
        # Layer format example: EDGE.DRILL_D8.0_P21.5
        # Extract diameter (D value)
        diameter_match = re.search(r'D(\d+\.?\d*)', self.layer_name)
        if diameter_match and self.diameter == 0.0:  # Only update if not already set
            try:
                self.diameter = float(diameter_match.group(1))
            except ValueError:
                pass
        
        # Extract depth (P value)
        depth_match = re.search(r'P(\d+\.?\d*)', self.layer_name)
        if depth_match:
            try:
                self.depth = float(depth_match.group(1))
            except ValueError:
                pass
    
    def _determine_edge_from_z(self):
        """
        Determine drilling edge based on Z position.
    
        Convention:
        - Z=0 indicates FRONT edge (drilling direction Y+)
        - Z~=-555 indicates BACK edge (drilling direction Y-)
        """
        _, _, z = self.position
        
        # Round Z to handle floating point imprecision
        z_rounded = round(z, 3)
        
        if z_rounded < -500:  # Large negative Z (approximately -555)
            self.edge = "BACK"
            self.direction = (0, -1, 0)  # Y- direction
            self.direction_vector = (0, -1, 0)
        else:  # Z near 0
            self.edge = "FRONT"
            self.direction = (0, 1, 0)   # Y+ direction
            self.direction_vector = (0, 1, 0)


class DrillingExtractor:
    """Main class for extracting drilling information from DXF files."""
    
    def __init__(self):
        """Initialize the drilling extractor."""
        # Set up logger for this class
        self.logger = setup_logger(__name__)
        
        # Layer keywords for identifying drilling points
        self.vert_drill_keyword = "V.DRILL"
        self.horz_drill_keyword = "EDGE.DRILL"
        
        # Alternative keywords that might be in your DXF files
        self.alt_vert_drill_keywords = ["VERT.DRILL", "VDRILL", "DRILL_V", "V_DRILL"]
        self.alt_horz_drill_keywords = ["EDGE_DRILL", "HDRILL", "DRILL_H", "H_DRILL", "HOR.DRILL"]
        
        # Pattern for extracting info from layer name
        self.diameter_pattern = r'D(\d+\.?\d*)'
        self.depth_pattern = r'P(\d+\.?\d*)'
        
        self.logger.info("DrillingExtractor initialized")
    
    def find_drilling_points(self, dxf_doc):
        """
        Find all drilling points in the DXF document.
        
        Args:
            dxf_doc: ezdxf document object
            
        Returns:
            tuple: (success, all_points, message) where:
                - success is a boolean indicating if points were found
                - all_points is a dict with 'vertical' and 'horizontal' keys
                - message contains success details or error information
        """
        if dxf_doc is None:
            error_msg = "No DXF document provided"
            self.logger.error(error_msg)
            return False, None, error_msg
        
        self.logger.info("Finding drilling points")
        
        try:
            # Get all entities in modelspace
            modelspace = dxf_doc.modelspace()
            
            # Lists to store found drilling points
            vertical_points = []
            horizontal_points = []
            
            # Look for drilling points
            for entity in modelspace:
                try:
                    # Check if entity is a circle (common for drilling points)
                    if entity.dxftype() == "CIRCLE":
                        # Get the layer name
                        layer_name = entity.dxf.layer
                        
                        # Check if it's a vertical drilling point
                        if (self.vert_drill_keyword in layer_name or 
                            any(keyword in layer_name for keyword in self.alt_vert_drill_keywords)):
                            try:
                                point = VerticalDrillPoint(entity, layer_name)
                                vertical_points.append(point)
                                self.logger.info(f"Found vertical drilling point at {point.position} on layer: {layer_name}")
                            except Exception as e:
                                self.logger.warning(f"Failed to process vertical drill point on layer {layer_name}: {str(e)}")
                        
                        # Check if it's a horizontal drilling point
                        elif (self.horz_drill_keyword in layer_name or 
                              any(keyword in layer_name for keyword in self.alt_horz_drill_keywords)):
                            try:
                                point = HorizontalDrillPoint(entity, layer_name)
                                horizontal_points.append(point)
                                self.logger.info(f"Found horizontal drilling point at {point.position} on layer: {layer_name}")
                            except Exception as e:
                                self.logger.warning(f"Failed to process horizontal drill point on layer {layer_name}: {str(e)}")
                            
                        # Generic circles - check naming patterns if not explicitly marked
                        elif "DRILL" in layer_name.upper():
                            # Try to determine type from other clues
                            if "HORIZONTAL" in layer_name.upper() or "EDGE" in layer_name.upper():
                                try:
                                    point = HorizontalDrillPoint(entity, layer_name)
                                    horizontal_points.append(point)
                                    self.logger.info(f"Found horizontal drilling point (from generic) at {point.position} on layer: {layer_name}")
                                except Exception as e:
                                    self.logger.warning(f"Failed to process generic horizontal drill point on layer {layer_name}: {str(e)}")
                            else:
                                # Default to vertical drilling if not specified
                                try:
                                    point = VerticalDrillPoint(entity, layer_name)
                                    vertical_points.append(point)
                                    self.logger.info(f"Found vertical drilling point (from generic) at {point.position} on layer: {layer_name}")
                                except Exception as e:
                                    self.logger.warning(f"Failed to process generic vertical drill point on layer {layer_name}: {str(e)}")
                except Exception as e:
                    self.logger.warning(f"Failed to process entity: {str(e)}")
                    continue
            
            # Check if any drilling points were found
            all_points = {
                'vertical': vertical_points,
                'horizontal': horizontal_points
            }
            
            total_points = len(vertical_points) + len(horizontal_points)
            
            if total_points == 0:
                warning_msg = "No drilling points found in DXF file"
                self.logger.warning(warning_msg)
                
                # For debugging - log all layer names from circles
                circle_layers = set()
                for entity in modelspace:
                    if entity.dxftype() == "CIRCLE":
                        circle_layers.add(entity.dxf.layer)
                
                if circle_layers:
                    self.logger.info(f"Circles found on these layers: {', '.join(circle_layers)}")
                
                return False, all_points, warning_msg
            
            success_msg = f"Found {len(vertical_points)} vertical and {len(horizontal_points)} horizontal drilling points"
            self.logger.info(success_msg)
            return True, all_points, success_msg
            
        except Exception as e:
            error_msg = f"Error finding drilling points: {str(e)}"
            log_exception(self.logger, error_msg)
            return False, {'vertical': [], 'horizontal': []}, error_msg
    
    def determine_drilling_direction(self, dxf_doc, drilling_points=None):
        """
        Determine drilling directions for all points.
        
        Args:
            dxf_doc: ezdxf document object
            drilling_points: Optional dict with pre-extracted drilling points
            
        Returns:
            tuple: (success, directions, message) where:
                - success is a boolean indicating if directions were determined
                - directions is a dict with point-to-direction mappings
                - message contains success details or error information
        """
        if dxf_doc is None:
            error_msg = "No DXF document provided"
            self.logger.error(error_msg)
            return False, None, error_msg
        
        # Get drilling points if not provided
        if drilling_points is None:
            success, drilling_points, _ = self.find_drilling_points(dxf_doc)
            if not success or not drilling_points:
                error_msg = "Could not extract drilling points for direction analysis"
                self.logger.error(error_msg)
                return False, None, error_msg
        
        self.logger.info("Determining drilling directions")
        
        try:
            # Create directions dictionary
            directions = {
                'vertical': [],
                'horizontal': []
            }
            
            # Process vertical drilling points (all have fixed Z- direction)
            for point in drilling_points['vertical']:
                directions['vertical'].append({
                    'point': point,
                    'direction': (0, 0, -1),  # Z- direction
                    'position': point.position
                })
            
            # Process horizontal drilling points (directions vary)
            # for point in drilling_points['horizontal']:
            #     directions['horizontal'].append({
            #         'point': point,
            #         'direction': point.direction,  # From entity data
            #         'position': point.position,
            #         'edge': point.edge
            #     })
            
            success_msg = "Drilling directions determined successfully"
            self.logger.info(success_msg)
            return True, directions, success_msg
            
        except Exception as e:
            error_msg = f"Error determining drilling directions: {str(e)}"
            log_exception(self.logger, error_msg)
            return False, None, error_msg
    
    def extract_drilling_parameters(self, dxf_doc, drilling_points=None):
        """
        Extract all drilling parameters (diameter, depth, etc.)
        
        Args:
            dxf_doc: ezdxf document object
            drilling_points: Optional dict with pre-extracted drilling points
            
        Returns:
            tuple: (success, parameters, message) where:
                - success is a boolean indicating if parameters were extracted
                - parameters is a dict with drilling parameters
                - message contains success details or error information
        """
        if dxf_doc is None:
            error_msg = "No DXF document provided"
            self.logger.error(error_msg)
            return False, None, error_msg
        
        # Get drilling points if not provided
        if drilling_points is None:
            success, drilling_points, _ = self.find_drilling_points(dxf_doc)
            if not success or not drilling_points:
                error_msg = "Could not extract drilling points for parameter analysis"
                self.logger.error(error_msg)
                return False, None, error_msg
        
        self.logger.info("Extracting drilling parameters")
        
        try:
            # Create parameters dictionary
            parameters = {
                'vertical': [],
                'horizontal': []
            }
            
            # Process vertical drilling points
            for point in drilling_points['vertical']:
                parameters['vertical'].append({
                    'position': point.position,
                    'diameter': point.diameter,
                    'depth': point.depth,
                    'layer': point.layer_name
                })
            
            # Process horizontal drilling points
            for point in drilling_points['horizontal']:
                parameters['horizontal'].append({
                    'position': point.position,
                    'diameter': point.diameter,
                    'depth': point.depth,
                    'direction': point.direction,
                    'edge': point.edge,
                    'layer': point.layer_name
                })
            
            success_msg = "Drilling parameters extracted successfully"
            self.logger.info(success_msg)
            return True, parameters, success_msg
            
        except Exception as e:
            error_msg = f"Error extracting drilling parameters: {str(e)}"
            log_exception(self.logger, error_msg)
            return False, None, error_msg
    
    def group_drilling_operations(self, dxf_doc, parameters=None):
        """
        Group related drilling operations by type, diameter, etc.
        
        Args:
            dxf_doc: ezdxf document object
            parameters: Optional dict with pre-extracted parameters
            
        Returns:
            tuple: (success, groups, message) where:
                - success is a boolean indicating if grouping was successful
                - groups is a dict with grouped drilling operations
                - message contains success details or error information
        """
        if dxf_doc is None:
            error_msg = "No DXF document provided"
            self.logger.error(error_msg)
            return False, None, error_msg
        
        # Get parameters if not provided
        if parameters is None:
            success, drilling_points, _ = self.find_drilling_points(dxf_doc)
            if not success or not drilling_points:
                error_msg = "Could not extract drilling points for grouping"
                self.logger.error(error_msg)
                return False, None, error_msg
                
            success, parameters, _ = self.extract_drilling_parameters(dxf_doc, drilling_points)
            if not success or not parameters:
                error_msg = "Could not extract drilling parameters for grouping"
                self.logger.error(error_msg)
                return False, None, error_msg
        
        self.logger.info("Grouping drilling operations")
        
        try:
            # Create groups dictionary
            groups = {
                'vertical': {},  # Grouped by diameter and depth
                'horizontal': {}  # Grouped by diameter, depth, and edge
            }
            
            # Group vertical drilling operations
            for params in parameters['vertical']:
                # Create group key: "Dxx.x_Pxx.x"
                diameter = params['diameter']
                depth = params['depth']
                group_key = f"D{diameter:.1f}_P{depth:.1f}"
                
                if group_key not in groups['vertical']:
                    groups['vertical'][group_key] = []
                
                groups['vertical'][group_key].append(params)
            
            # Group horizontal drilling operations
            for params in parameters['horizontal']:
                # Create group key: "Dxx.x_Pxx.x_EDGE"
                diameter = params['diameter']
                depth = params['depth']
                edge = params['edge']
                group_key = f"D{diameter:.1f}_P{depth:.1f}_{edge}"
                
                if group_key not in groups['horizontal']:
                    groups['horizontal'][group_key] = []
                
                groups['horizontal'][group_key].append(params)
            
            # Sort each group by position
            for group_key, operations in groups['vertical'].items():
                try:
                    groups['vertical'][group_key] = sorted(operations, key=lambda x: (x['position'][0], x['position'][1]))
                except Exception:
                    # If sorting fails, keep unsorted
                    pass
            
            for group_key, operations in groups['horizontal'].items():
                try:
                    groups['horizontal'][group_key] = sorted(operations, key=lambda x: (x['position'][0], x['position'][1], x['position'][2]))
                except Exception:
                    # If sorting fails, keep unsorted
                    pass
            
            success_msg = f"Grouped drilling operations into {len(groups['vertical'])} vertical and {len(groups['horizontal'])} horizontal groups"
            self.logger.info(success_msg)
            return True, groups, success_msg
            
        except Exception as e:
            error_msg = f"Error grouping drilling operations: {str(e)}"
            log_exception(self.logger, error_msg)
            return False, None, error_msg
    
    def extract_all_drilling_info(self, dxf_doc):
        """
        Extract complete drilling information from the DXF document.
        
        Combines all extraction functions to provide a complete set of
        drilling data in a single call.
        
        Args:
            dxf_doc: ezdxf document object
            
        Returns:
            tuple: (success, drilling_info, message) where:
                - success is a boolean indicating if extraction succeeded
                - drilling_info is a dict with all drilling information
                - message contains success details or error information
        """
        if dxf_doc is None:
            error_msg = "No DXF document provided"
            self.logger.error(error_msg)
            return False, None, error_msg
        
        self.logger.info("Extracting complete drilling information")
        
        try:
            # Extract drilling points - if this fails, create empty structure
            try:
                points_success, drilling_points, points_msg = self.find_drilling_points(dxf_doc)
                if not points_success:
                    self.logger.warning(f"Failed to extract drilling points: {points_msg}")
                    drilling_points = {'vertical': [], 'horizontal': []}
            except Exception as e:
                self.logger.warning(f"Exception in find_drilling_points: {str(e)}")
                drilling_points = {'vertical': [], 'horizontal': []}
            
            # Proceed only if there are drilling points
            if not drilling_points['vertical'] and not drilling_points['horizontal']:
                warning_msg = "No drilling points found in the DXF file"
                self.logger.warning(warning_msg)
                
                # Return empty structure with success=False
                empty_result = {
                    'points': {'vertical': [], 'horizontal': []},
                    'directions': {'vertical': [], 'horizontal': []},
                    'parameters': {'vertical': [], 'horizontal': []},
                    'groups': {'vertical': {}, 'horizontal': {}},
                    'vertical_count': 0,
                    'horizontal_count': 0,
                    'vertical_groups': 0,
                    'horizontal_groups': 0
                }
                return False, empty_result, warning_msg
            
            # Continue with direction determination
            try:
                directions_success, directions, directions_msg = self.determine_drilling_direction(dxf_doc, drilling_points)
                if not directions_success:
                    self.logger.warning(f"Failed to determine drilling directions: {directions_msg}")
                    directions = {'vertical': [], 'horizontal': []}
            except Exception as e:
                self.logger.warning(f"Exception in determine_drilling_direction: {str(e)}")
                directions = {'vertical': [], 'horizontal': []}
            
            # Extract parameters
            try:
                params_success, parameters, params_msg = self.extract_drilling_parameters(dxf_doc, drilling_points)
                if not params_success:
                    self.logger.warning(f"Failed to extract drilling parameters: {params_msg}")
                    parameters = {'vertical': [], 'horizontal': []}
            except Exception as e:
                self.logger.warning(f"Exception in extract_drilling_parameters: {str(e)}")
                parameters = {'vertical': [], 'horizontal': []}
            
            # Group drilling operations
            try:
                groups_success, groups, groups_msg = self.group_drilling_operations(dxf_doc, parameters)
                if not groups_success:
                    self.logger.warning(f"Failed to group drilling operations: {groups_msg}")
                    groups = {'vertical': {}, 'horizontal': {}}
            except Exception as e:
                self.logger.warning(f"Exception in group_drilling_operations: {str(e)}")
                groups = {'vertical': {}, 'horizontal': {}}
            
            # Combine all information into a single drilling info dictionary
            drilling_info = {
                'points': drilling_points,
                'directions': directions,
                'parameters': parameters,
                'groups': groups,
                'vertical_count': len(drilling_points['vertical']),
                'horizontal_count': len(drilling_points['horizontal']),
                'vertical_groups': len(groups['vertical']),
                'horizontal_groups': len(groups['horizontal'])
            }
            
            success_msg = "Drilling information extracted successfully"
            self.logger.info(success_msg)
            return True, drilling_info, success_msg
            
        except Exception as e:
            error_msg = f"Error extracting drilling info: {str(e)}"
            log_exception(self.logger, error_msg)
            
            # Return empty structure in case of error
            empty_result = {
                'points': {'vertical': [], 'horizontal': []},
                'directions': {'vertical': [], 'horizontal': []},
                'parameters': {'vertical': [], 'horizontal': []},
                'groups': {'vertical': {}, 'horizontal': {}},
                'vertical_count': 0,
                'horizontal_count': 0,
                'vertical_groups': 0,
                'horizontal_groups': 0
            }
            return False, empty_result, error_msg


# Example usage if run directly
if __name__ == "__main__":
    import sys
    from DXF.file_loader import DxfLoader
    
    extractor = DrillingExtractor()
    loader = DxfLoader()
    
    success, doc, message = loader.load_dxf()
    
    if success:
        print(message)
        success, drilling_info, message = extractor.extract_all_drilling_info(doc)
        
        print(f"\nAll drilling info extraction: {'Succeeded' if success else 'Failed'}")
        print(f"Message: {message}")
        
        if success:
            print("\nDrilling Information:")
            print(f"Vertical drilling points: {drilling_info['vertical_count']}")
            print(f"Horizontal drilling points: {drilling_info['horizontal_count']}")
            
            print("\nVertical Drilling Groups:")
            for group_key, operations in drilling_info['groups']['vertical'].items():
                print(f"  Group {group_key}: {len(operations)} operations")
                for op in operations:
                    print(f"    - Position: ({op['position'][0]:.3f}, {op['position'][1]:.3f})")
            
            print("\nHorizontal Drilling Groups:")
            for group_key, operations in drilling_info['groups']['horizontal'].items():
                print(f"  Group {group_key}: {len(operations)} operations")
                for op in operations:
                    print(f"    - Position: ({op['position'][0]:.3f}, {op['position'][1]:.3f}, {op['position'][2]:.3f})")
                    if 'direction' in op:
                        print(f"      Direction: ({op['direction'][0]:.1f}, {op['direction'][1]:.1f}, {op['direction'][2]:.1f})")
        else:
            print(f"Error: {message}")
    else:
        print(f"Error: {message}")