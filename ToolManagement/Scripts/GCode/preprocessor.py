#!/usr/bin/env python3
"""
Module for G-code preprocessing and enhancement.

This module implements the G-code preprocessor functionality that inserts
safety checks, tool validation, and other enhancements into G-code programs
before execution, as specified in the knowledge base.

Classes:
    MovementAnalyzer: Analyzes G-code movements and determines safety requirements
    GCodePreprocessor: Processes G-code files to add safety enhancements

Functions:
    main(): Command-line entry point for the preprocessor

References:
    - MRFP-68: Tool Movement Safety Check MVP
    - M150_SafetyCheck.m1s Implementation
    - DRO to G-Code Variables Mapping (knowledge base)
"""

import re
import os
import sys
import datetime
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List

# Import from Utils package - centralized utility functions
from Utils.logging_utils import setup_logger, log_exception
from Utils.error_utils import ErrorHandler, BaseError, ErrorCategory, ErrorSeverity
from Utils.file_utils import FileUtils
from Utils.path_utils import PathUtils

# Import the normalizer
from GCode.gcode_normalizer import GCodeNormalizer

# Set up logger
logger = setup_logger(__name__)


class MovementAnalyzer:
    """
    Analyzes G-code movement commands to determine mode and axes.
    
    This class provides methods to analyze G-code lines and identify
    movement commands that require safety validation. It detects G-code
    mode (G0/G1/G2/G3) and which axes are involved in each movement.
    
    Attributes:
        g1_pattern: Regular expression for G1 commands
        g2_pattern: Regular expression for G2 commands
        g3_pattern: Regular expression for G3 commands
        x_pattern: Regular expression for X axis movements
        y_pattern: Regular expression for Y axis movements
        z_pattern: Regular expression for Z axis movements
    """
    
    def __init__(self):
        """Initialize the MovementAnalyzer with regex patterns."""
        # G-code command patterns - updated to be more precise and avoid false positives
        self.g1_pattern = re.compile(r'(?:N\d+)?G0*1(?=[XYZIJKRF\s]|$)')  # Match G1 followed by axis or end
        self.g2_pattern = re.compile(r'(?:N\d+)?G0*2(?=[XYZIJKRF\s]|$)')  # Match G2 followed by axis or end
        self.g3_pattern = re.compile(r'(?:N\d+)?G0*3(?=[XYZIJKRF\s]|$)')  # Match G3 followed by axis or end
        
        # Axis movement patterns
        self.x_pattern = re.compile(r'[Xx][+-]?[0-9.]+')
        self.y_pattern = re.compile(r'[Yy][+-]?[0-9.]+')
        self.z_pattern = re.compile(r'[Zz][+-]?[0-9.]+')
    
    def analyze_line(self, line: str) -> Dict[str, Any]:
        """
        Analyze a G-code line to determine movement type and axes.
        
        Args:
            line: G-code line to analyze
            
        Returns:
            dict: Movement information with keys:
                - g_code: 0 if not G1/G2/G3, or 1/2/3 for G1/G2/G3
                - x_move: 1 if X axis moves, 0 otherwise
                - y_move: 1 if Y axis moves, 0 otherwise
                - z_move: 1 if Z axis moves, 0 otherwise
                - needs_check: True if safety check needed
        """
        # Default values
        result = {
            "g_code": 0,
            "x_move": 0,
            "y_move": 0,
            "z_move": 0,
            "needs_check": False
        }
        
        # Determine G-code
        g1_match = self.g1_pattern.search(line)
        g2_match = self.g2_pattern.search(line)
        g3_match = self.g3_pattern.search(line)
        
        if g1_match:
            result["g_code"] = 1
            result["needs_check"] = True
            logger.debug(f"Found G1 command in line: {line.strip()}")
        elif g2_match:
            result["g_code"] = 2
            result["needs_check"] = True
            logger.debug(f"Found G2 command in line: {line.strip()}")
        elif g3_match:
            result["g_code"] = 3
            result["needs_check"] = True
            logger.debug(f"Found G3 command in line: {line.strip()}")
        
        # Only check for axis movements if this is a movement command
        if result["needs_check"]:
            result["x_move"] = 1 if self.x_pattern.search(line) else 0
            result["y_move"] = 1 if self.y_pattern.search(line) else 0
            result["z_move"] = 1 if self.z_pattern.search(line) else 0
            logger.debug(f"Movement axes: X={result['x_move']}, Y={result['y_move']}, Z={result['z_move']}")
            
        return result


class GCodePreprocessor:
    """
    Preprocesses G-code files to add safety checks.
    
    This class analyzes G-code files and inserts necessary safety checks
    based on tool type and movement parameters. It specifically targets
    G1/G2/G3 movements and adds variable settings and M150 calls to
    validate safety constraints.
    
    Attributes:
        analyzer: MovementAnalyzer instance to detect G-code movements
        current_timestamp: Timestamp for generated files
    """
    
    def __init__(self):
        """Initialize the GCodePreprocessor."""
        self.analyzer = MovementAnalyzer()
        self.current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def preprocess_file(self, input_file: str, output_file: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Process a G-code file, adding safety checks for movements.
        
        Args:
            input_file: Path to input G-code file
            output_file: Path to output file. If None, 
                         generates output filename.
        
        Returns:
            Tuple: (success, message, details)
        """
        try:
            # Normalize and validate paths
            input_path = PathUtils.normalize_path(input_file)
            logger.info(f"Processing file: {input_path}")
            
            # Generate output filename if not provided
            if output_file is None:
                input_path_obj = Path(input_path)
                # Preserve the original file extension
                output_path = str(input_path_obj.with_stem(f"{input_path_obj.stem}_safe").with_suffix(input_path_obj.suffix))
            else:
                output_path = PathUtils.normalize_path(output_file)
            
            logger.info(f"Output will be written to: {output_path}")
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            PathUtils.ensure_dir(output_dir)
            
            # Read input file
            logger.info("Reading input file...")
            try:
                with open(input_path, 'r') as f:
                    content = f.read()
                logger.info(f"Successfully read file: {len(content)} characters")
            except Exception as e:
                logger.error(f"Failed to read input file: {str(e)}")
                return False, f"Failed to read input file: {str(e)}", {}
            
            # Process content
            logger.info("Analyzing G-code content...")
            result = self._process_content(content, os.path.basename(input_path))
            logger.info(f"Analysis complete. Found {result['safety_checks_added']} movements requiring safety checks.")
            
            # Write output file
            logger.info(f"Writing output file: {output_path}")
            try:
                with open(output_path, 'w') as f:
                    f.write(result["processed_content"])
                logger.info(f"Successfully wrote output file: {len(result['processed_content'])} characters")
            except Exception as e:
                logger.error(f"Failed to write output file: {str(e)}")
                return False, f"Failed to write output file: {str(e)}", {}
            
            logger.info(f"Successfully processed {result['line_count']} lines, added {result['safety_checks_added']} safety checks")
            return True, "G-code preprocessing completed successfully", {
                "input_file": input_path,
                "output_file": output_path,
                "lines_processed": result["line_count"],
                "safety_checks_added": result["safety_checks_added"]
            }
            
        except Exception as e:
            logger.error(f"Error preprocessing G-code: {str(e)}")
            return ErrorHandler.from_exception(e)
    
    def _process_content(self, content: str, filename: str) -> Dict[str, Any]:
        """
        Process G-code content, adding safety checks.
        
        Args:
            content: G-code content to process
            filename: Original filename for reference
            
        Returns:
            dict: Result with processed content and statistics
        """
        lines = content.splitlines()
        result_lines = []
        
        # Add header
        result_lines.append("(Safety-enhanced G-code generated by preprocessor)")
        result_lines.append(f"(Original file: {filename})")
        result_lines.append(f"(Generated on: {self.current_timestamp})")
        result_lines.append("")
        
        line_count = 0
        safety_checks_added = 0
        
        # Log some sample lines for debugging
        if len(lines) > 20:
            logger.info(f"First 5 lines of file:")
            for i in range(min(5, len(lines))):
                logger.info(f"Line {i+1}: {lines[i]}")
        
        # Process each line
        for line in lines:
            line_count += 1
            stripped_line = line.strip()
            
            # Skip empty lines and comments
            if not stripped_line or stripped_line.startswith('(') or stripped_line.startswith(';'):
                result_lines.append(line)
                continue
            
            # Analyze movement - print debug for specific important lines
            if "G1" in stripped_line or "G2" in stripped_line or "G3" in stripped_line:
                logger.info(f"Line {line_count} (potential G-code): {stripped_line}")
            
            movement = self.analyzer.analyze_line(stripped_line)
            
            # Add safety checks if needed
            if movement["needs_check"]:
                logger.info(f"Line {line_count}: Adding safety check for G{movement['g_code']} movement")
                logger.info(f"  Axes: X={movement['x_move']} Y={movement['y_move']} Z={movement['z_move']}")
                result_lines.append(f"#600 = {movement['g_code']}")
                result_lines.append(f"#601 = {movement['x_move']}")
                result_lines.append(f"#602 = {movement['y_move']}")
                result_lines.append(f"#603 = {movement['z_move']}")
                result_lines.append("M150")
                safety_checks_added += 1
            
            # Add original line
            result_lines.append(line)
            
            # Periodic progress updates for large files
            if line_count % 500 == 0:
                logger.info(f"Processed {line_count} lines, found {safety_checks_added} safety checks so far")
        
        # Add footer
        result_lines.append("")
        result_lines.append("(End of safety-enhanced G-code)")
        result_lines.append(f"(Added {safety_checks_added} safety checks)")
        
        return {
            "processed_content": "\n".join(result_lines),
            "line_count": line_count,
            "safety_checks_added": safety_checks_added
        }


def main():
    """Main function for command-line usage."""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process G-code files with normalization and safety checks')
    parser.add_argument('input', help='Input G-code file', nargs='?')
    parser.add_argument('-o', '--output', help='Output G-code file (default: input_safe.txt)')
    parser.add_argument('--skip-normalize', action='store_true', help='Skip normalization step')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    
    # Set logging level based on verbosity
    if args.verbose:
        logger.setLevel('DEBUG')
        logger.debug("Verbose logging enabled")
    
    # Get input file - either from command line or file selector
    input_file = args.input
    if not input_file:
        try:
            from Utils.ui_utils import UIUtils
            logger.info("No file specified, launching file selector...")
            success, file_path, details = UIUtils.select_file(
                title="Select G-code file to process",
                file_types=[("G-code files", "*.txt;*.nc;*.gcode")]
            )
            if success:
                input_file = file_path
                logger.info(f"Selected file: {input_file}")
            else:
                print("No file selected. Exiting.")
                import sys
                sys.exit(0)
        except ImportError:
            print("File selection UI not available. Please specify a file on the command line.")
            import sys
            sys.exit(1)
    
    # Generate output filename if not provided
    if args.output:
        output_file = args.output
    else:
        input_path_obj = Path(input_file)
        output_file = str(input_path_obj.with_stem(f"{input_path_obj.stem}_safe").with_suffix(input_path_obj.suffix))
    
    # Step 1: Normalize the G-code file (unless skipped)
    if not args.skip_normalize:
        print(f"Step 1: Normalizing {input_file}...")
        normalizer = GCodeNormalizer()
        
        # Create temporary file for normalized output
        normalized_file = str(Path(input_file).with_stem(f"{Path(input_file).stem}_normalized").with_suffix(Path(input_file).suffix))
        
        norm_success, norm_message, norm_details = normalizer.normalize_file(input_file, normalized_file)
        
        if not norm_success:
            print(f"Error in normalization step: {norm_message}")
            print("Proceeding with original file for safety preprocessing.")
            file_for_safety = input_file
        else:
            print(f"Normalization successful:")
            print(f"- G-codes normalized: {norm_details.get('g_codes_normalized', 0)}")
            print(f"- Redundant coordinates removed: {norm_details.get('coordinates_removed', 0)}")
            print(f"- Explicit G-commands added: {norm_details.get('g01_commands_added', 0)}")
            print(f"- Normalized file: {normalized_file}")
            file_for_safety = normalized_file
            
            # Add note about parametric G-code limitation
            logger.info("⚠️ Note: Parametric G-code using variables (e.g., X#100) is not supported in the "
                        "current implementation of normalization and safety checks. These codes are "
                        "left unmodified. See future task \"Variable-aware G-code Normalization\" for "
                        "planned enhancements.")
    else:
        print("Normalization step skipped.")
        file_for_safety = input_file
    
    # Step 2: Add safety checks
    print(f"\nStep 2: Adding safety checks to {os.path.basename(file_for_safety)}...")
    preprocessor = GCodePreprocessor()
    safety_success, safety_message, safety_details = preprocessor.preprocess_file(file_for_safety, output_file)
    
    if safety_success:
        print(f"Success: {safety_message}")
        print(f"- Lines processed: {safety_details.get('lines_processed', 0)}")
        print(f"- Safety checks added: {safety_details.get('safety_checks_added', 0)}")
        print(f"- Output written to: {safety_details.get('output_file', 'unknown')}")
    else:
        print(f"Error in safety preprocessing: {safety_message}")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()