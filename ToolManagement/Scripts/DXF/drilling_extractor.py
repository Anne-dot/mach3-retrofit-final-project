"""
Module for extracting drilling information from DXF files.

This module handles raw data extraction from DXF files without any classification
or detection. It extracts all necessary data (coordinates, layer names, extrusion
vectors, etc.) that will later be used for drilling point classification and
coordinate transformation.

References:
    - MRFP-80: DXF to G-code Generation Epic
    - MRFP-130: Develop Drilling Point Detection
"""

import re
import math
from typing import List, Dict, Tuple, Optional, Any, Union

# Import from Utils package
from Utils.logging_utils import setup_logger, log_exception


class DrillPoint:
    """
    Class representing a drilling point with raw data extraction.
    
    This class extracts and stores raw data from DXF drilling entities
    without any classification or edge detection.
    """
    
    def __init__(self, entity, layer_name):
        """
        Initialize drilling point data.
        
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
        self.extrusion_vector = None  # Extrusion vector for drilling direction
        
        # Extract all data
        self.extract_data()
    
    def extract_data(self):
        """Extract all available data from entity without classification."""
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
            
            # Try to extract depth from attribute 39 (extrusion) or thickness
            try:
                if hasattr(self.entity.dxf, "thickness"):
                    thickness = self.entity.dxf.thickness
                    if thickness is not None:
                        self.depth = abs(float(thickness))
                
                if self.depth == 0.0 and hasattr(self.entity, "get_dxf_attrib"):
                    extrusion = self.entity.get_dxf_attrib(39, default=None)
                    if extrusion is not None:
                        self.depth = abs(float(extrusion))
            except Exception:
                pass
            
            # Extract drilling parameters from layer name if not found in attributes
            if self.depth == 0.0:
                self.extract_parameters_from_layer_name()
                
            # Extract extrusion vector (critical for drilling direction)
            self.extract_extrusion_vector()
    
    def extract_parameters_from_layer_name(self):
        """Extract drilling parameters from layer name."""
        # Layer format examples:
        # V.DRILL_D15.0_P14.0_F1
        # EDGE.DRILL_D8.0_P21.5
        
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
    
    def extract_extrusion_vector(self):
        """Extract extrusion vector for drilling direction detection."""
        try:
            # Try to get extrusion attribute
            if hasattr(self.entity.dxf, "extrusion"):
                extrusion = self.entity.dxf.extrusion
                
                # Handle different types of extrusion values
                if isinstance(extrusion, (tuple, list)) and len(extrusion) >= 3:
                    self.extrusion_vector = (
                        float(extrusion[0]),
                        float(extrusion[1]),
                        float(extrusion[2])
                    )
                elif hasattr(extrusion, "x") and hasattr(extrusion, "y") and hasattr(extrusion, "z"):
                    self.extrusion_vector = (
                        float(extrusion.x),
                        float(extrusion.y),
                        float(extrusion.z)
                    )
            
            # Try extrusion direction attributes 210/220/230
            elif all(hasattr(self.entity.dxf, attr) for attr in ["210", "220", "230"]):
                self.extrusion_vector = (
                    float(self.entity.dxf.get("210", 0)),
                    float(self.entity.dxf.get("220", 0)),
                    float(self.entity.dxf.get("230", 0))
                )
        except Exception:
            self.extrusion_vector = None
    
    def __str__(self):
        """String representation of drilling point."""
        return f"DrillPoint at {self.position}, D={self.diameter:.1f}mm, Depth={self.depth:.1f}mm"


class DrillingExtractor:
    """
    Class for extracting drilling information from DXF files.
    
    This class focuses solely on finding and extracting drilling data from
    DXF files without any classification or detection.
    """
    
    def __init__(self):
        """Initialize the drilling extractor."""
        # Set up logger for this class
        self.logger = setup_logger(__name__)
        
        # Layer keywords for finding drilling entities
        self.drill_keywords = [
            "DRILL",            # Generic drill
            "V.DRILL",          # Vertical drill
            "VERT.DRILL",       # Vertical drill alternate
            "EDGE.DRILL",       # Edge/horizontal drill
            "VDRILL",           # Short vertical drill
            "HDRILL",           # Short horizontal drill
            "DRILL_V",          # Vertical drill alternate
            "DRILL_H",          # Horizontal drill alternate
            "V_DRILL",          # Vertical drill alternate
            "H_DRILL",          # Horizontal drill alternate
            "HOR.DRILL"         # Horizontal drill alternate
        ]
        
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
            tuple: (success, drill_points, message) where:
                - success is a boolean indicating if points were found
                - drill_points is a list of DrillPoint objects
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
            
            # List to store found drilling points
            drill_points = []
            
            # Look for drilling points
            for entity in modelspace:
                try:
                    # Check if entity is a circle (common for drilling points)
                    if entity.dxftype() == "CIRCLE":
                        # Get the layer name
                        layer_name = entity.dxf.layer
                        
                        # Check if layer name contains any drill keyword
                        if any(keyword in layer_name for keyword in self.drill_keywords):
                            try:
                                # Create a DrillPoint object without classification
                                point = DrillPoint(entity, layer_name)
                                drill_points.append(point)
                                self.logger.info(f"Found drilling point at {point.position} on layer: {layer_name}")
                            except Exception as e:
                                self.logger.warning(f"Failed to process drill point on layer {layer_name}: {str(e)}")
                except Exception as e:
                    self.logger.warning(f"Failed to process entity: {str(e)}")
                    continue
            
            # Check if any drilling points were found
            if not drill_points:
                warning_msg = "No drilling points found in DXF file"
                self.logger.warning(warning_msg)
                
                # For debugging - log all layer names from circles
                circle_layers = set()
                for entity in modelspace:
                    if entity.dxftype() == "CIRCLE":
                        circle_layers.add(entity.dxf.layer)
                
                if circle_layers:
                    self.logger.info(f"Circles found on these layers: {', '.join(circle_layers)}")
                
                return False, [], warning_msg
            
            success_msg = f"Found {len(drill_points)} drilling points"
            self.logger.info(success_msg)
            return True, drill_points, success_msg
            
        except Exception as e:
            error_msg = f"Error finding drilling points: {str(e)}"
            log_exception(self.logger, error_msg)
            return False, [], error_msg
    
    def extract_drilling_parameters(self, drill_points):
        """
        Extract and compile all drilling parameters in a standardized format.
        
        Args:
            drill_points: List of DrillPoint objects
            
        Returns:
            tuple: (success, parameters, message) where:
                - success is a boolean indicating if parameters were extracted
                - parameters is a list of parameter dictionaries
                - message contains success details or error information
        """
        if not drill_points:
            warning_msg = "No drilling points provided for parameter extraction"
            self.logger.warning(warning_msg)
            return False, [], warning_msg
        
        self.logger.info("Extracting drilling parameters")
        
        try:
            parameters = []
            
            # Process drilling points
            for point in drill_points:
                param_dict = {
                    'position': point.position,
                    'diameter': point.diameter,
                    'depth': point.depth,
                    'layer': point.layer_name,
                    'extrusion_vector': point.extrusion_vector
                }
                    
                parameters.append(param_dict)
            
            success_msg = "Drilling parameters extracted successfully"
            self.logger.info(success_msg)
            return True, parameters, success_msg
            
        except Exception as e:
            error_msg = f"Error extracting drilling parameters: {str(e)}"
            log_exception(self.logger, error_msg)
            return False, [], error_msg
    
    def extract_all_drilling_info(self, dxf_doc):
        """
        Extract all drilling information from the DXF document.
        
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
            # Extract drilling points
            success, drill_points, message = self.find_drilling_points(dxf_doc)
            if not success:
                return False, {'points': [], 'parameters': [], 'count': 0}, message
            
            # Extract parameters
            params_success, parameters, params_msg = self.extract_drilling_parameters(drill_points)
            if not params_success:
                warning_msg = f"Failed to extract drilling parameters: {params_msg}"
                self.logger.warning(warning_msg)
                parameters = []
            
            # Combine all information into a single drilling info dictionary
            drilling_info = {
                'points': drill_points,
                'parameters': parameters,
                'count': len(drill_points)
            }
            
            success_msg = f"Drilling information extracted successfully: found {len(drill_points)} drilling points"
            self.logger.info(success_msg)
            return True, drilling_info, success_msg
            
        except Exception as e:
            error_msg = f"Error extracting drilling info: {str(e)}"
            log_exception(self.logger, error_msg)
            
            # Return empty structure in case of error
            return False, {'points': [], 'parameters': [], 'count': 0}, error_msg


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
        
        print(f"\nDrilling info extraction: {'Succeeded' if success else 'Failed'}")
        print(f"Message: {message}")
        
        if success:
            print(f"\nFound {drilling_info['count']} drilling points")
            
            print("\nDrilling Points:")
            for i, point in enumerate(drilling_info['points']):
                print(f"\nPoint {i+1}:")
                print(f"  Position: {point.position}")
                print(f"  Layer: {point.layer_name}")
                print(f"  Diameter: {point.diameter}mm")
                print(f"  Depth: {point.depth}mm")
                print(f"  Extrusion Vector: {point.extrusion_vector}")
        else:
            print(f"Error: {message}")
    else:
        print(f"Error: {message}")