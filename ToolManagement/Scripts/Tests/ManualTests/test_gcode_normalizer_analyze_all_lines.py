#!/usr/bin/env python3
"""
Manual test script for GCodeNormalizer.

This script provides a way to test the GCodeNormalizer functionality 
with sample G-code files and view the changes made by each normalization step.
"""

import os
import sys
# Add the Scripts directory to the path (parent of GCode)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# Import from GCode module
from GCode.gcode_normalizer import GCodeNormalizer
import re


def print_separator(title):
    """Print a separator with title."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")


def compare_lines(original, normalized):
    """Compare original and normalized lines with detailed analysis."""
    # Check if this is a comment, empty line, or non-G-code line
    if not original.strip() or original.strip().startswith('(') or original.strip().startswith(';'):
        return {
            "g_code_normalized": False,
            "coordinates_removed": False,
            "removed_coords": [],
            "g01_added": False,
            "g_code_added": False,
            "added_g_code": None,
            "reason": "Comment or empty line - no normalization needed"
        }
        
    # Check for variable assignments or other non-G-code lines
    if original.strip().startswith('#'):
        # Check if there's a G-code mentioned in a comment
        comment_match = re.search(r'\((G\d+)', original)
        if comment_match and (comment_match.group(1) == 'G1' or comment_match.group(1) == 'G2' or comment_match.group(1) == 'G3'):
            reason = f"Variable assignment with G-code reference in comment - normalized format in comment"
            return {
                "g_code_normalized": original != normalized,
                "coordinates_removed": False,
                "removed_coords": [],
                "g01_added": False,
                "g_code_added": False,
                "added_g_code": None,
                "reason": reason
            }
        else:
            return {
                "g_code_normalized": False,
                "coordinates_removed": False,
                "removed_coords": [],
                "g01_added": False,
                "g_code_added": False,
                "added_g_code": None,
                "reason": "Variable assignment - no G-code to normalize"
            }
    
    # Check for G-code normalization
    g_code_normalized = False
    g_code_reason = []
    
    if re.search(r'G0(?![0-9])', original) and 'G00' in normalized:
        g_code_normalized = True
        g_code_reason.append("G0 → G00")
    if re.search(r'G1(?![0-9])', original) and 'G01' in normalized:
        g_code_normalized = True
        g_code_reason.append("G1 → G01")
    if re.search(r'G2(?![0-9])', original) and 'G02' in normalized:
        g_code_normalized = True
        g_code_reason.append("G2 → G02")
    if re.search(r'G3(?![0-9])', original) and 'G03' in normalized:
        g_code_normalized = True
        g_code_reason.append("G3 → G03")
    
    if original == normalized and (re.search(r'G00', original) or re.search(r'G01', original) or 
                                  re.search(r'G02', original) or re.search(r'G03', original)):
        g_code_reason.append("Already in normalized format")

    # Check for coordinate removal
    coordinates_removed = False
    orig_coords = re.findall(r'([XYZ][+-]?[0-9]*\.?[0-9]+)', original)
    norm_coords = re.findall(r'([XYZ][+-]?[0-9]*\.?[0-9]+)', normalized)
    
    if len(orig_coords) > len(norm_coords):
        coordinates_removed = True
        removed_coords = [coord for coord in orig_coords if coord not in norm_coords]
    else:
        removed_coords = []
        if orig_coords:
            if original == normalized:
                g_code_reason.append("No redundant coordinates detected")

    # Check for G01 addition
    g01_added = False
    if not re.search(r'G0*1', original) and re.search(r'G0*1', normalized):
        g01_added = True
    
    # Check for any G-code addition
    g_code_added = False
    added_g_code = None
    
    # Look for G-codes in normalized that aren't in original
    if not re.search(r'G\d+', original):
        g_code_match = re.search(r'G(\d+)', normalized)
        if g_code_match:
            g_code_added = True
            added_g_code = f"G{g_code_match.group(1)}"
    
    # Determine reason for no changes
    if original == normalized:
        if not orig_coords:
            reason = "No coordinates to normalize"
        elif re.search(r'G0*[0-3]', original):
            if "Already in normalized format" not in g_code_reason:
                g_code_reason.append("Already in normalized format")
            reason = ", ".join(g_code_reason)
        else:
            reason = "No normalization needed"
    else:
        reason_parts = []
        if g_code_normalized:
            reason_parts.append("G-code format normalized: " + ", ".join(g_code_reason))
        if coordinates_removed:
            reason_parts.append(f"Redundant coordinates removed: {', '.join(removed_coords)}")
        if g01_added:
            reason_parts.append("Added explicit G01 command")
        elif g_code_added and added_g_code:
            reason_parts.append(f"Added explicit {added_g_code} command")
            
        reason = " | ".join(reason_parts)

    return {
        "g_code_normalized": g_code_normalized,
        "coordinates_removed": coordinates_removed,
        "removed_coords": removed_coords,
        "g01_added": g01_added,
        "g_code_added": g_code_added,
        "added_g_code": added_g_code,
        "reason": reason
    }


def print_comparison(original, normalized, changes):
    """Print comparison with detailed explanation of changes or lack of changes."""
    # Format change information
    status = []
    if changes["g_code_normalized"]:
        status.append("G-code normalized")
    if changes["coordinates_removed"]:
        status.append(f"Removed coords: {', '.join(changes['removed_coords'])}")
    if changes["g01_added"]:
        status.append("Added G01")
    elif changes["g_code_added"] and changes["added_g_code"]:
        status.append(f"Added {changes['added_g_code']}")

    status_str = " | ".join(status) if status else "No changes"
    
    # Print original and normalized lines
    print(f"  Original: {original.strip()}")
    print(f"Normalized: {normalized.strip()}")
    print(f"   Changes: {status_str}")
    print(f"   Reason: {changes['reason']}")
    print()


def test_gcode_normalizer(gcode_file):
    """Test the GCodeNormalizer with a G-code file."""
    print_separator(f"TESTING GCODE NORMALIZER ON {os.path.basename(gcode_file)}")
    
    # Create normalizer instance
    normalizer = GCodeNormalizer()
    
    # Process a small portion for detailed output
    print("Loading G-code file...")
    with open(gcode_file, 'r') as f:
        content = f.read()
    
    lines = content.splitlines(True)  # Keep newlines
    
    # Print file info
    print(f"File: {gcode_file}")
    print(f"Total lines: {len(lines)}")
    print()
    
    # Test normalizing individual lines for detailed analysis
    print_separator("DETAILED LINE-BY-LINE ANALYSIS OF ALL LINES")
    
    # Reset state for consistent testing
    normalizer._reset_state()
    
    # Analyze ALL lines
    for i, line in enumerate(lines):
        original_line = line
        normalized_line = normalizer._normalize_line(line)
        changes = compare_lines(original_line, normalized_line)
        
        print(f"Line {i+1}:")
        print_comparison(original_line, normalized_line, changes)
    
    # Test full file normalization
    print_separator("NORMALIZING ENTIRE FILE")
    
    # Generate a normalized output filename
    input_basename = os.path.basename(gcode_file)
    output_file = f"{os.path.splitext(input_basename)[0]}_normalized{os.path.splitext(input_basename)[1]}"
    output_path = os.path.join(os.path.dirname(gcode_file), output_file)
    
    # Normalize the file
    success, message, details = normalizer.normalize_file(gcode_file, output_path)
    
    if success:
        print(f"Success: {message}")
        print(f"Processed {details.get('lines_processed', 0)} lines")
        print(f"Normalized {details.get('g_codes_normalized', 0)} G-codes")
        print(f"Removed {details.get('coordinates_removed', 0)} redundant coordinates")
        print(f"Added {details.get('g01_commands_added', 0)} explicit G01 commands")
        print(f"Output written to: {details.get('output_file', 'unknown')}")
        
        # Compare lines from original and normalized file
        print_separator("COMPARING ONLY CHANGED LINES: ORIGINAL VS NORMALIZED FILE")
        
        print("Original file  :", gcode_file)
        print("Normalized file:", output_path)
        print()
        
        with open(output_path, 'r') as f:
            normalized_content = f.read()
        
        normalized_lines = normalized_content.splitlines(True)
        
        # Skip header and footer lines in normalized file
        norm_start = 0
        norm_end = len(normalized_lines)
        
        for i, line in enumerate(normalized_lines):
            if line.strip() and not line.strip().startswith('(') and norm_start == 0:
                norm_start = i
                break
                
        for i in range(len(normalized_lines) - 1, 0, -1):
            if normalized_lines[i].strip() and not normalized_lines[i].strip().startswith('('):
                norm_end = i + 1
                break
        
        # Map original lines to normalized lines
        line_mapping = {}
        orig_lines_with_n = [(i, line) for i, line in enumerate(lines) if re.search(r'^N\d+', line.strip())]
        norm_lines_with_n = [(i, line) for i, line in enumerate(normalized_lines[norm_start:norm_end]) 
                            if re.search(r'^N\d+', line.strip())]
        
        # Create mapping based on N-numbers
        for orig_i, orig_line in orig_lines_with_n:
            n_match = re.search(r'^N(\d+)', orig_line.strip())
            if n_match:
                n_num = n_match.group(1)
                for norm_i, norm_line in norm_lines_with_n:
                    if re.search(f'^N{n_num}', norm_line.strip()):
                        line_mapping[orig_i] = norm_start + norm_i
                        break
        
        # Show only lines that have changes
        print("Showing only lines that have been modified:")
        print()
        
        changes_found = 0
        for i, line in enumerate(lines):
            if i in line_mapping:
                norm_i = line_mapping[i]
                # Only show if there are changes
                if line.strip() != normalized_lines[norm_i].strip():
                    changes = compare_lines(line, normalized_lines[norm_i])
                    print(f"Line {i+1} (original) → Line {norm_i+1} (normalized):")
                    print_comparison(line, normalized_lines[norm_i], changes)
                    changes_found += 1
        
        if changes_found == 0:
            print("No changes found in any line.")
        else:
            print(f"Total changed lines: {changes_found}")
        
        print("\nTEST COMPLETED")
        return True
    else:
        print(f"Error: {message}")
        return False


if __name__ == "__main__":
    # Get G-code file from command line or use default
    if len(sys.argv) > 1:
        gcode_file = sys.argv[1]
    else:
        # Look for G-code files in the correct test data directory
        test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "TestData", "Gcode")
        if not os.path.exists(test_data_dir):
            print(f"Test data directory not found: {test_data_dir}")
            test_data_dir = os.path.dirname(__file__)  # Fallback to current directory
        else:
            print(f"Found test data directory: {test_data_dir}")
            
        gcode_files = []
        for root, dirs, files in os.walk(test_data_dir):
            for file in files:
                if file.endswith('.txt') or file.endswith('.nc') or file.endswith('.gcode'):
                    if "001" in file:  # Prioritize the files we've seen in your examples
                        gcode_files.insert(0, os.path.join(root, file))
                    else:
                        gcode_files.append(os.path.join(root, file))
            
        if gcode_files:
            print("Available G-code files:")
            for i, file in enumerate(gcode_files):
                print(f"{i+1}. {os.path.basename(file)} ({file})")
            
            choice = input("Enter file number to test (or press Enter for first file): ")
            if choice and choice.isdigit() and 1 <= int(choice) <= len(gcode_files):
                gcode_file = gcode_files[int(choice) - 1]
            else:
                gcode_file = gcode_files[0]
                
            print(f"Using file: {gcode_file}")
        else:
            print(f"No G-code files found in {test_data_dir}")
            gcode_file = input("Enter path to G-code file: ")
    
    if os.path.exists(gcode_file):
        test_gcode_normalizer(gcode_file)
    else:
        print(f"File not found: {gcode_file}")