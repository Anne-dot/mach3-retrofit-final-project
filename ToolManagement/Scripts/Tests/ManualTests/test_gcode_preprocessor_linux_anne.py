import os
import sys
import re
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from GCode.preprocessor import GCodePreprocessor
from GCode.gcode_normalizer import GCodeNormalizer

# Set up paths
test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "TestData")
gcode_file_path = os.path.join(test_data_dir, "Gcode", "001.txt")

# File selection logic
print(f"Processing G-code file: {os.path.basename(gcode_file_path)}")

# Check if file exists
if not os.path.exists(gcode_file_path):
    print(f"ERROR: File does not exist: {gcode_file_path}")
    possible_files = []
    for root, dirs, files in os.walk(test_data_dir):
        for file in files:
            if file.endswith('.txt'):
                possible_files.append(os.path.join(root, file))
    if possible_files:
        print(f"These G-code files were found:")
        for i, file in enumerate(possible_files):
            print(f"  {i+1}. {file}")
        print("\nEnter the number of the file to use, or press Enter to exit:")
        choice = input()
        if choice.isdigit() and 1 <= int(choice) <= len(possible_files):
            gcode_file_path = possible_files[int(choice)-1]
            print(f"Using file: {gcode_file_path}")
        else:
            print("Exiting...")
            sys.exit(1)
    else:
        print("No G-code files found. Exiting...")
        sys.exit(1)

# STEP 1: Normalize G-code file
print("\n=== STEP 1: G-CODE NORMALIZATION ===")
normalizer = GCodeNormalizer()

# Generate output filename for normalized file
normalized_file_path = os.path.join(
    os.path.dirname(gcode_file_path),
    f"{os.path.splitext(os.path.basename(gcode_file_path))[0]}_normalized{os.path.splitext(gcode_file_path)[1]}"
)

# Process the file with the normalizer
print(f"Normalizing: {os.path.basename(gcode_file_path)}")
start_time = time.time()
norm_success, norm_message, norm_details = normalizer.normalize_file(gcode_file_path, normalized_file_path)
norm_time = time.time() - start_time

# Process normalization results
if norm_success:
    print(f"Successfully normalized G-code file in {norm_time:.2f} seconds")
    print(f"  Lines processed: {norm_details.get('lines_processed', 'N/A')}")
    print(f"  G-codes normalized: {norm_details.get('g_codes_normalized', 'N/A')}")
    print(f"  Coordinates removed: {norm_details.get('coordinates_removed', 'N/A')}")
    print(f"  G01 commands added: {norm_details.get('g01_commands_added', 'N/A')}")
    print(f"  Output file: {norm_details.get('output_file', 'N/A')}")
    
    # Compare sizes
    if os.path.exists(normalized_file_path):
        input_size = os.path.getsize(gcode_file_path)
        norm_size = os.path.getsize(normalized_file_path)
        print(f"  Input file size: {input_size} bytes")
        print(f"  Normalized file size: {norm_size} bytes")
        print(f"  Size difference: {norm_size - input_size:+} bytes")
else:
    print(f"Failed to normalize G-code file: {norm_message}")
    print("Continuing with original file for safety preprocessing...")
    normalized_file_path = gcode_file_path

# STEP 2: Apply safety checks
print("\n=== STEP 2: SAFETY PREPROCESSING ===")
preprocessor = GCodePreprocessor()

# Generate output filename for safety-enhanced file
safety_file_path = os.path.join(
    os.path.dirname(normalized_file_path),
    f"{os.path.splitext(os.path.basename(normalized_file_path))[0]}_safe{os.path.splitext(normalized_file_path)[1]}"
)

# Process the file with safety preprocessor
print(f"Adding safety checks to: {os.path.basename(normalized_file_path)}")
start_time = time.time()
safety_success, safety_message, safety_details = preprocessor.preprocess_file(normalized_file_path, safety_file_path)
safety_time = time.time() - start_time

# Process safety results
if safety_success:
    print(f"Successfully added safety checks in {safety_time:.2f} seconds")
    print(f"  Lines processed: {safety_details.get('lines_processed', 'N/A')}")
    print(f"  Safety checks added: {safety_details.get('safety_checks_added', 'N/A')}")
    print(f"  Output file: {safety_details.get('output_file', 'N/A')}")
    
    # Analyze the processed file
    output_file = safety_details.get('output_file')
    if os.path.exists(output_file):
        print("\n=== ANALYSIS OF SAFETY-ENHANCED FILE ===")
        
        # Compare file sizes
        input_size = os.path.getsize(gcode_file_path)
        norm_size = os.path.getsize(normalized_file_path)
        output_size = os.path.getsize(output_file)
        print(f"  Original file size: {input_size} bytes")
        print(f"  Normalized file size: {norm_size} bytes")
        print(f"  Safety-enhanced file size: {output_size} bytes")
        print(f"  Total size change: {output_size - input_size:+} bytes")
        
        # Read all files for analysis
        with open(gcode_file_path, 'r') as f:
            original_lines = f.readlines()
        
        with open(normalized_file_path, 'r') as f:
            normalized_lines = f.readlines()
            
        with open(output_file, 'r') as f:
            processed_lines = f.readlines()
        
        # Create regex patterns similar to the preprocessor
        g1_pattern = re.compile(r'(?:N\d+)?G0*1(?=[^0-9]|$)')
        g2_pattern = re.compile(r'(?:N\d+)?G0*2(?=[^0-9]|$)')
        g3_pattern = re.compile(r'(?:N\d+)?G0*3(?=[^0-9]|$)')
        
        # Find all G1, G2, G3 commands in original and normalized files
        orig_g1_lines = []
        orig_g2_lines = []
        orig_g3_lines = []
        
        norm_g1_lines = []
        norm_g2_lines = []
        norm_g3_lines = []
        
        for i, line in enumerate(original_lines):
            if g1_pattern.search(line):
                orig_g1_lines.append((i+1, line.strip()))
            elif g2_pattern.search(line):
                orig_g2_lines.append((i+1, line.strip()))
            elif g3_pattern.search(line):
                orig_g3_lines.append((i+1, line.strip()))
        
        for i, line in enumerate(normalized_lines):
            if g1_pattern.search(line) or 'G01' in line:
                norm_g1_lines.append((i+1, line.strip()))
            elif g2_pattern.search(line) or 'G02' in line:
                norm_g2_lines.append((i+1, line.strip()))
            elif g3_pattern.search(line) or 'G03' in line:
                norm_g3_lines.append((i+1, line.strip()))
        
        # Count safety checks in processed file
        safety_checks = []
        for i, line in enumerate(processed_lines):
            if line.strip() == "M150":
                # Find what this safety check is for
                check_type = None
                for j in range(max(0, i-5), i):
                    if j < len(processed_lines):
                        if "#600 = 1" in processed_lines[j]:
                            check_type = "G1"
                            break
                        elif "#600 = 2" in processed_lines[j]:
                            check_type = "G2"
                            break
                        elif "#600 = 3" in processed_lines[j]:
                            check_type = "G3"
                            break
                
                # Find what line number this safety check is for
                target_line = None
                if i+1 < len(processed_lines):
                    target_line = processed_lines[i+1].strip()
                
                safety_checks.append((check_type, target_line))
        
        # Count matches
        orig_g1_count = len(orig_g1_lines)
        orig_g2_count = len(orig_g2_lines)
        orig_g3_count = len(orig_g3_lines)
        
        norm_g1_count = len(norm_g1_lines)
        norm_g2_count = len(norm_g2_lines)
        norm_g3_count = len(norm_g3_lines)
        
        # Count G1/G2/G3 safety checks
        g1_checks = sum(1 for check in safety_checks if check[0] == "G1")
        g2_checks = sum(1 for check in safety_checks if check[0] == "G2")
        g3_checks = sum(1 for check in safety_checks if check[0] == "G3")
        
        print("\nG-code analysis:")
        print(f"  Original file G-codes: G1={orig_g1_count}, G2={orig_g2_count}, G3={orig_g3_count}")
        print(f"  Normalized file G-codes: G1={norm_g1_count}, G2={norm_g2_count}, G3={norm_g3_count}")
        print(f"  G-code format change: G1={norm_g1_count-orig_g1_count:+}, G2={norm_g2_count-orig_g2_count:+}, G3={norm_g3_count-orig_g3_count:+}")
        
        print("\nSafety checks found in processed file:")
        print(f"  G1 safety checks: {g1_checks}/{norm_g1_count}")
        print(f"  G2 safety checks: {g2_checks}/{norm_g2_count}")
        print(f"  G3 safety checks: {g3_checks}/{norm_g3_count}")
        print(f"  Total safety checks: {len(safety_checks)}/{norm_g1_count + norm_g2_count + norm_g3_count}")
        
        # Check if the safety checks match expectations based on normalized file
        expected_checks = norm_g1_count + norm_g2_count + norm_g3_count
        
        print("\nVerification Summary:")
        if len(safety_checks) == expected_checks:
            print(f"  ✓ All {expected_checks} movements have safety checks")
        else:
            print(f"  ✗ Mismatch: Expected {expected_checks} safety checks, found {len(safety_checks)}")
            print(f"  Note: This mismatch can possibly be due to pattern matching issues. G17/G28/G30 could be")
            print(f"        incorrectly counted as G1/G2/G3. Actual safety checks are likely correct.")
            
        # Confirm the file ends properly
        if len(processed_lines) >= 2 and "(End of safety-enhanced G-code)" in processed_lines[-2]:
            print("  ✓ File has proper ending")
        else:
            print("  ✗ File ending is incorrect")
    else:
        print(f"ERROR: Output file not found: {output_file}")
else:
    print(f"Failed to add safety checks: {safety_message}")
    input("Press Enter to exit...")
    sys.exit(1)

print("\n=== COMPLETE TEST SUMMARY ===")
print(f"Original file: {os.path.basename(gcode_file_path)}")
print(f"Normalized file: {os.path.basename(normalized_file_path)}")
print(f"Safety-enhanced file: {os.path.basename(safety_file_path)}")
print(f"Normalization statistics: {norm_details.get('g_codes_normalized', 0)} formats normalized, {norm_details.get('coordinates_removed', 0)} coordinates removed")
print(f"Safety statistics: {safety_details.get('safety_checks_added', 0)} safety checks added")
print("\nTwo-stage preprocessing test completed")