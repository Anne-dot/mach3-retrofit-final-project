"""
Module for loading and validating DXF files.

This module handles the initial loading of DXF files, validation of file
format, and provides the basic file object that other modules will use
for data extraction. It isolates file I/O operations from data processing.

References:
    - MRFP-80: DXF to G-code Generation Epic
"""

import os
import sys
import platform
import tkinter as tk
from tkinter import filedialog

# Import from Utils package
from Utils.logging_utils import setup_logger, log_exception

try:
    import ezdxf
    from ezdxf.document import Drawing
except ImportError:
    print("Error: ezdxf library not found. Please install with: pip install ezdxf")
    sys.exit(1)


class DxfLoader:
    """Class for loading and validating DXF files."""
    
    def __init__(self):
        """Initialize the DXF loader."""
        # Set up logger for this class
        self.logger = setup_logger(__name__)
        
        self.dxf_doc = None
        self.file_path = None
        self.error_message = ""
        self.logger.info("DxfLoader initialized")
        
    def load_dxf(self, file_path=None):
        """
        Loads and validates a DXF file.
        
        Args:
            file_path: Optional path to DXF file. If not provided, will prompt for selection.
            
        Returns:
            tuple: (success, document, message) where:
                - success is a boolean indicating if loading was successful
                - document is the ezdxf document object or None if failed
                - message contains success message or error details
        """
        # If no path provided, prompt for file selection
        if file_path is None:
            self.logger.info("No file path provided, prompting for selection")
            file_path = self.select_dxf_file()
            
            # Check if user canceled file selection
            if not file_path:
                self.logger.warning("File selection canceled by user")
                return False, None, "File selection canceled by user"
        
        self.file_path = file_path
        self.logger.info(f"Attempting to load DXF file: {file_path}")
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                error_msg = f"File not found: {file_path}"
                self.logger.error(error_msg)
                return False, None, error_msg
                
            # Check if file is accessible
            if not os.access(file_path, os.R_OK):
                error_msg = f"File not accessible (permission denied): {file_path}"
                self.logger.error(error_msg)
                return False, None, error_msg
                
            # Check if file has .dxf extension
            if not file_path.lower().endswith('.dxf'):
                error_msg = f"File does not have .dxf extension: {file_path}"
                self.logger.error(error_msg)
                return False, None, error_msg
            
            # Load the DXF file
            self.dxf_doc = ezdxf.readfile(file_path)
            
            # Check if modelspace contains at least one entity
            modelspace = self.dxf_doc.modelspace()
            entity_count = len(list(modelspace))
            
            if entity_count == 0:
                error_msg = "DXF file contains no entities in modelspace"
                self.logger.error(error_msg)
                return False, None, error_msg
            
            success_msg = f"Successfully loaded DXF file: {os.path.basename(file_path)}"
            self.logger.info(success_msg)
            return True, self.dxf_doc, success_msg
            
        except ezdxf.DXFError as e:
            error_msg = f"Error loading DXF file: {str(e)}"
            self.error_message = error_msg
            log_exception(self.logger, error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error loading DXF file: {str(e)}"
            self.error_message = error_msg
            log_exception(self.logger, error_msg)
            return False, None, error_msg

    def is_valid_dxf(self, file_path):
        """
        Validates that a file is a readable, valid DXF.
        
        Required elements:
        - Valid DXF format parsable by ezdxf
        - Contains at least one entity
        
        Note: Specific entity requirements (workpiece boundaries, 
        drilling points) are validated in their respective modules.
        
        Args:
            file_path: Path to DXF file
            
        Returns:
            tuple: (is_valid, message) where is_valid is boolean and
                   message explains any validation failures
        """
        self.logger.info(f"Validating DXF file: {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            self.logger.error(error_msg)
            return False, error_msg
            
        # Check if file is accessible
        if not os.access(file_path, os.R_OK):
            error_msg = f"File not accessible (permission denied): {file_path}"
            self.logger.error(error_msg)
            return False, error_msg
            
        # Check if file has .dxf extension
        if not file_path.lower().endswith('.dxf'):
            error_msg = f"File does not have .dxf extension: {file_path}"
            self.logger.error(error_msg)
            return False, error_msg
            
        try:
            # Try to parse with ezdxf to check format
            doc = ezdxf.readfile(file_path)
            
            # Check if modelspace contains at least one entity
            modelspace = doc.modelspace()
            entity_count = len(list(modelspace))
            
            if entity_count == 0:
                error_msg = "DXF file contains no entities in modelspace"
                self.logger.error(error_msg)
                return False, error_msg
            
            valid_msg = f"DXF file is valid with {entity_count} entities"
            self.logger.info(valid_msg)
            return True, valid_msg
            
        except ezdxf.DXFError as e:
            error_msg = f"Invalid DXF file format: {str(e)}"
            log_exception(self.logger, error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error validating DXF file: {str(e)}"
            log_exception(self.logger, error_msg)
            return False, error_msg
    
    def get_dxf_info(self, dxf_doc=None):
        """
        Returns basic information about the DXF file.
        
        Args:
            dxf_doc: Optional ezdxf document object. If None, uses previously loaded document.
            
        Returns:
            dict: Dictionary containing information about the DXF file, or None if no document available
        """
        doc = dxf_doc if dxf_doc is not None else self.dxf_doc
        
        if doc is None:
            self.logger.warning("Attempted to get DXF info with no document loaded")
            return None
            
        self.logger.info("Extracting DXF file information")
        
        # Get modelspace for entity analysis
        modelspace = doc.modelspace()
        
        # Count entities by type
        entity_counts = {}
        for entity in modelspace:
            entity_type = entity.dxftype()
            if entity_type not in entity_counts:
                entity_counts[entity_type] = 0
            entity_counts[entity_type] += 1
        
        # Get layer information
        layers = {layer.dxf.name: {
            'color': layer.dxf.color,
            'linetype': layer.dxf.linetype,
            'is_on': layer.is_on
        } for layer in doc.layers}
        
        # Compile information
        info = {
            'filename': os.path.basename(self.file_path) if self.file_path else "Unknown",
            'dxf_version': doc.dxfversion,
            'encoding': doc.encoding,
            'entity_counts': entity_counts,
            'total_entities': sum(entity_counts.values()),
            'layers': layers,
            'header_variables': len(doc.header)
        }
        
        self.logger.info(f"Extracted information from DXF file with {info['total_entities']} total entities")
        return info
    
    def select_dxf_file(self):
        """
        Prompts the user to select a DXF file using an appropriate UI for the platform.
        
        Returns:
            str: Selected file path, or None if selection was canceled
        """
        # Windows: Use tkinter file dialog
        if platform.system() == "Windows":
            self.logger.info("Using Windows file dialog for DXF selection")
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            file_path = filedialog.askopenfilename(
                title="Select DXF File",
                filetypes=[("DXF files", "*.dxf"), ("All files", "*.*")]
            )
            
            if file_path:
                self.logger.info(f"Selected file: {file_path}")
            else:
                self.logger.info("File selection canceled")
                
            return file_path if file_path else None
            
        # Linux/Other: Show file list in terminal
        else:
            self.logger.info("Using terminal interface for DXF selection")
            # Get the path to the test data directory
            test_data_dir = os.path.abspath(os.path.join(
                os.path.dirname(__file__), 
                '..', '..', 'Tests', 'TestData', 'DXF'
            ))
            
            # Check if directory exists
            if not os.path.exists(test_data_dir):
                error_msg = f"Test data directory not found: {test_data_dir}"
                self.logger.error(error_msg)
                print(error_msg)
                return None
                
            # List DXF files
            dxf_files = [f for f in os.listdir(test_data_dir) if f.lower().endswith('.dxf')]
            
            if not dxf_files:
                error_msg = f"No DXF files found in {test_data_dir}"
                self.logger.error(error_msg)
                print(error_msg)
                return None
                
            # Display file list
            print("\nAvailable DXF files:")
            for i, file_name in enumerate(dxf_files):
                print(f"{i+1}. {file_name}")
                
            # Get user selection
            while True:
                try:
                    selection = input("\nEnter file number (or 'q' to quit): ")
                    
                    if selection.lower() == 'q':
                        self.logger.info("File selection canceled by user")
                        return None
                        
                    index = int(selection) - 1
                    if 0 <= index < len(dxf_files):
                        selected_file = os.path.join(test_data_dir, dxf_files[index])
                        self.logger.info(f"Selected file: {selected_file}")
                        return selected_file
                    else:
                        print(f"Invalid selection. Please enter 1-{len(dxf_files)}.")
                except ValueError:
                    print("Please enter a valid number.")


# Example usage if run directly
if __name__ == "__main__":
    loader = DxfLoader()
    success, doc, message = loader.load_dxf()
    
    if success:
        print(message)
        info = loader.get_dxf_info(doc)
        print("\nDXF Information:")
        print(f"File: {info['filename']}")
        print(f"Version: {info['dxf_version']}")
        print(f"Total entities: {info['total_entities']}")
        print("\nEntity counts:")
        for entity_type, count in info['entity_counts'].items():
            print(f"  - {entity_type}: {count}")
        print("\nLayers:")
        for layer_name in info['layers']:
            print(f"  - {layer_name}")
    else:
        print(f"Error: {message}")
